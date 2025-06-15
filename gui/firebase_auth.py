"""
客戶端 Firebase 認證管理器 - 通過 Render 服務器代理
"""
import requests
import json
import time
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

class FirebaseAuthManager:
    """Firebase 認證管理器類 - 客戶端版本"""
    
    def __init__(self, server_url: str = None):
        # 配置服務器 URL - 請替換為您的 Render 服務 URL
        self.server_url = server_url or "https://artale-auth-service.onrender.com"
        self.session_token = None
        self.current_user = None
        self.current_session_id = None  # 兼容性
        self.is_initialized = True
        self.heartbeat_running = False  # 兼容性
        
        # 設置請求會話
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ArtaleScript/1.1.0'
        })
        
        # 會話監控
        self.last_validation = 0
        self.validation_interval = 120  # 每2分鐘驗證一次
        
        print(f"🔥 客戶端認證管理器初始化完成，服務器: {self.server_url}")
    
    def authenticate_user(self, user_uuid: str, force_login: bool = True) -> Tuple[bool, str, Optional[Dict]]:
        """認證用戶"""
        try:
            print(f"🔑 開始認證用戶: {user_uuid[:8]}...")
            
            response = self.session.post(
                f"{self.server_url}/auth/login",
                json={
                    'uuid': user_uuid,
                    'force_login': force_login
                },
                timeout=15  # 增加超時時間
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    self.session_token = data['session_token']
                    self.current_user = {
                        'uuid_hash': user_uuid,  # 兼容性
                        'data': data['user_data']
                    }
                    self.current_session_id = data['session_token'][:16]  # 兼容性
                    
                    print(f"✅ 認證成功: {data['user_data'].get('display_name', 'Unknown')}")
                    return True, data['message'], data['user_data']
                else:
                    print(f"❌ 認證失敗: {data.get('error', 'Unknown error')}")
                    return False, data.get('error', 'Unknown error'), None
            
            elif response.status_code == 429:
                return False, "請求過於頻繁，請稍後再試", None
            
            elif response.status_code == 401:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', 'UUID 未授權'), None
            
            else:
                error_data = response.json() if response.content else {}
                return False, error_data.get('error', f'HTTP {response.status_code}'), None
                
        except requests.exceptions.Timeout:
            print("❌ 連接超時")
            return False, "連接超時，請檢查網路連接", None
        
        except requests.exceptions.ConnectionError:
            print("❌ 連接錯誤")
            return False, "無法連接到認證服務器，請檢查網路連接", None
        
        except Exception as e:
            print(f"❌ 認證錯誤: {str(e)}")
            return False, f"認證失敗: {str(e)}", None
    
    def logout_user(self):
        """用戶登出"""
        try:
            if self.session_token:
                print("🔓 正在登出...")
                response = self.session.post(
                    f"{self.server_url}/auth/logout",
                    json={'session_token': self.session_token},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("✅ 登出成功")
                else:
                    print("⚠️ 登出請求失敗，但本地會話已清除")
                    
        except Exception as e:
            print(f"⚠️ 登出時發生錯誤: {str(e)}")
        finally:
            # 清除本地會話
            self.session_token = None
            self.current_user = None
            self.current_session_id = None
            self.last_validation = 0
    
    def validate_session(self) -> bool:
        """驗證當前會話"""
        if not self.session_token:
            return False
        
        # 避免過於頻繁的驗證
        current_time = time.time()
        if current_time - self.last_validation < self.validation_interval:
            return True
        
        try:
            print("🔍 驗證會話...")
            response = self.session.post(
                f"{self.server_url}/auth/validate",
                json={'session_token': self.session_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    # 更新用戶數據
                    if self.current_user:
                        self.current_user['data'] = data['user_data']
                    
                    self.last_validation = current_time
                    print("✅ 會話驗證通過")
                    return True
                else:
                    print("❌ 會話驗證失敗")
                    self._handle_session_invalid()
                    return False
            else:
                print(f"❌ 會話驗證失敗: HTTP {response.status_code}")
                self._handle_session_invalid()
                return False
                
        except requests.exceptions.Timeout:
            print("⚠️ 會話驗證超時，假設會話仍有效")
            return True  # 網路問題時不強制登出
        
        except requests.exceptions.ConnectionError:
            print("⚠️ 無法連接認證服務器，假設會話仍有效")
            return True  # 網路問題時不強制登出
        
        except Exception as e:
            print(f"⚠️ 會話驗證錯誤: {str(e)}")
            return True  # 出錯時不強制登出
    
    def _handle_session_invalid(self):
        """處理會話失效"""
        print("🔄 會話已失效，清除本地數據")
        self.session_token = None
        self.current_user = None
        self.current_session_id = None
        self.last_validation = 0
    
    def is_user_logged_in(self) -> bool:
        """檢查用戶是否已登入"""
        return self.session_token is not None and self.current_user is not None
    
    def get_current_user(self) -> Optional[Dict]:
        """獲取當前用戶信息"""
        return self.current_user
    
    def check_permission(self, permission: str) -> bool:
        """檢查特定權限"""
        if not self.current_user:
            return False
        
        permissions = self.current_user['data'].get('permissions', {})
        return permissions.get(permission, False)
    
    def get_user_permissions(self) -> Dict[str, bool]:
        """獲取用戶權限"""
        if not self.current_user:
            return {}
        
        return self.current_user['data'].get('permissions', {})
    
    def force_logout_user(self, target_uuid: str) -> Tuple[bool, str]:
        """強制登出指定用戶（管理員功能） - 暫不支援"""
        return False, "此功能需要管理員權限，請聯繫管理員"
    
    def get_active_sessions(self) -> list:
        """獲取所有活躍會話列表 - 暫不支援"""
        return []
    
    def create_user(self, uuid: str, user_info: Dict) -> Tuple[bool, str]:
        """創建新用戶（管理員功能） - 暫不支援"""
        return False, "此功能需要管理員權限，請聯繫管理員"
    
    def get_connection_status(self) -> Dict[str, any]:
        """獲取連接狀態"""
        return {
            'initialized': self.is_initialized,
            'server_url': self.server_url,
            'has_current_user': self.current_user is not None,
            'has_active_session': self.session_token is not None,
            'last_validation': self.last_validation,
            'heartbeat_running': self.heartbeat_running  # 兼容性
        }

# 全域認證管理器實例
_auth_manager = None

def get_auth_manager() -> FirebaseAuthManager:
    """獲取全域認證管理器實例"""
    global _auth_manager
    if _auth_manager is None:
        # 替換為您的 Render 服務 URL
        server_url = "https://artale-auth-service.onrender.com"
        _auth_manager = FirebaseAuthManager(server_url)
    return _auth_manager

def initialize_auth(credentials_path: str = None) -> bool:
    """初始化認證系統（兼容性函數）"""
    global _auth_manager
    _auth_manager = get_auth_manager()
    return _auth_manager.is_initialized