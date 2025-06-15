"""
Firebase 用戶管理工具 - 用於管理授權用戶和會話
"""
import sys
import os
from datetime import datetime, timedelta
from firebase_auth import get_auth_manager
import hashlib

class UserManager:
    """用戶管理類"""
    
    def __init__(self):
        self.auth_manager = get_auth_manager()
        if not self.auth_manager.is_initialized:
            print("❌ Firebase 初始化失敗，請檢查憑證文件")
            sys.exit(1)
    
    def add_user(self, uuid: str, display_name: str = None, expires_days: int = 30, 
                 script_access: bool = True, config_modify: bool = True):
        """
        添加新用戶
        
        Args:
            uuid: 用戶 UUID
            display_name: 顯示名稱
            expires_days: 有效期天數（0表示永久）
            script_access: 是否有腳本執行權限
            config_modify: 是否有配置修改權限
        """
        if not uuid:
            print("❌ UUID 不能為空")
            return False
        
        # 準備用戶數據
        user_data = {
            'display_name': display_name or f"User_{uuid[:8]}",
            'permissions': {
                'script_access': script_access,
                'config_modify': config_modify
            },
            'created_by': 'admin_tool',
            'notes': f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        # 設置到期時間
        if expires_days > 0:
            expires_at = datetime.now() + timedelta(days=expires_days)
            user_data['expires_at'] = expires_at.isoformat()
        
        # 創建用戶
        success, message = self.auth_manager.create_user(uuid, user_data)
        
        if success:
            print(f"✅ 用戶創建成功:")
            print(f"   UUID: {uuid}")
            print(f"   顯示名稱: {user_data['display_name']}")
            print(f"   腳本權限: {'是' if script_access else '否'}")
            print(f"   配置權限: {'是' if config_modify else '否'}")
            if expires_days > 0:
                print(f"   到期時間: {user_data['expires_at']}")
            else:
                print(f"   到期時間: 永久")
        else:
            print(f"❌ 創建用戶失敗: {message}")
        
        return success
    
    def list_users(self):
        """列出所有用戶"""
        try:
            users_ref = self.auth_manager.db.collection('authorized_users')
            users = users_ref.stream()
            
            print("\n📋 授權用戶列表:")
            print("-" * 90)
            print(f"{'UUID Hash':<16} {'顯示名稱':<20} {'狀態':<8} {'到期時間':<20} {'登入次數':<8} {'會話':<8}")
            print("-" * 90)
            
            user_count = 0
            active_sessions = self.get_active_sessions_summary()
            
            for user in users:
                user_data = user.to_dict()
                user_count += 1
                
                uuid_hash = user.id
                display_name = user_data.get('display_name', 'Unknown')
                active = user_data.get('active', True)
                status = "啟用" if active else "停用"
                login_count = user_data.get('login_count', 0)
                
                # 檢查是否有活躍會話
                has_session = "在線" if uuid_hash in active_sessions else "離線"
                
                # 處理到期時間
                expires_at = user_data.get('expires_at')
                if expires_at:
                    if isinstance(expires_at, str):
                        expires_str = expires_at.split('T')[0]  # 只顯示日期
                    else:
                        expires_str = str(expires_at).split('T')[0]
                else:
                    expires_str = "永久"
                
                print(f"{uuid_hash[:16]:<16} {display_name[:20]:<20} {status:<8} {expires_str:<20} {login_count:<8} {has_session:<8}")
            
            print("-" * 90)
            print(f"總計: {user_count} 個用戶，{len(active_sessions)} 個在線")
            
        except Exception as e:
            print(f"❌ 列出用戶失敗: {str(e)}")
    
    def get_active_sessions_summary(self):
        """獲取活躍會話摘要"""
        try:
            sessions = self.auth_manager.get_active_sessions()
            # 返回 uuid_hash 到 session_id 的映射
            return {session.get('user_uuid_hash', ''): session.get('session_id', '') for session in sessions}
        except Exception as e:
            print(f"⚠️ 獲取會話摘要失敗: {str(e)}")
            return {}
    
    def list_active_sessions(self):
        """列出所有活躍會話"""
        try:
            sessions = self.auth_manager.get_active_sessions()
            
            if not sessions:
                print("\n📱 目前沒有活躍會話")
                return
            
            print(f"\n📱 活躍會話列表 (共 {len(sessions)} 個):")
            print("-" * 100)
            print(f"{'會話ID':<20} {'用戶名稱':<20} {'登入時間':<20} {'最後活動':<20} {'IP地址':<15}")
            print("-" * 100)
            
            for session in sessions:
                session_id = session.get('session_id', 'Unknown')[:18]
                user_name = session.get('user_display_name', 'Unknown')[:18]
                
                created_at = session.get('created_at')
                if created_at:
                    if hasattr(created_at, 'strftime'):
                        created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        created_str = str(created_at)[:19]
                else:
                    created_str = "Unknown"
                
                last_heartbeat = session.get('last_heartbeat')
                if last_heartbeat:
                    if hasattr(last_heartbeat, 'strftime'):
                        heartbeat_str = last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        heartbeat_str = str(last_heartbeat)[:19]
                else:
                    heartbeat_str = "Unknown"
                
                client_info = session.get('client_info', {})
                ip_address = client_info.get('ip_address', 'Unknown')[:14]
                
                print(f"{session_id:<20} {user_name:<20} {created_str:<20} {heartbeat_str:<20} {ip_address:<15}")
            
            print("-" * 100)
            
        except Exception as e:
            print(f"❌ 列出活躍會話失敗: {str(e)}")
    
    def force_logout_user(self, uuid: str):
        """強制登出指定用戶的所有會話"""
        if not uuid:
            print("❌ UUID 不能為空")
            return False
        
        print(f"⚠️ 即將強制登出用戶: {uuid}")
        confirm = input("請輸入 'LOGOUT' 確認強制登出: ")
        
        if confirm != 'LOGOUT':
            print("❌ 操作已取消")
            return False
        
        try:
            success, message = self.auth_manager.force_logout_user(uuid)
            
            if success:
                print(f"✅ 強制登出成功: {message}")
            else:
                print(f"❌ 強制登出失敗: {message}")
            
            return success
            
        except Exception as e:
            print(f"❌ 強制登出失敗: {str(e)}")
            return False
    
    def cleanup_expired_sessions(self):
        """清理過期會話"""
        try:
            print("🧹 開始清理過期會話...")
            
            # 調用認證管理器的清理方法
            self.auth_manager._cleanup_expired_sessions()
            
            # 獲取清理後的會話數量
            active_sessions = self.auth_manager.get_active_sessions()
            print(f"✅ 清理完成，目前活躍會話數: {len(active_sessions)}")
            
        except Exception as e:
            print(f"❌ 清理過期會話失敗: {str(e)}")
    
    def get_session_details(self, session_id_prefix: str):
        """根據會話ID前綴獲取詳細信息"""
        try:
            sessions = self.auth_manager.get_active_sessions()
            
            matching_sessions = [s for s in sessions if s.get('session_id', '').startswith(session_id_prefix)]
            
            if not matching_sessions:
                print(f"❌ 找不到以 '{session_id_prefix}' 開頭的會話")
                return False
            
            if len(matching_sessions) > 1:
                print(f"⚠️ 找到 {len(matching_sessions)} 個匹配的會話，請提供更精確的前綴")
                for i, session in enumerate(matching_sessions, 1):
                    print(f"  {i}. {session.get('session_id', '')[:20]}...")
                return False
            
            session = matching_sessions[0]
            
            print(f"\n📱 會話詳細信息:")
            print("-" * 50)
            print(f"會話ID: {session.get('session_id', 'Unknown')}")
            print(f"用戶名稱: {session.get('user_display_name', 'Unknown')}")
            
            created_at = session.get('created_at')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    created_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    created_str = str(created_at)
                print(f"登入時間: {created_str}")
            
            last_heartbeat = session.get('last_heartbeat')
            if last_heartbeat:
                if hasattr(last_heartbeat, 'strftime'):
                    heartbeat_str = last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')
                    # 計算最後活動距現在的時間
                    time_diff = datetime.now() - last_heartbeat
                    print(f"最後活動: {heartbeat_str} ({int(time_diff.total_seconds())} 秒前)")
                else:
                    print(f"最後活動: {str(last_heartbeat)}")
            
            client_info = session.get('client_info', {})
            if client_info:
                print(f"IP地址: {client_info.get('ip_address', 'Unknown')}")
                machine_info = client_info.get('machine_info', {})
                if machine_info:
                    print(f"作業系統: {machine_info.get('os', 'Unknown')} {machine_info.get('os_version', '')}")
                    print(f"處理器: {machine_info.get('processor', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 獲取會話詳細信息失敗: {str(e)}")
            return False
    
    def deactivate_user(self, uuid: str):
        """停用用戶"""
        try:
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.auth_manager.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"❌ 找不到用戶: {uuid}")
                return False
            
            user_ref.update({
                'active': False,
                'deactivated_at': datetime.now(),
                'deactivated_by': 'admin_tool'
            })
            
            # 同時強制登出該用戶
            self.auth_manager.force_logout_user(uuid)
            
            print(f"✅ 用戶已停用並強制登出: {uuid}")
            return True
            
        except Exception as e:
            print(f"❌ 停用用戶失敗: {str(e)}")
            return False
    
    def activate_user(self, uuid: str):
        """啟用用戶"""
        try:
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.auth_manager.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"❌ 找不到用戶: {uuid}")
                return False
            
            update_data = {
                'active': True,
                'reactivated_at': datetime.now(),
                'reactivated_by': 'admin_tool'
            }
            
            # 移除停用相關字段
            user_data = user_doc.to_dict()
            if 'deactivated_at' in user_data:
                update_data['deactivated_at'] = None
            if 'deactivated_by' in user_data:
                update_data['deactivated_by'] = None
            
            user_ref.update(update_data)
            
            print(f"✅ 用戶已啟用: {uuid}")
            return True
            
        except Exception as e:
            print(f"❌ 啟用用戶失敗: {str(e)}")
            return False
    
    def extend_user(self, uuid: str, extend_days: int):
        """延長用戶有效期"""
        try:
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.auth_manager.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"❌ 找不到用戶: {uuid}")
                return False
            
            user_data = user_doc.to_dict()
            
            # 計算新的到期時間
            current_expires = user_data.get('expires_at')
            if current_expires:
                if isinstance(current_expires, str):
                    current_expires = datetime.fromisoformat(current_expires.replace('Z', ''))
                else:
                    current_expires = current_expires.replace(tzinfo=None)
                
                # 如果已過期，從現在開始計算
                if current_expires < datetime.now():
                    new_expires = datetime.now() + timedelta(days=extend_days)
                else:
                    new_expires = current_expires + timedelta(days=extend_days)
            else:
                # 如果原本是永久，從現在開始計算
                new_expires = datetime.now() + timedelta(days=extend_days)
            
            user_ref.update({
                'expires_at': new_expires.isoformat(),
                'extended_at': datetime.now(),
                'extended_by': 'admin_tool'
            })
            
            print(f"✅ 用戶有效期已延長:")
            print(f"   UUID: {uuid}")
            print(f"   新到期時間: {new_expires.strftime('%Y-%m-%d %H:%M:%S')}")
            return True
            
        except Exception as e:
            print(f"❌ 延長用戶有效期失敗: {str(e)}")
            return False
    
    def get_user_info(self, uuid: str):
        """獲取用戶詳細信息"""
        try:
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.auth_manager.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"❌ 找不到用戶: {uuid}")
                return False
            
            user_data = user_doc.to_dict()
            
            print(f"\n📊 用戶詳細信息:")
            print("-" * 50)
            print(f"UUID: {uuid}")
            print(f"UUID Hash: {uuid_hash}")
            print(f"顯示名稱: {user_data.get('display_name', 'Unknown')}")
            print(f"狀態: {'啟用' if user_data.get('active', True) else '停用'}")
            
            # 權限信息
            permissions = user_data.get('permissions', {})
            print(f"腳本權限: {'是' if permissions.get('script_access', False) else '否'}")
            print(f"配置權限: {'是' if permissions.get('config_modify', False) else '否'}")
            
            # 時間信息
            created_at = user_data.get('created_at')
            if created_at:
                if hasattr(created_at, 'timestamp'):
                    created_str = datetime.fromtimestamp(created_at.timestamp()).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    created_str = str(created_at)
                print(f"創建時間: {created_str}")
            
            expires_at = user_data.get('expires_at')
            if expires_at:
                if isinstance(expires_at, str):
                    expires_str = expires_at.split('T')[0] + ' ' + expires_at.split('T')[1].split('.')[0]
                else:
                    expires_str = str(expires_at)
                print(f"到期時間: {expires_str}")
            else:
                print(f"到期時間: 永久")
            
            last_login = user_data.get('last_login')
            if last_login:
                if hasattr(last_login, 'timestamp'):
                    login_str = datetime.fromtimestamp(last_login.timestamp()).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    login_str = str(last_login)
                print(f"最後登入: {login_str}")
            else:
                print(f"最後登入: 從未登入")
            
            print(f"登入次數: {user_data.get('login_count', 0)}")
            
            # 檢查是否有活躍會話
            active_sessions = self.get_active_sessions_summary()
            if uuid_hash in active_sessions:
                session_id = active_sessions[uuid_hash]
                print(f"目前狀態: 在線 (會話ID: {session_id[:16]}...)")
            else:
                print(f"目前狀態: 離線")
            
            # 備註信息
            notes = user_data.get('notes')
            if notes:
                print(f"備註: {notes}")
            
            return True
            
        except Exception as e:
            print(f"❌ 獲取用戶信息失敗: {str(e)}")
            return False
    
    def delete_user(self, uuid: str):
        """刪除用戶（危險操作）"""
        print(f"⚠️  這是危險操作，將永久刪除用戶: {uuid}")
        confirm = input("請輸入 'DELETE' 確認刪除: ")
        
        if confirm != 'DELETE':
            print("❌ 操作已取消")
            return False
        
        try:
            uuid_hash = hashlib.sha256(uuid.encode()).hexdigest()
            user_ref = self.auth_manager.db.collection('authorized_users').document(uuid_hash)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"❌ 找不到用戶: {uuid}")
                return False
            
            # 先強制登出用戶
            self.auth_manager.force_logout_user(uuid)
            
            # 然後刪除用戶記錄
            user_ref.delete()
            print(f"✅ 用戶已刪除: {uuid}")
            return True
            
        except Exception as e:
            print(f"❌ 刪除用戶失敗: {str(e)}")
            return False
    
    def show_unauthorized_attempts(self, limit: int = 10):
        """顯示未授權登入嘗試"""
        try:
            attempts_ref = self.auth_manager.db.collection('unauthorized_attempts')
            attempts = attempts_ref.order_by('timestamp', direction='DESCENDING').limit(limit).stream()
            
            print(f"\n🚨 最近 {limit} 次未授權登入嘗試:")
            print("-" * 80)
            print(f"{'時間':<20} {'UUID Hash (前16位)':<20} {'IP地址':<15} {'作業系統':<15}")
            print("-" * 80)
            
            attempt_count = 0
            for attempt in attempts:
                attempt_data = attempt.to_dict()
                attempt_count += 1
                
                timestamp = attempt_data.get('timestamp')
                if hasattr(timestamp, 'timestamp'):
                    time_str = datetime.fromtimestamp(timestamp.timestamp()).strftime('%Y-%m-%d %H:%M:%S')
                else:
                    time_str = str(timestamp)[:19]
                
                uuid_hash = attempt_data.get('uuid_hash', 'Unknown')[:16]
                ip_address = attempt_data.get('ip_address', 'Unknown')
                machine_info = attempt_data.get('machine_info', {})
                os_info = machine_info.get('os', 'Unknown')
                
                print(f"{time_str:<20} {uuid_hash:<20} {ip_address:<15} {os_info:<15}")
            
            print("-" * 80)
            print(f"總計: {attempt_count} 次嘗試")
            
        except Exception as e:
            print(f"❌ 顯示未授權嘗試失敗: {str(e)}")

