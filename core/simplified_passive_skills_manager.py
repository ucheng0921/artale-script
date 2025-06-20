"""
簡化版被動技能管理器 - 減少調試輸出，提升性能
"""
import time
import random
import pyautogui


class PassiveSkillsManager:
    def __init__(self):
        # 技能冷卻追踪
        self.last_used_time = {
            'skill_1': 0,
            'skill_2': 0,
            'skill_3': 0,
            'skill_4': 0
        }
        
        # 使用計數（簡化版）
        self.usage_count = {
            'skill_1': 0,
            'skill_2': 0,
            'skill_3': 0,
            'skill_4': 0
        }
        
        # 初始化時間
        self.start_time = time.time()
        
        # 簡化的調試設定
        self.check_count = 0
        self.last_status_time = 0
        self.status_interval = 300.0  # 5分鐘輸出一次狀態
        
        print("🎯 被動技能管理器已初始化")
        self._print_config()
    
    def _print_config(self):
        """顯示配置摘要 - 簡化版"""
        try:
            from config import (
                ENABLE_PASSIVE_SKILLS,
                ENABLE_PASSIVE_SKILL_1, ENABLE_PASSIVE_SKILL_2, 
                ENABLE_PASSIVE_SKILL_3, ENABLE_PASSIVE_SKILL_4
            )
            
            if not ENABLE_PASSIVE_SKILLS:
                print("❌ 被動技能已禁用")
                return
            
            enabled_skills = []
            for i in range(1, 5):
                enabled = getattr(__import__('config'), f'ENABLE_PASSIVE_SKILL_{i}')
                if enabled:
                    key = getattr(__import__('config'), f'PASSIVE_SKILL_{i}_KEY')
                    cooldown = getattr(__import__('config'), f'PASSIVE_SKILL_{i}_COOLDOWN')
                    enabled_skills.append(f"技能{i}({key}): {cooldown}s")
            
            if enabled_skills:
                print(f"✅ 啟用技能: {', '.join(enabled_skills)}")
            else:
                print("⚠️ 無啟用的被動技能")
                
        except ImportError:
            print("❌ 配置載入失敗")
    
    def check_and_use_skills(self):
        """檢查並使用可用的被動技能 - 每次只使用一個技能"""
        try:
            from config import ENABLE_PASSIVE_SKILLS
            if not ENABLE_PASSIVE_SKILLS:
                return
        except ImportError:
            return
        
        current_time = time.time()
        self.check_count += 1
        
        # 定期狀態輸出（每5分鐘）
        if current_time - self.last_status_time >= self.status_interval:
            self._print_simple_status()
            self.last_status_time = current_time
        
        # 收集所有可用的技能，並按優先級排序
        available_skills = []
        
        for skill_num in ['1', '2', '3', '4']:
            skill_id = f'skill_{skill_num}'
            
            try:
                enabled, key, cooldown = self._get_skill_config(skill_num)
                
                if not enabled:
                    continue
                
                # 檢查冷卻時間 
                last_used = self.last_used_time[skill_id]
                time_since_use = current_time - last_used

                # 如果技能可用（冷卻完成或從未使用）
                if last_used == 0 or time_since_use >= cooldown:
                    available_skills.append({
                        'skill_id': skill_id,
                        'skill_num': skill_num,
                        'key': key,
                        'cooldown': cooldown,
                        'priority': cooldown  # 冷卻時間越長，優先級越高
                    })
                    
            except (ImportError, AttributeError):
                continue
        
        # 如果有可用技能，選擇優先級最高的（冷卻時間最長的）
        if available_skills:
            # 按優先級排序（冷卻時間降序）
            available_skills.sort(key=lambda x: x['priority'], reverse=True)
            
            # 使用優先級最高的技能
            skill_to_use = available_skills[0]
            self._use_skill(
                skill_to_use['skill_id'], 
                skill_to_use['key'], 
                skill_to_use['skill_num'], 
                current_time
            )
    
    def _print_simple_status(self):
        """輸出簡化的狀態信息"""
        total_uses = sum(self.usage_count.values())
        uptime_minutes = (time.time() - self.start_time) / 60
        
        print(f"📊 被動技能狀態: 運行{uptime_minutes:.1f}分鐘, 總使用{total_uses}次")
    
    def _get_skill_config(self, skill_num):
        """獲取技能配置"""
        config_map = {
            '1': ('ENABLE_PASSIVE_SKILL_1', 'PASSIVE_SKILL_1_KEY', 'PASSIVE_SKILL_1_COOLDOWN'),
            '2': ('ENABLE_PASSIVE_SKILL_2', 'PASSIVE_SKILL_2_KEY', 'PASSIVE_SKILL_2_COOLDOWN'),
            '3': ('ENABLE_PASSIVE_SKILL_3', 'PASSIVE_SKILL_3_KEY', 'PASSIVE_SKILL_3_COOLDOWN'),
            '4': ('ENABLE_PASSIVE_SKILL_4', 'PASSIVE_SKILL_4_KEY', 'PASSIVE_SKILL_4_COOLDOWN')
        }
        
        enable_attr, key_attr, cooldown_attr = config_map[skill_num]
        
        import config
        enabled = getattr(config, enable_attr)
        key = getattr(config, key_attr)
        cooldown = getattr(config, cooldown_attr)
        
        return enabled, key, cooldown
    

    def _use_skill(self, skill_id, key, skill_num, current_time):
        """使用技能 - 簡化版，減少調試輸出"""
        try:
            from config import PASSIVE_SKILL_RANDOM_DELAY_MIN, PASSIVE_SKILL_RANDOM_DELAY_MAX
            
            # 隨機延遲
            if PASSIVE_SKILL_RANDOM_DELAY_MAX > PASSIVE_SKILL_RANDOM_DELAY_MIN:
                delay = random.uniform(PASSIVE_SKILL_RANDOM_DELAY_MIN, PASSIVE_SKILL_RANDOM_DELAY_MAX)
                time.sleep(delay)
            
            # 檢查按鍵是否有效
            if not key or len(key.strip()) == 0:
                return False
            
            # 執行按鍵操作
            pyautogui.keyDown(key)
            time.sleep(0.05)  # 添加小延遲確保按鍵註冊
            pyautogui.keyUp(key)
            
            # 更新記錄
            self.last_used_time[skill_id] = current_time
            self.usage_count[skill_id] += 1
            
            # 簡化的成功提示（只在首次使用或每10次使用時顯示）
            count = self.usage_count[skill_id]
            if count == 1 or count % 10 == 0:
                print(f"🎯 技能{skill_num}({key}) 已使用 {count}次")
            
            return True
            
        except Exception as e:
            print(f"❌ 技能{skill_num}使用失敗: {e}")
            return False
    
    def get_enabled_skills_count(self):
        """獲取啟用的技能數量"""
        try:
            from config import (
                ENABLE_PASSIVE_SKILLS,
                ENABLE_PASSIVE_SKILL_1, ENABLE_PASSIVE_SKILL_2, 
                ENABLE_PASSIVE_SKILL_3, ENABLE_PASSIVE_SKILL_4
            )
            
            if not ENABLE_PASSIVE_SKILLS:
                return 0
            
            return sum([
                ENABLE_PASSIVE_SKILL_1,
                ENABLE_PASSIVE_SKILL_2,
                ENABLE_PASSIVE_SKILL_3,
                ENABLE_PASSIVE_SKILL_4
            ])
            
        except ImportError:
            return 0
    
    def reset_all_cooldowns(self):
        """重置所有技能冷卻（調試用）"""
        print("🔄 重置所有技能冷卻時間")
        for skill_id in self.last_used_time:
            self.last_used_time[skill_id] = 0
        print("✅ 所有技能冷卻已重置")
    
    def get_simple_stats(self):
        """獲取簡化統計信息"""
        uptime = time.time() - self.start_time
        total_used = sum(self.usage_count.values())
        enabled_count = self.get_enabled_skills_count()
        
        return {
            'uptime_minutes': uptime / 60,
            'total_uses': total_used,
            'enabled_skills': enabled_count,
            'check_count': self.check_count
        }
    
    def force_use_next_skill(self):
        """強制使用下一個可用技能（調試用）"""
        current_time = time.time()
        
        # 找到下一個可用技能
        for skill_num in ['1', '2', '3', '4']:
            skill_id = f'skill_{skill_num}'
            try:
                enabled, key, cooldown = self._get_skill_config(skill_num)
                if enabled:
                    print(f"🚨 [強制] 強制使用技能{skill_num}({key})")
                    success = self._use_skill(skill_id, key, skill_num, current_time)
                    return success
            except Exception as e:
                print(f"❌ [強制] 技能{skill_num}配置錯誤: {e}")
                continue
        
        print("❌ [強制] 沒有可用的技能")
        return False