"""
配置管理器 - 處理GUI與腳本配置的同步（支援外部配置文件）
"""
import os
import sys
import importlib
from typing import Dict, Any, Optional, Tuple
import json
import datetime

class ConfigManager:
    """配置管理器類"""
    
    def __init__(self):
        self.config_module = None
        self.config_cache = {}
        self.load_config()
    
    def load_config(self):
        """載入配置模組"""
        try:
            # 添加腳本目錄到路徑
            script_dir = os.path.dirname(os.path.dirname(__file__))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # 導入配置模組
            import config
            self.config_module = config
            
            # 載入當前配置到緩存
            self._update_cache()
            
            print("✅ 配置模組載入成功")
            print(f"💾 外部配置文件路徑: {config.get_external_config_path()}")
            return True
            
        except ImportError as e:
            print(f"❌ 配置模組載入失敗: {e}")
            return False
    
    def _update_cache(self):
        """更新配置緩存"""
        if not self.config_module:
            return
        
        # 獲取所有配置項
        config_items = {
            name: getattr(self.config_module, name)
            for name in dir(self.config_module)
            if not name.startswith('_') and not callable(getattr(self.config_module, name))
        }
        
        self.config_cache = config_items
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        if self.config_module and hasattr(self.config_module, key):
            return getattr(self.config_module, key)
        return self.config_cache.get(key, default)
    
    def set_config(self, key: str, value: Any) -> bool:
        """設置配置值"""
        try:
            if self.config_module:
                # 設置到模組中
                setattr(self.config_module, key, value)
                
                # 更新緩存
                self.config_cache[key] = value
                
                print(f"✅ 配置已更新: {key} = {value}")
                return True
            else:
                print("❌ 配置模組未載入")
                return False
                
        except Exception as e:
            print(f"❌ 設置配置失敗: {e}")
            return False
    
    def update_configs(self, config_dict: Dict[str, Any]) -> bool:
        """批量更新配置"""
        success_count = 0
        
        for key, value in config_dict.items():
            if self.set_config(key, value):
                success_count += 1
        
        print(f"✅ 配置批量更新完成: {success_count}/{len(config_dict)} 項成功")
        return success_count == len(config_dict)
    
    def get_gui_relevant_configs(self) -> Dict[str, Any]:
        """獲取與GUI相關的配置"""
        gui_configs = {}
        
        # 定義GUI相關的配置項 - 只包含指定的參數
        gui_config_keys = [
            # 怪物檢測與攻擊配置
            'ENABLED_MONSTERS',
            'JUMP_KEY',
            'ATTACK_KEY',
            'SECONDARY_ATTACK_KEY',
            'ENABLE_SECONDARY_ATTACK',
            'PRIMARY_ATTACK_CHANCE',
            'SECONDARY_ATTACK_CHANCE',
            'ATTACK_RANGE_X',
            'JUMP_ATTACK_MODE',
            
            # 被動技能系統配置 - 移除觸發條件相關
            'ENABLE_PASSIVE_SKILLS',
            'PASSIVE_SKILL_1_KEY',
            'PASSIVE_SKILL_2_KEY',
            'PASSIVE_SKILL_3_KEY',
            'PASSIVE_SKILL_4_KEY',
            'PASSIVE_SKILL_1_COOLDOWN',
            'PASSIVE_SKILL_2_COOLDOWN',
            'PASSIVE_SKILL_3_COOLDOWN',
            'PASSIVE_SKILL_4_COOLDOWN',
            'ENABLE_PASSIVE_SKILL_1',
            'ENABLE_PASSIVE_SKILL_2',
            'ENABLE_PASSIVE_SKILL_3',
            'ENABLE_PASSIVE_SKILL_4',
            'PASSIVE_SKILL_RANDOM_DELAY_MIN',
            'PASSIVE_SKILL_RANDOM_DELAY_MAX',
            
            # 隨機下跳功能配置
            'ENABLE_RANDOM_DOWN_JUMP',
            'RANDOM_DOWN_JUMP_MIN_INTERVAL',
            'RANDOM_DOWN_JUMP_MAX_INTERVAL',
            
            # 增強移動系統配置
            'ENABLE_ENHANCED_MOVEMENT',
            'ENABLE_JUMP_MOVEMENT',
            'JUMP_MOVEMENT_CHANCE',
            'ENABLE_DASH_MOVEMENT',
            'DASH_MOVEMENT_CHANCE',
            'DASH_SKILL_KEY',
            'DASH_SKILL_COOLDOWN',
            'ROPE_COOLDOWN_TIME',
            
            # 紅點偵測與換頻道配置
            'ENABLE_RED_DOT_DETECTION',
            'RED_DOT_MIN_TIME',
            'RED_DOT_MAX_TIME',
            
            # 檢測參數配置
            'Y_LAYER_THRESHOLD',
        ]
        
        for key in gui_config_keys:
            gui_configs[key] = self.get_config(key)
        
        return gui_configs
    
    def validate_config(self, key: str, value: Any) -> Tuple[bool, str]:
        """驗證配置值"""
        validators = {
            # 攻擊相關
            'PRIMARY_ATTACK_CHANCE': lambda x: (0.0 <= x <= 1.0, "機率必須在0.0-1.0之間"),
            'SECONDARY_ATTACK_CHANCE': lambda x: (0.0 <= x <= 1.0, "機率必須在0.0-1.0之間"),
            'ATTACK_RANGE_X': lambda x: (x > 0, "攻擊範圍必須大於0"),
            
            # 移動相關
            'JUMP_MOVEMENT_CHANCE': lambda x: (0.0 <= x <= 1.0, "機率必須在0.0-1.0之間"),
            'DASH_MOVEMENT_CHANCE': lambda x: (0.0 <= x <= 1.0, "機率必須在0.0-1.0之間"),
            'DASH_SKILL_COOLDOWN': lambda x: (x >= 0, "冷卻時間不能為負數"),
            'ROPE_COOLDOWN_TIME': lambda x: (x >= 0, "冷卻時間不能為負數"),
            
            # 被動技能相關
            'PASSIVE_SKILL_1_COOLDOWN': lambda x: (x >= 1.0, "冷卻時間必須至少1秒"),
            'PASSIVE_SKILL_2_COOLDOWN': lambda x: (x >= 1.0, "冷卻時間必須至少1秒"),
            'PASSIVE_SKILL_3_COOLDOWN': lambda x: (x >= 1.0, "冷卻時間必須至少1秒"),
            'PASSIVE_SKILL_4_COOLDOWN': lambda x: (x >= 1.0, "冷卻時間必須至少1秒"),
            'PASSIVE_SKILL_RANDOM_DELAY_MIN': lambda x: (x >= 0, "延遲時間不能為負數"),
            'PASSIVE_SKILL_RANDOM_DELAY_MAX': lambda x: (x >= 0, "延遲時間不能為負數"),
            
            # 隨機下跳相關
            'RANDOM_DOWN_JUMP_MIN_INTERVAL': lambda x: (x >= 5.0, "最小間隔建議至少5秒"),
            'RANDOM_DOWN_JUMP_MAX_INTERVAL': lambda x: (x >= 10.0, "最大間隔建議至少10秒"),
            
            # 紅點偵測相關
            'RED_DOT_MIN_TIME': lambda x: (x > 0, "時間必須大於0"),
            'RED_DOT_MAX_TIME': lambda x: (x > 0, "時間必須大於0"),
            
            # 檢測參數相關
            'Y_LAYER_THRESHOLD': lambda x: (x > 0, "閾值必須大於0"),
            
            # 按鍵相關 - 支援常見按鍵名稱
            'JUMP_KEY': lambda x: self._validate_key(x),
            'DASH_SKILL_KEY': lambda x: self._validate_key(x),
            'ATTACK_KEY': lambda x: self._validate_key(x),
            'SECONDARY_ATTACK_KEY': lambda x: self._validate_key(x),
            'PASSIVE_SKILL_1_KEY': lambda x: self._validate_key(x),
            'PASSIVE_SKILL_2_KEY': lambda x: self._validate_key(x),
            'PASSIVE_SKILL_3_KEY': lambda x: self._validate_key(x),
            'PASSIVE_SKILL_4_KEY': lambda x: self._validate_key(x),
            
            # 選擇類型
            'JUMP_ATTACK_MODE': lambda x: (x in ['original', 'mage', 'disabled'], "攻擊模式必須是 original, mage 或 disabled"),
        }
        
        if key in validators:
            try:
                result = validators[key](value)
                if isinstance(result, tuple):
                    return result
                else:
                    return result, "OK"
            except Exception as e:
                return False, f"驗證錯誤: {str(e)}"
        
        return True, "OK"
    
    def _validate_key(self, key_value: str) -> Tuple[bool, str]:
        """驗證按鍵值 - 支援單字符和常見按鍵名稱"""
        if not isinstance(key_value, str) or len(key_value) == 0:
            return False, "按鍵不能為空"
        
        # 常見的有效按鍵名稱
        valid_keys = [
            # 單字符按鍵
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
            'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
            '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
            # 特殊按鍵
            'alt', 'ctrl', 'shift', 'space', 'enter', 'tab', 'esc', 'escape',
            'up', 'down', 'left', 'right', 'home', 'end', 'pageup', 'pagedown',
            'insert', 'delete', 'backspace', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6',
            'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
        ]
        
        key_lower = key_value.lower()
        
        # 檢查是否為有效按鍵
        if key_lower in valid_keys:
            return True, "OK"
        
        # 如果是單個字符，也接受
        if len(key_value) == 1:
            return True, "OK"
        
        return False, f"無效的按鍵: {key_value}。支援單字符或常見按鍵名稱(如: alt, ctrl, space等)"
    
    def get_config_descriptions(self) -> Dict[str, Dict[str, str]]:
        """獲取配置項描述，按分類組織"""
        descriptions = {
            "怪物檢測與攻擊配置": {
                'ENABLED_MONSTERS': '啟用的怪物類型',
                'JUMP_KEY': '跳躍按鍵',
                'ATTACK_KEY': '主要攻擊按鍵',
                'SECONDARY_ATTACK_KEY': '次要攻擊按鍵',
                'ENABLE_SECONDARY_ATTACK': '啟用次要攻擊按鍵',
                'PRIMARY_ATTACK_CHANCE': '主要攻擊機率 (0.0-1.0)',
                'SECONDARY_ATTACK_CHANCE': '次要攻擊機率 (0.0-1.0)',
                'ATTACK_RANGE_X': '攻擊範圍X軸 (像素)',
                'JUMP_ATTACK_MODE': '上跳攻擊模式(mage請至下設定位移按鍵)',
            },
            "被動技能系統配置": {
                'ENABLE_PASSIVE_SKILLS': '啟用被動技能系統',
                'PASSIVE_SKILL_1_KEY': '被動技能1按鍵',
                'PASSIVE_SKILL_1_COOLDOWN': '被動技能1冷卻時間 (秒)',
                'ENABLE_PASSIVE_SKILL_1': '啟用被動技能1',
                'PASSIVE_SKILL_2_KEY': '被動技能2按鍵',
                'PASSIVE_SKILL_2_COOLDOWN': '被動技能2冷卻時間 (秒)',
                'ENABLE_PASSIVE_SKILL_2': '啟用被動技能2',
                'PASSIVE_SKILL_3_KEY': '被動技能3按鍵',
                'PASSIVE_SKILL_3_COOLDOWN': '被動技能3冷卻時間 (秒)',
                'ENABLE_PASSIVE_SKILL_3': '啟用被動技能3',
                'PASSIVE_SKILL_4_KEY': '被動技能4按鍵',
                'PASSIVE_SKILL_4_COOLDOWN': '被動技能4冷卻時間 (秒)',
                'ENABLE_PASSIVE_SKILL_4': '啟用被動技能4',
                'PASSIVE_SKILL_RANDOM_DELAY_MIN': '隨機延遲最小值 (秒)',
                'PASSIVE_SKILL_RANDOM_DELAY_MAX': '隨機延遲最大值 (秒)',
            },
            "隨機下跳功能配置": {
                'ENABLE_RANDOM_DOWN_JUMP': '啟用隨機下跳',
                'RANDOM_DOWN_JUMP_MIN_INTERVAL': '下跳最小間隔 (秒)',
                'RANDOM_DOWN_JUMP_MAX_INTERVAL': '下跳最大間隔 (秒)',
            },
            "增強移動系統配置": {
                'ENABLE_ENHANCED_MOVEMENT': '啟用增強移動',
                'ENABLE_JUMP_MOVEMENT': '啟用跳躍移動',
                'JUMP_MOVEMENT_CHANCE': '跳躍移動機率 (0.0-1.0)',
                'ENABLE_DASH_MOVEMENT': '啟用位移技能移動',
                'DASH_MOVEMENT_CHANCE': '位移技能移動機率 (0.0-1.0)',
                'DASH_SKILL_KEY': '位移技能按鍵',
                'DASH_SKILL_COOLDOWN': '位移技能冷卻時間 (秒)',
            },
            "攀爬配置": {
                'ROPE_COOLDOWN_TIME': '爬繩冷卻時間 (秒)',
            },
            "紅點偵測與換頻道配置": {
                'ENABLE_RED_DOT_DETECTION': '啟用紅點偵測',
                'RED_DOT_MIN_TIME': '紅點檢測最小時間 (秒)',
                'RED_DOT_MAX_TIME': '紅點檢測最大時間 (秒)',
            },
            "檢測參數配置": {
                'Y_LAYER_THRESHOLD': 'Y軸樓層差異閾值 (像素)',
            }
        }
        return descriptions
    
    def get_config_types(self) -> Dict[str, str]:
        """獲取配置項的數據類型"""
        types = {
            # 怪物檢測與攻擊配置
            'ENABLED_MONSTERS': 'list',
            'JUMP_KEY': 'str',
            'ATTACK_KEY': 'str',
            'SECONDARY_ATTACK_KEY': 'str',
            'ENABLE_SECONDARY_ATTACK': 'bool',
            'PRIMARY_ATTACK_CHANCE': 'float',
            'SECONDARY_ATTACK_CHANCE': 'float',
            'ATTACK_RANGE_X': 'int',
            'JUMP_ATTACK_MODE': 'choice',
            
            # 被動技能系統配置
            'ENABLE_PASSIVE_SKILLS': 'bool',
            'PASSIVE_SKILL_1_KEY': 'str',
            'PASSIVE_SKILL_2_KEY': 'str',
            'PASSIVE_SKILL_3_KEY': 'str',
            'PASSIVE_SKILL_4_KEY': 'str',
            'PASSIVE_SKILL_1_COOLDOWN': 'float',
            'PASSIVE_SKILL_2_COOLDOWN': 'float',
            'PASSIVE_SKILL_3_COOLDOWN': 'float',
            'PASSIVE_SKILL_4_COOLDOWN': 'float',
            'ENABLE_PASSIVE_SKILL_1': 'bool',
            'ENABLE_PASSIVE_SKILL_2': 'bool',
            'ENABLE_PASSIVE_SKILL_3': 'bool',
            'ENABLE_PASSIVE_SKILL_4': 'bool',
            'PASSIVE_SKILL_RANDOM_DELAY_MIN': 'float',
            'PASSIVE_SKILL_RANDOM_DELAY_MAX': 'float',
            
            # 隨機下跳功能配置
            'ENABLE_RANDOM_DOWN_JUMP': 'bool',
            'RANDOM_DOWN_JUMP_MIN_INTERVAL': 'float',
            'RANDOM_DOWN_JUMP_MAX_INTERVAL': 'float',
            
            # 增強移動系統配置
            'ENABLE_ENHANCED_MOVEMENT': 'bool',
            'ENABLE_JUMP_MOVEMENT': 'bool',
            'JUMP_MOVEMENT_CHANCE': 'float',
            'ENABLE_DASH_MOVEMENT': 'bool',
            'DASH_MOVEMENT_CHANCE': 'float',
            'DASH_SKILL_KEY': 'str',
            'DASH_SKILL_COOLDOWN': 'float',
            'ROPE_COOLDOWN_TIME': 'float',
            
            # 紅點偵測與換頻道配置
            'ENABLE_RED_DOT_DETECTION': 'bool',
            'RED_DOT_MIN_TIME': 'float',
            'RED_DOT_MAX_TIME': 'float',
            
            # 檢測參數配置
            'Y_LAYER_THRESHOLD': 'int',
        }
        return types
    
    def get_config_choices(self) -> Dict[str, list]:
        """獲取選擇類型配置的選項"""
        choices = {
            'JUMP_ATTACK_MODE': ['original', 'mage', 'disabled'],
        }
        return choices
    
    def save_config_to_file(self, filepath: Optional[str] = None) -> bool:
        """保存配置到外部文件（使用config模組功能）"""
        try:
            if not self.config_module:
                print("❌ 配置模組未載入")
                return False
            
            # 獲取當前配置
            current_configs = self.get_gui_relevant_configs()
            
            # 使用config模組的保存功能
            success = self.config_module.save_external_config(current_configs)
            
            if success:
                print(f"✅ 配置已保存到外部文件")
            else:
                print(f"❌ 保存外部配置失敗")
            
            return success
            
        except Exception as e:
            print(f"❌ 保存配置到文件失敗: {e}")
            return False
    
    def load_config_from_file(self, filepath: Optional[str] = None) -> bool:
        """從外部文件載入配置（使用config模組功能）"""
        try:
            if not self.config_module:
                print("❌ 配置模組未載入")
                return False
            
            # 使用config模組的重新載入功能
            success = self.config_module.reload_config()
            
            if success:
                # 更新本地緩存
                self._update_cache()
                print(f"✅ 配置已從外部文件載入")
            else:
                print(f"❌ 載入外部配置失敗")
            
            return success
            
        except Exception as e:
            print(f"❌ 從文件載入配置失敗: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """重置到默認配置"""
        try:
            # 重新載入配置模組以獲取默認值
            if self.config_module:
                importlib.reload(self.config_module)
                self._update_cache()
                print("✅ 配置已重置為默認值")
                
                # 刪除外部配置文件
                try:
                    external_config_path = self.config_module.get_external_config_path()
                    if external_config_path.exists():
                        external_config_path.unlink()
                        print("✅ 外部配置文件已刪除")
                except Exception as e:
                    print(f"⚠️ 刪除外部配置文件失敗: {e}")
                
                return True
            else:
                print("❌ 配置模組未載入")
                return False
                
        except Exception as e:
            print(f"❌ 重置配置失敗: {e}")
            return False
    
    def export_config_template(self, filepath: Optional[str] = None) -> bool:
        """導出配置模板"""
        try:
            if not filepath:
                if self.config_module:
                    app_path = self.config_module.get_application_path()
                    filepath = app_path / 'config_template.json'
                else:
                    filepath = os.path.join(os.path.dirname(__file__), 'config_template.json')
            
            # 獲取配置和描述
            configs = self.get_gui_relevant_configs()
            descriptions = self.get_config_descriptions()
            types = self.get_config_types()
            choices = self.get_config_choices()
            
            # 創建模板
            template = {
                "_description": "Artale Script 配置模板",
                "_note": "修改配置值後重新載入即可生效",
                "_categories": {}
            }
            
            # 按分類組織
            for category, category_configs in descriptions.items():
                template["_categories"][category] = {}
                for key, description in category_configs.items():
                    config_type = types.get(key, "unknown")
                    config_choices = choices.get(key, [])
                    
                    template["_categories"][category][key] = {
                        "value": configs.get(key),
                        "description": description,
                        "type": config_type,
                        "choices": config_choices if config_choices else None
                    }
            
            # 保存模板
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=4, ensure_ascii=False)
            
            print(f"✅ 配置模板已導出到: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ 導出配置模板失敗: {e}")
            return False
    
    def get_external_config_status(self) -> Dict[str, Any]:
        """獲取外部配置文件狀態"""
        try:
            if not self.config_module:
                return {"error": "配置模組未載入"}
            
            config_path = self.config_module.get_external_config_path()
            
            status = {
                "path": str(config_path),
                "exists": config_path.exists(),
                "size": 0,
                "modified": None,
                "configs_count": 0
            }
            
            if config_path.exists():
                status["size"] = config_path.stat().st_size
                status["modified"] = datetime.datetime.fromtimestamp(config_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # 讀取配置數量
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                    status["configs_count"] = len(config_data.get("configs", {}))
                except:
                    status["configs_count"] = "unknown"
            
            return status
            
        except Exception as e:
            return {"error": str(e)}