def main():
    """主函數"""
    user_manager = UserManager()
    
    while True:
        print("\n" + "="*70)
        print("🔥 Firebase 用戶管理工具 - 支援會話管理")
        print("="*70)
        print("👥 用戶管理:")
        print("1. 添加用戶")
        print("2. 列出所有用戶")
        print("3. 查看用戶詳細信息")
        print("4. 停用用戶")
        print("5. 啟用用戶")
        print("6. 延長用戶有效期")
        print("7. 刪除用戶")
        print()
        print("📱 會話管理:")
        print("8. 查看活躍會話")
        print("9. 查看會話詳細信息")
        print("10. 強制登出用戶")
        print("11. 清理過期會話")
        print()
        print("🚨 安全日誌:")
        print("12. 查看未授權嘗試")
        print()
        print("0. 退出")
        print("-" * 70)
        
        try:
            choice = input("請選擇操作 (0-12): ").strip()
            
            if choice == '0':
                print("👋 再見！")
                break
            
            elif choice == '1':
                print("\n➕ 添加新用戶")
                uuid = input("請輸入 UUID: ").strip()
                display_name = input("請輸入顯示名稱 (可選): ").strip() or None
                
                expires_input = input("請輸入有效期天數 (0=永久, 默認30): ").strip()
                try:
                    expires_days = int(expires_input) if expires_input else 30
                except ValueError:
                    expires_days = 30
                
                script_access = input("腳本執行權限 (y/N): ").strip().lower() == 'y'
                config_modify = input("配置修改權限 (y/N): ").strip().lower() == 'y'
                
                user_manager.add_user(uuid, display_name, expires_days, script_access, config_modify)
            
            elif choice == '2':
                user_manager.list_users()
            
            elif choice == '3':
                print("\n📊 查看用戶信息")
                uuid = input("請輸入 UUID: ").strip()
                user_manager.get_user_info(uuid)
            
            elif choice == '4':
                print("\n🚫 停用用戶")
                uuid = input("請輸入要停用的 UUID: ").strip()
                user_manager.deactivate_user(uuid)
            
            elif choice == '5':
                print("\n✅ 啟用用戶")
                uuid = input("請輸入要啟用的 UUID: ").strip()
                user_manager.activate_user(uuid)
            
            elif choice == '6':
                print("\n📅 延長用戶有效期")
                uuid = input("請輸入 UUID: ").strip()
                extend_input = input("請輸入要延長的天數: ").strip()
                try:
                    extend_days = int(extend_input)
                    user_manager.extend_user(uuid, extend_days)
                except ValueError:
                    print("❌ 無效的天數")
            
            elif choice == '7':
                print("\n🗑️ 刪除用戶")
                uuid = input("請輸入要刪除的 UUID: ").strip()
                user_manager.delete_user(uuid)
            
            elif choice == '8':
                print("\n📱 查看活躍會話")
                user_manager.list_active_sessions()
            
            elif choice == '9':
                print("\n📱 查看會話詳細信息")
                session_prefix = input("請輸入會話ID前綴 (至少8個字符): ").strip()
                if len(session_prefix) >= 8:
                    user_manager.get_session_details(session_prefix)
                else:
                    print("❌ 會話ID前綴至少需要8個字符")
            
            elif choice == '10':
                print("\n🔨 強制登出用戶")
                uuid = input("請輸入要強制登出的 UUID: ").strip()
                user_manager.force_logout_user(uuid)
            
            elif choice == '11':
                print("\n🧹 清理過期會話")
                user_manager.cleanup_expired_sessions()
            
            elif choice == '12':
                print("\n🚨 查看未授權嘗試")
                limit_input = input("請輸入顯示數量 (默認10): ").strip()
                try:
                    limit = int(limit_input) if limit_input else 10
                except ValueError:
                    limit = 10
                user_manager.show_unauthorized_attempts(limit)
            
            else:
                print("❌ 無效的選擇，請重新輸入")
        
        except KeyboardInterrupt:
            print("\n\n👋 程式被中斷，再見！")
            break
        except Exception as e:
            print(f"\n❌ 發生錯誤: {str(e)}")

if __name__ == "__main__":
    main()