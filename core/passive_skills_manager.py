"""
修復版被動技能管理器 - 增加詳細調試信息和問題診斷
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
        
        # 使用計數
        self.usage_count = {
            'skill_1': 0,
            'skill_2': 0,
            'skill_3': 0,
            'skill_4': 0
        }
        
        # 初始化時間
        self.start_time = time.time()
        
        # ★★★ 新增：調試標誌 ★★★
        self.debug_mode = True
        self.last_debug_time = 0
        self.debug_interval = 10.0  # 每10秒輸出一次調試信息
        
        # ★★★ 新增：檢查計數器 ★★★
        self.check_count = 0
        self.successful_use_count = 0
        
        print("🎯 被動技能管理器已初始化")
        self._print_config()
        self._validate_pyautogui()
    
    def _validate_pyautogui(self):
        """驗證 pyautogui 是否正常工作"""
        try:
            # 測試 pyautogui 功能
            current_pos = pyautogui.position()
            print(f"✅ pyautogui 正常運作，當前滑鼠位置: {current_pos}")
            
            # 檢查 failsafe 設置
            if pyautogui.FAILSAFE:
                print("⚠️ pyautogui.FAILSAFE 已啟用，可能會阻止按鍵操作")
            
            return True
        except Exception as e:
            print(f"❌ pyautogui 驗證失敗: {e}")
            return False
    
    def _print_config(self):
        """顯示配置摘要"""
        try:
            from config import (
                ENABLE_PASSIVE_SKILLS,
                PASSIVE_SKILL_1_KEY, PASSIVE_SKILL_2_KEY, PASSIVE_SKILL_3_KEY, PASSIVE_SKILL_4_KEY,
                PASSIVE_SKILL_1_COOLDOWN, PASSIVE_SKILL_2_COOLDOWN, PASSIVE_SKILL_3_COOLDOWN, PASSIVE_SKILL_4_COOLDOWN,
                ENABLE_PASSIVE_SKILL_1, ENABLE_PASSIVE_SKILL_2, ENABLE_PASSIVE_SKILL_3, ENABLE_PASSIVE_SKILL_4,
                PASSIVE_SKILL_RANDOM_DELAY_MIN, PASSIVE_SKILL_RANDOM_DELAY_MAX
            )
            
            if not ENABLE_PASSIVE_SKILLS:
                print("❌ 被動技能已禁用")
                return
            
            skills = [
                (1, ENABLE_PASSIVE_SKILL_1, PASSIVE_SKILL_1_KEY, PASSIVE_SKILL_1_COOLDOWN),
                (2, ENABLE_PASSIVE_SKILL_2, PASSIVE_SKILL_2_KEY, PASSIVE_SKILL_2_COOLDOWN),
                (3, ENABLE_PASSIVE_SKILL_3, PASSIVE_SKILL_3_KEY, PASSIVE_SKILL_3_COOLDOWN),
                (4, ENABLE_PASSIVE_SKILL_4, PASSIVE_SKILL_4_KEY, PASSIVE_SKILL_4_COOLDOWN)
            ]
            
            enabled_skills = []
            for num, enabled, key, cooldown in skills:
                if enabled:
                    enabled_skills.append(f"技能{num}({key}): {cooldown}秒")
            
            if enabled_skills:
                print("✅ 啟用的被動技能:")
                for skill in enabled_skills:
                    print(f"   {skill}")
                print(f"   隨機延遲: {PASSIVE_SKILL_RANDOM_DELAY_MIN}-{PASSIVE_SKILL_RANDOM_DELAY_MAX}秒")
            else:
                print("⚠️ 無啟用的被動技能")
                
        except ImportError as e:
            print(f"❌ 配置載入失敗: {e}")
    
    def check_and_use_skills(self):
        """檢查並使用可用的被動技能 - 增強版"""
        try:
            from config import ENABLE_PASSIVE_SKILLS
            if not ENABLE_PASSIVE_SKILLS:
                if self.debug_mode and self.check_count % 50 == 0:  # 每50次檢查提醒一次
                    print("❌ 被動技能功能已禁用")
                return
        except ImportError:
            if self.debug_mode and self.check_count % 50 == 0:
                print("❌ 無法載入被動技能配置")
            return
        
        current_time = time.time()
        self.check_count += 1
        
        # ★★★ 調試信息：定期輸出狀態 ★★★
        if self.debug_mode and current_time - self.last_debug_time >= self.debug_interval:
            self._print_debug_status(current_time)
            self.last_debug_time = current_time
        
        # 檢查四個技能
        skills_checked = 0
        skills_used = 0
        
        for skill_num in ['1', '2', '3', '4']:
            skill_id = f'skill_{skill_num}'
            was_used = self._check_skill(skill_id, current_time)
            skills_checked += 1
            if was_used:
                skills_used += 1
                self.successful_use_count += 1
        
        # ★★★ 詳細調試：每次檢查的結果 ★★★
        if self.debug_mode and (skills_used > 0 or self.check_count % 100 == 0):
            print(f"🔍 [調試] 第{self.check_count}次檢查: {skills_checked}個技能檢查, {skills_used}個技能使用")
    
    def _print_debug_status(self, current_time):
        """輸出詳細的調試狀態"""
        uptime = current_time - self.start_time
        print(f"\n{'='*60}")
        print(f"🔧 被動技能調試報告 (運行時間: {uptime:.1f}秒)")
        print(f"   檢查次數: {self.check_count}")
        print(f"   成功使用: {self.successful_use_count}")
        
        # 顯示每個技能的冷卻狀態
        for i in range(1, 5):
            skill_id = f'skill_{i}'
            try:
                enabled, key, cooldown = self._get_skill_config(str(i))
                if enabled:
                    last_used = self.last_used_time[skill_id]
                    if last_used == 0:
                        status = "從未使用，可立即使用"
                    else:
                        time_since_use = current_time - last_used
                        if time_since_use >= cooldown:
                            status = f"冷卻完成，可使用 (上次使用: {time_since_use:.1f}秒前)"
                        else:
                            remaining = cooldown - time_since_use
                            status = f"冷卻中，剩餘 {remaining:.1f}秒"
                    
                    count = self.usage_count[skill_id]
                    print(f"   技能{i}({key}): {status} [使用次數: {count}]")
            except:
                print(f"   技能{i}: 配置錯誤")
        
        print(f"{'='*60}\n")
    
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
    
    def _check_skill(self, skill_id, current_time):
        """檢查單個技能是否可用並使用 - 增強版"""
        skill_num = skill_id.split('_')[1]
        
        try:
            enabled, key, cooldown = self._get_skill_config(skill_num)
            
            # 如果技能未啟用，跳過
            if not enabled:
                return False
            
            # 檢查冷卻時間 
            last_used = self.last_used_time[skill_id]
            time_since_use = current_time - last_used

            # ★★★ 修復：初始值為0時應該可以立即使用 ★★★
            if last_used > 0 and time_since_use < cooldown:
                # 還在冷卻中
                if self.debug_mode and self.check_count % 200 == int(skill_num):
                    remaining = cooldown - time_since_use
                    print(f"🕒 [調試] 技能{skill_num}({key}) 冷卻中，剩餘 {remaining:.1f}秒")
                return False

            # ★★★ 新增：確保初始狀態可以使用 ★★★
            if last_used == 0:
                print(f"🎯 [調試] 技能{skill_num}({key}) 初次可用，準備使用")
            
            # ★★★ 詳細調試：準備使用技能 ★★★
            if self.debug_mode:
                if last_used == 0:
                    print(f"🎯 [調試] 技能{skill_num}({key}) 首次使用準備中...")
                else:
                    print(f"🎯 [調試] 技能{skill_num}({key}) 冷卻完成，準備使用 (上次: {time_since_use:.1f}秒前)")
            
            # 使用技能
            success = self._use_skill_with_debug(skill_id, key, skill_num, current_time)
            return success
                          
        except (ImportError, AttributeError) as e:
            if self.debug_mode:
                print(f"⚠️ [調試] 技能{skill_num}配置錯誤: {e}")
            return False
    
    def _use_skill_with_debug(self, skill_id, key, skill_num, current_time):
        """使用技能 - 增強版，包含詳細調試"""
        try:
            from config import PASSIVE_SKILL_RANDOM_DELAY_MIN, PASSIVE_SKILL_RANDOM_DELAY_MAX
            
            # ★★★ 調試：技能使用前狀態 ★★★
            print(f"🚀 [調試] 開始使用技能{skill_num}({key})")
            
            # 隨機延遲
            if PASSIVE_SKILL_RANDOM_DELAY_MAX > PASSIVE_SKILL_RANDOM_DELAY_MIN:
                delay = random.uniform(PASSIVE_SKILL_RANDOM_DELAY_MIN, PASSIVE_SKILL_RANDOM_DELAY_MAX)
                print(f"⏳ [調試] 隨機延遲 {delay:.2f}秒")
                time.sleep(delay)
            
            # ★★★ 詳細調試：按鍵操作 ★★★
            print(f"⌨️ [調試] 準備按下按鍵: {key}")
            
            # 檢查按鍵是否有效
            if not key or len(key.strip()) == 0:
                print(f"❌ [調試] 無效的按鍵: '{key}'")
                return False
            
            # 嘗試按鍵操作
            try:
                print(f"⌨️ [調試] 執行 pyautogui.keyDown('{key}')")
                pyautogui.keyDown(key)
                
                print(f"⌨️ [調試] 執行 pyautogui.keyUp('{key}')")
                pyautogui.keyUp(key)
                
                print(f"✅ [調試] 按鍵操作完成: {key}")
                
            except Exception as key_error:
                print(f"❌ [調試] 按鍵操作失敗: {key_error}")
                return False
            
            # 更新記錄
            self.last_used_time[skill_id] = current_time
            self.usage_count[skill_id] += 1
            
            print(f"🎯 使用技能{skill_num}({key}) - 總計: {self.usage_count[skill_id]}次")
            print(f"✅ [調試] 技能{skill_num}使用成功，下次可用時間: {current_time + self._get_skill_config(skill_num)[2]:.1f}")
            
            return True
            
        except Exception as e:
            print(f"❌ [調試] 技能{skill_num}({key})使用過程失敗: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False
    
    def force_use_skill(self, skill_num):
        """強制使用技能（調試用）"""
        skill_id = f'skill_{skill_num}'
        try:
            enabled, key, cooldown = self._get_skill_config(str(skill_num))
            if enabled:
                print(f"🚨 [強制] 強制使用技能{skill_num}({key})")
                success = self._use_skill_with_debug(skill_id, key, str(skill_num), time.time())
                return success
            else:
                print(f"❌ [強制] 技能{skill_num}未啟用")
                return False
        except Exception as e:
            print(f"❌ [強制] 強制使用技能{skill_num}失敗: {e}")
            return False
    
    def test_all_keys(self):
        """測試所有啟用的技能按鍵（調試用）"""
        print("🧪 測試所有被動技能按鍵...")
        
        for i in range(1, 5):
            try:
                enabled, key, cooldown = self._get_skill_config(str(i))
                if enabled:
                    print(f"🧪 測試技能{i}按鍵: {key}")
                    try:
                        pyautogui.keyDown(key)
                        time.sleep(0.1)
                        pyautogui.keyUp(key)
                        print(f"✅ 技能{i}({key}) 按鍵測試成功")
                    except Exception as e:
                        print(f"❌ 技能{i}({key}) 按鍵測試失敗: {e}")
                    
                    time.sleep(0.5)  # 測試間隔
            except Exception as e:
                print(f"❌ 技能{i}配置錯誤: {e}")
    
    def reset_all_cooldowns(self):
        """重置所有技能冷卻（調試用）"""
        print("🔄 重置所有技能冷卻時間")
        for skill_id in self.last_used_time:
            self.last_used_time[skill_id] = 0
        print("✅ 所有技能冷卻已重置")
    
    def toggle_debug(self):
        """切換調試模式"""
        self.debug_mode = not self.debug_mode
        print(f"🔧 被動技能調試模式: {'開啟' if self.debug_mode else '關閉'}")
    
    def get_statistics(self):
        """獲取統計信息"""
        try:
            from config import ENABLE_PASSIVE_SKILLS
            if not ENABLE_PASSIVE_SKILLS:
                return "被動技能統計: 功能已禁用"
        except ImportError:
            return "被動技能統計: 配置載入失敗"
        
        uptime = time.time() - self.start_time
        uptime_minutes = uptime / 60
        
        total_used = sum(self.usage_count.values())
        
        stats = [
            f"被動技能統計:",
            f"  運行時間: {uptime_minutes:.1f} 分鐘",
            f"  檢查次數: {self.check_count}",
            f"  總計使用: {total_used} 次",
            f"  成功率: {self.successful_use_count}/{self.check_count} ({self.successful_use_count/max(1,self.check_count)*100:.1f}%)"
        ]
        
        # 顯示個別技能使用次數
        for i in range(1, 5):
            skill_id = f'skill_{i}'
            count = self.usage_count[skill_id]
            if count > 0:
                avg_per_minute = count / uptime_minutes if uptime_minutes > 0 else 0
                stats.append(f"  技能{i}: {count}次 ({avg_per_minute:.1f}/分鐘)")
        
        return "\n".join(stats)
    
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
    
    def validate_configuration(self):
        """驗證配置"""
        try:
            from config import ENABLE_PASSIVE_SKILLS
            if not ENABLE_PASSIVE_SKILLS:
                return ["被動技能已禁用"]
        except ImportError:
            return ["配置載入失敗"]
        
        warnings = []
        enabled_count = self.get_enabled_skills_count()
        
        if enabled_count == 0:
            warnings.append("警告: 沒有啟用任何被動技能")
        
        try:
            from config import PASSIVE_SKILL_RANDOM_DELAY_MIN, PASSIVE_SKILL_RANDOM_DELAY_MAX
            
            if PASSIVE_SKILL_RANDOM_DELAY_MIN < 0:
                warnings.append("警告: 最小延遲時間不能為負數")
            if PASSIVE_SKILL_RANDOM_DELAY_MAX < PASSIVE_SKILL_RANDOM_DELAY_MIN:
                warnings.append("警告: 最大延遲時間應大於等於最小延遲時間")
                
        except ImportError:
            warnings.append("警告: 延遲配置載入失敗")
        
        # 驗證按鍵配置
        for i in range(1, 5):
            try:
                enabled, key, cooldown = self._get_skill_config(str(i))
                if enabled:
                    if not key or len(key.strip()) == 0:
                        warnings.append(f"警告: 技能{i}按鍵為空")
                    if cooldown < 0:
                        warnings.append(f"警告: 技能{i}冷卻時間不能為負數")
            except Exception as e:
                warnings.append(f"警告: 技能{i}配置錯誤: {e}")
        
        return warnings if warnings else ["配置驗證通過"]