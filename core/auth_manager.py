"""
認證管理器 - 核心認證系統
"""
import hashlib
import time
import os
import json
from datetime import datetime, timedelta
import uuid

class AuthManager:
    """認證管理器"""
    
    def __init__(self):
        self.current_session = None
        self.session_start_time = None
        self.session_timeout = 3600  # 1小時超時
        self.auth_token_file = ".auth_session"
        
    def generate_session_token(self, user_uuid: str) -> str:
        """生成會話令牌"""
        timestamp = str(int(time.time()))
        session_id = str(uuid.uuid4())
        
        # 創建令牌數據
        token_data = {
            'user_uuid_hash': hashlib.sha256(user_uuid.encode()).hexdigest(),
            'session_id': session_id,
            'timestamp': timestamp,
            'expires_at': int(time.time()) + self.session_timeout
        }
        
        # 生成簽名
        signature = self._generate_signature(token_data)
        token_data['signature'] = signature
        
        return json.dumps(token_data)
    
    def _generate_signature(self, token_data: dict) -> str:
        """生成令牌簽名"""
        # 使用多重hash增加安全性
        data_str = f"{token_data['user_uuid_hash']}{token_data['session_id']}{token_data['timestamp']}"
        
        # 添加機器特徵
        machine_id = self._get_machine_id()
        data_str += machine_id
        
        # 多重hash
        hash1 = hashlib.sha256(data_str.encode()).hexdigest()
        hash2 = hashlib.sha512((hash1 + data_str).encode()).hexdigest()
        
        return hash2[:32]  # 取前32位
    
    def _get_machine_id(self) -> str:
        """更寬鬆的機器識別"""
        return "flexible_auth"  # 基本上不綁定設備
    
    def save_session_token(self, token: str):
        """保存會話令牌到文件"""
        try:
            with open(self.auth_token_file, 'w') as f:
                f.write(token)
            
            # 設置文件隱藏屬性
            if os.name == 'nt':  # Windows
                try:
                    import subprocess
                    subprocess.run(['attrib', '+h', self.auth_token_file], 
                                 capture_output=True, check=False)
                except:
                    pass
        except Exception as e:
            print(f"保存會話令牌失敗: {e}")
    
    def load_session_token(self) -> str:
        """從文件讀取會話令牌"""
        try:
            if os.path.exists(self.auth_token_file):
                with open(self.auth_token_file, 'r') as f:
                    return f.read().strip()
        except:
            pass
        return None
    
    def verify_session_token(self, token: str = None) -> bool:
        """驗證會話令牌"""
        if token is None:
            token = self.load_session_token()
        
        if not token:
            return False
        
        try:
            token_data = json.loads(token)
            
            # 檢查必要字段
            required_fields = ['user_uuid_hash', 'session_id', 'timestamp', 'expires_at', 'signature']
            if not all(field in token_data for field in required_fields):
                return False
            
            # 檢查過期時間
            if int(time.time()) > token_data['expires_at']:
                self.clear_session()
                return False
            
            # 驗證簽名
            expected_signature = self._generate_signature(token_data)
            if token_data['signature'] != expected_signature:
                return False
            
            # 更新當前會話
            self.current_session = token_data
            return True
            
        except Exception as e:
            print(f"令牌驗證失敗: {e}")
            return False
    
    def clear_session(self):
        """清除會話"""
        self.current_session = None
        self.session_start_time = None
        
        try:
            if os.path.exists(self.auth_token_file):
                os.remove(self.auth_token_file)
        except:
            pass
    
    def is_authenticated(self) -> bool:
        """檢查是否已認證"""
        return self.verify_session_token()
    
    def get_session_info(self) -> dict:
        """獲取會話信息"""
        if not self.current_session:
            return None
        
        return {
            'user_hash': self.current_session['user_uuid_hash'][:8] + "...",
            'session_id': self.current_session['session_id'][:8] + "...",
            'expires_at': datetime.fromtimestamp(self.current_session['expires_at']).strftime('%Y-%m-%d %H:%M:%S')
        }

# 全局認證管理器實例
_auth_manager = AuthManager()

def get_auth_manager():
    """獲取認證管理器實例"""
    return _auth_manager

def require_authentication():
    """裝飾器：要求認證"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not _auth_manager.is_authenticated():
                print("❌ 未認證訪問被拒絕")
                print("請先通過 GUI 登入系統")
                exit(1)
            return func(*args, **kwargs)
        return wrapper
    return decorator