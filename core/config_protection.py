"""
配置保護模組 - 防止直接修改配置
"""
import hashlib
import json
import os
from datetime import datetime

class ConfigProtection:
    """配置保護類"""
    
    def __init__(self):
        self.config_hash_file = ".config_integrity"
        self.protected_configs = [
            'ENABLED_MONSTERS',
            'ATTACK_KEY',
            'SECONDARY_ATTACK_KEY', 
            'DETECTION_INTERVAL',
            'MATCH_THRESHOLD'
        ]
    
    def generate_config_hash(self, config_values: dict) -> str:
        """生成配置哈希值"""
        # 只對受保護的配置生成哈希
        protected_values = {}
        for key in self.protected_configs:
            if key in config_values:
                protected_values[key] = config_values[key]
        
        # 將配置轉為字符串並生成哈希
        config_str = json.dumps(protected_values, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def save_config_integrity(self, config_values: dict):
        """保存配置完整性信息"""
        try:
            config_hash = self.generate_config_hash(config_values)
            
            integrity_data = {
                'hash': config_hash,
                'timestamp': datetime.now().isoformat(),
                'protected_keys': self.protected_configs
            }
            
            with open(self.config_hash_file, 'w') as f:
                json.dump(integrity_data, f)
                
        except Exception as e:
            print(f"保存配置完整性失敗: {e}")
    
    def verify_config_integrity(self, current_config_values: dict) -> bool:
        """驗證配置完整性"""
        try:
            if not os.path.exists(self.config_hash_file):
                # 首次運行，保存當前配置
                self.save_config_integrity(current_config_values)
                return True
            
            # 讀取保存的哈希
            with open(self.config_hash_file, 'r') as f:
                integrity_data = json.load(f)
            
            saved_hash = integrity_data['hash']
            current_hash = self.generate_config_hash(current_config_values)
            
            if saved_hash != current_hash:
                print("⚠️ 警告：檢測到配置文件被修改")
                print("為了安全，某些配置修改需要重新認證")
                
                # 可以選擇是否允許繼續
                return self._handle_config_change(current_config_values)
            
            return True
            
        except Exception as e:
            print(f"配置完整性驗證失敗: {e}")
            return False
    
    def _handle_config_change(self, new_config_values: dict) -> bool:
        """處理配置變更"""
        print("配置變更處理選項:")
        print("1. 接受變更並更新完整性哈希")
        print("2. 拒絕變更並退出")
        
        try:
            choice = input("請選擇 (1/2): ").strip()
            
            if choice == '1':
                self.save_config_integrity(new_config_values)
                print("✅ 配置變更已接受")
                return True
            else:
                print("❌ 配置變更被拒絕")
                return False
                
        except:
            print("❌ 默認拒絕配置變更")
            return False

# 在 config.py 的最後添加保護檢查
def check_config_integrity():
    """檢查配置完整性"""
    protection = ConfigProtection()
    
    # 獲取當前配置值
    import config
    current_config = {}
    
    for attr_name in protection.protected_configs:
        if hasattr(config, attr_name):
            current_config[attr_name] = getattr(config, attr_name)
    
    # 驗證完整性
    if not protection.verify_config_integrity(current_config):
        print("配置完整性驗證失敗，程式退出")
        exit(1)

# 在 config.py 末尾調用
# check_config_integrity()