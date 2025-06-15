"""
修復版隨機下跳功能 - 增加詳細調試信息和問題診斷
"""
import time
import random
import pyautogui
from config import JUMP_KEY

class RandomDownJump:
    def __init__(self):
        # 下跳狀態追踪
        self.last_down_jump_time = 0
        self.next_down_jump_time = 0
        self.down_jump_count = 0
        
        # 狀態標誌
        self.is_down_jumping = False
        self.manager_start_time = time.time()
        
        # ★★★ 修復：調試標誌預設開啟 ★★★
        self.debug_down_jump = True
        
        # ★★★ 新增：檢查計數器 ★★★
        self.check_count = 0
        self.condition_failed_reasons = {}  # 記錄各種失敗原因
        
        # ★★★ 新增：定期調試報告 ★★★
        self.last_debug_report_time = 0
        self.debug_report_interval = 15.0  # 每15秒報告一次狀態
        
        # 初始化配置
        self.load_config()
        
        # 設定第一次下跳時間
        self.schedule_next_down_jump()
        
        print("🦘 隨機下跳功能已初始化")
        self.print_down_jump_summary()
        
        # ★★★ 新增：立即檢查配置和時間設定 ★★★
        self._validate_initial_setup()
    
    def _validate_initial_setup(self):
        """驗證初始設定"""
        current_time = time.time()
        time_until_first = self.next_down_jump_time - current_time
        
        print(f"🔧 [調試] 首次下跳時間檢查:")
        print(f"   當前時間: {current_time:.1f}")
        print(f"   下次下跳時間: {self.next_down_jump_time:.1f}")
        print(f"   距離首次下跳: {time_until_first:.1f}秒")
        
        if time_until_first < 0:
            print("⚠️ 警告: 首次下跳時間已過期，立即重新安排")
            self.schedule_next_down_jump()
        elif time_until_first > 60:
            print("⚠️ 警告: 首次下跳時間過長，可能需要等待很久")
    
    def load_config(self):
        """載入配置設定"""
        try:
            from config import (
                ENABLE_RANDOM_DOWN_JUMP,
                RANDOM_DOWN_JUMP_MIN_INTERVAL, RANDOM_DOWN_JUMP_MAX_INTERVAL,
                DOWN_JUMP_HOLD_TIME, DOWN_JUMP_CHANCE,
                DOWN_JUMP_ONLY_WHEN_MOVING, DOWN_JUMP_AVOID_DURING_ATTACK, DOWN_JUMP_AVOID_DURING_CLIMBING,
                DOWN_JUMP_WITH_DIRECTION, DOWN_JUMP_RANDOM_DIRECTION
            )
            
            self.enabled = ENABLE_RANDOM_DOWN_JUMP
            self.min_interval = RANDOM_DOWN_JUMP_MIN_INTERVAL
            self.max_interval = RANDOM_DOWN_JUMP_MAX_INTERVAL
            self.hold_time = DOWN_JUMP_HOLD_TIME
            self.execute_chance = DOWN_JUMP_CHANCE
            
            # 觸發條件
            self.only_when_moving = DOWN_JUMP_ONLY_WHEN_MOVING
            self.avoid_during_attack = DOWN_JUMP_AVOID_DURING_ATTACK
            self.avoid_during_climbing = DOWN_JUMP_AVOID_DURING_CLIMBING
            
            # 方向設定
            self.with_direction = DOWN_JUMP_WITH_DIRECTION
            self.random_direction = DOWN_JUMP_RANDOM_DIRECTION
            
            print("✅ 隨機下跳配置載入成功")
            
        except ImportError as e:
            print(f"❌ 隨機下跳配置載入失敗: {e}")
            self.enabled = False
    
    def print_down_jump_summary(self):
        """印出下跳配置摘要"""
        if not self.enabled:
            print("❌ 隨機下跳功能已禁用")
            return
        
        print("📋 隨機下跳配置摘要:")
        print(f"   ⏰ 觸發間隔: {self.min_interval}-{self.max_interval}秒")
        print(f"   🎲 執行機率: {self.execute_chance*100:.0f}%")
        print(f"   ⏱️ 按鍵保持: {self.hold_time}秒")
        
        # 觸發條件
        conditions = []
        if self.only_when_moving:
            conditions.append("僅移動時")
        if self.avoid_during_attack:
            conditions.append("避免攻擊時")
        if self.avoid_during_climbing:
            conditions.append("避免爬繩時")
        
        print(f"   🎯 觸發條件: {', '.join(conditions) if conditions else '無限制'}")
        
        # 方向設定
        direction_info = []
        if self.with_direction:
            if self.random_direction:
                direction_info.append("隨機方向")
            else:
                direction_info.append("當前移動方向")
        else:
            direction_info.append("無方向鍵")
        
        print(f"   🧭 方向設定: {', '.join(direction_info)}")
    
    def schedule_next_down_jump(self):
        """安排下一次下跳時間"""
        if not self.enabled:
            return
        
        current_time = time.time()
        interval = random.uniform(self.min_interval, self.max_interval)
        self.next_down_jump_time = current_time + interval
        
        if self.debug_down_jump:
            print(f"📅 下一次下跳安排在 {interval:.1f}秒後 (時間: {self.next_down_jump_time:.1f})")
    
    def should_execute_down_jump(self, movement_state=None, is_attacking=False, is_climbing=False):
        """判斷是否應該執行下跳 - 增強版"""
        if not self.enabled:
            return False
        
        current_time = time.time()
        self.check_count += 1
        
        # ★★★ 新增：定期調試報告 ★★★
        if self.debug_down_jump and current_time - self.last_debug_report_time >= self.debug_report_interval:
            self._print_debug_report(current_time)
            self.last_debug_report_time = current_time
        
        # 檢查是否到達預定時間
        time_until_next = self.next_down_jump_time - current_time
        if time_until_next > 0:
            if self.debug_down_jump and self.check_count % 500 == 0:  # 每500次檢查輸出一次
                print(f"⏳ [調試] 下跳時間未到，還需等待 {time_until_next:.1f}秒")
            self._record_failure_reason("時間未到")
            return False
        
        # 檢查是否正在下跳
        if self.is_down_jumping:
            if self.debug_down_jump:
                print(f"🚫 [調試] 正在下跳中，跳過檢查")
            self._record_failure_reason("正在下跳")
            return False
        
        # ★★★ 重要調試：時間到了，開始詳細檢查 ★★★
        if self.debug_down_jump:
            print(f"⏰ [調試] 下跳時間到！開始條件檢查 (檢查次數: {self.check_count})")
        
        # 檢查執行機率
        random_value = random.random()
        if random_value > self.execute_chance:
            if self.debug_down_jump:
                print(f"🎲 [調試] 下跳機率檢查未通過: {random_value:.3f} > {self.execute_chance} ({self.execute_chance*100:.0f}%)")
            self._record_failure_reason("機率未通過")
            self.schedule_next_down_jump()  # 重新安排
            return False
        
        if self.debug_down_jump:
            print(f"🎲 [調試] 下跳機率檢查通過: {random_value:.3f} <= {self.execute_chance} ({self.execute_chance*100:.0f}%)")
        
        # 檢查移動條件
        if self.only_when_moving:
            is_moving = movement_state and getattr(movement_state, 'is_moving', False)
            if not is_moving:
                if self.debug_down_jump:
                    moving_status = "無移動狀態" if not movement_state else f"is_moving={getattr(movement_state, 'is_moving', 'N/A')}"
                    print(f"🚫 [調試] 下跳條件不滿足: 需要移動但當前未移動 ({moving_status})")
                self._record_failure_reason("需要移動但未移動")
                self.schedule_next_down_jump()
                return False
        
        # 檢查攻擊條件
        if self.avoid_during_attack and is_attacking:
            if self.debug_down_jump:
                print(f"🚫 [調試] 下跳條件不滿足: 正在攻擊")
            self._record_failure_reason("正在攻擊")
            self.schedule_next_down_jump()
            return False
        
        # 檢查爬繩條件
        if self.avoid_during_climbing and is_climbing:
            if self.debug_down_jump:
                print(f"🚫 [調試] 下跳條件不滿足: 正在爬繩")
            self._record_failure_reason("正在爬繩")
            self.schedule_next_down_jump()
            return False
        
        # ★★★ 所有條件都滿足 ★★★
        if self.debug_down_jump:
            print(f"✅ [調試] 所有下跳條件都滿足，準備執行下跳！")
        
        return True
    
    def _record_failure_reason(self, reason):
        """記錄失敗原因統計"""
        if reason not in self.condition_failed_reasons:
            self.condition_failed_reasons[reason] = 0
        self.condition_failed_reasons[reason] += 1
    
    def _print_debug_report(self, current_time):
        """輸出詳細的調試報告"""
        uptime = current_time - self.manager_start_time
        time_until_next = self.next_down_jump_time - current_time
        
        print(f"\n{'='*60}")
        print(f"🦘 隨機下跳調試報告 (運行時間: {uptime:.1f}秒)")
        print(f"   檢查次數: {self.check_count}")
        print(f"   執行次數: {self.down_jump_count}")
        print(f"   成功率: {self.down_jump_count}/{self.check_count} ({self.down_jump_count/max(1,self.check_count)*100:.2f}%)")
        print(f"   距離下次下跳: {time_until_next:.1f}秒")
        
        if self.condition_failed_reasons:
            print(f"   失敗原因統計:")
            for reason, count in self.condition_failed_reasons.items():
                percentage = count / max(1, self.check_count) * 100
                print(f"     {reason}: {count}次 ({percentage:.1f}%)")
        
        print(f"{'='*60}\n")
    
    def execute_down_jump(self, current_direction=None):
        """執行下跳動作 - 增強版"""
        if not self.enabled or self.is_down_jumping:
            return False
        
        try:
            self.is_down_jumping = True
            current_time = time.time()
            
            print(f"🦘 執行隨機下跳 #{self.down_jump_count + 1}")
            
            # 決定下跳方向
            direction_key = None
            if self.with_direction:
                if self.random_direction:
                    direction_key = random.choice(['left', 'right'])
                    if self.debug_down_jump:
                        print(f"   🧭 使用隨機方向: {direction_key}")
                elif current_direction and current_direction in ['left', 'right']:
                    direction_key = current_direction
                    if self.debug_down_jump:
                        print(f"   🧭 使用當前方向: {direction_key}")
                else:
                    # 如果沒有當前方向，隨機選一個
                    direction_key = random.choice(['left', 'right'])
                    if self.debug_down_jump:
                        print(f"   🧭 無當前方向，隨機選擇: {direction_key}")
            
            # 執行下跳動作
            keys_to_press = ['down', JUMP_KEY]
            if direction_key:
                keys_to_press.append(direction_key)
            
            keys_str = ' + '.join(keys_to_press)
            print(f"   ⌨️ 按鍵組合: {keys_str} (保持 {self.hold_time}秒)")
            
            # ★★★ 新增：詳細的按鍵操作調試 ★★★
            if self.debug_down_jump:
                print(f"🔧 [調試] 開始按鍵操作序列:")
            
            # 同時按下所有按鍵
            for key in keys_to_press:
                if self.debug_down_jump:
                    print(f"🔧 [調試] 按下: {key}")
                pyautogui.keyDown(key)
            
            if self.debug_down_jump:
                print(f"🔧 [調試] 保持按鍵 {self.hold_time}秒...")
            
            # 保持指定時間
            time.sleep(self.hold_time)
            
            # 釋放所有按鍵
            for key in keys_to_press:
                if self.debug_down_jump:
                    print(f"🔧 [調試] 釋放: {key}")
                pyautogui.keyUp(key)
            
            # 更新統計
            self.down_jump_count += 1
            self.last_down_jump_time = current_time
            
            print(f"✅ 下跳執行完成 (總計: {self.down_jump_count}次)")
            
            # 安排下一次下跳
            self.schedule_next_down_jump()
            
            return True
            
        except Exception as e:
            print(f"❌ 下跳執行失敗: {e}")
            import traceback
            print(f"詳細錯誤: {traceback.format_exc()}")
            return False
        
        finally:
            self.is_down_jumping = False
    
    def check_and_execute(self, movement_state=None, is_attacking=False, is_climbing=False):
        """檢查並執行下跳（主要調用接口）- 增強版"""
        # ★★★ 新增：輸入參數調試 ★★★
        if self.debug_down_jump and self.check_count % 1000 == 0:  # 每1000次檢查輸出一次參數狀態
            moving_status = "None" if movement_state is None else getattr(movement_state, 'is_moving', 'N/A')
            direction_status = "None" if movement_state is None else getattr(movement_state, 'direction', 'N/A')
            print(f"🔧 [調試] 下跳檢查參數: moving={moving_status}, direction={direction_status}, attacking={is_attacking}, climbing={is_climbing}")
        
        if not self.should_execute_down_jump(movement_state, is_attacking, is_climbing):
            return False
        
        # 獲取當前移動方向
        current_direction = None
        if movement_state and hasattr(movement_state, 'direction'):
            current_direction = movement_state.direction
        
        return self.execute_down_jump(current_direction)
    
    def force_trigger_down_jump(self, direction=None):
        """強制觸發下跳（調試用）"""
        if not self.enabled:
            print("❌ 隨機下跳功能已禁用，無法強制觸發")
            return False
        
        print("🚨 強制觸發隨機下跳")
        return self.execute_down_jump(direction)
    
    def test_down_jump_keys(self):
        """測試下跳按鍵（調試用）"""
        print("🧪 測試下跳按鍵...")
        
        test_keys = ['down', JUMP_KEY]
        for key in test_keys:
            try:
                print(f"🧪 測試按鍵: {key}")
                pyautogui.keyDown(key)
                time.sleep(0.1)
                pyautogui.keyUp(key)
                print(f"✅ 按鍵 {key} 測試成功")
            except Exception as e:
                print(f"❌ 按鍵 {key} 測試失敗: {e}")
            time.sleep(0.3)
        
        print("✅ 下跳按鍵測試完成")
    
    def adjust_trigger_time_for_testing(self, seconds_from_now):
        """調整下次觸發時間（調試用）"""
        current_time = time.time()
        self.next_down_jump_time = current_time + seconds_from_now
        print(f"🔧 調整下跳觸發時間: {seconds_from_now}秒後 (時間: {self.next_down_jump_time:.1f})")
    
    def reset_statistics(self):
        """重置統計數據"""
        self.check_count = 0
        self.down_jump_count = 0
        self.condition_failed_reasons = {}
        self.manager_start_time = time.time()
        print("🔄 隨機下跳統計數據已重置")
    
    def get_status(self):
        """獲取下跳狀態"""
        if not self.enabled:
            return "隨機下跳: 已禁用"
        
        current_time = time.time()
        
        if self.is_down_jumping:
            return "隨機下跳: 執行中..."
        
        time_until_next = self.next_down_jump_time - current_time
        if time_until_next > 0:
            return f"隨機下跳: 下次觸發 {time_until_next:.1f}秒後"
        else:
            return "隨機下跳: 等待條件滿足"
    
    def get_statistics(self):
        """獲取使用統計"""
        if not self.enabled:
            return "隨機下跳統計: 功能已禁用"
        
        uptime = time.time() - self.manager_start_time
        uptime_minutes = uptime / 60
        
        avg_per_minute = self.down_jump_count / uptime_minutes if uptime_minutes > 0 else 0
        success_rate = self.down_jump_count / max(1, self.check_count) * 100
        
        stats = [
            f"隨機下跳統計:",
            f"  運行時間: {uptime_minutes:.1f} 分鐘",
            f"  檢查次數: {self.check_count}",
            f"  總計執行: {self.down_jump_count} 次",
            f"  成功率: {success_rate:.2f}%",
            f"  平均頻率: {avg_per_minute:.1f} 次/分鐘"
        ]
        
        if self.last_down_jump_time > 0:
            time_since_last = time.time() - self.last_down_jump_time
            stats.append(f"  上次執行: {time_since_last:.1f}秒前")
        
        # 顯示失敗原因統計
        if self.condition_failed_reasons:
            stats.append("  失敗原因:")
            for reason, count in self.condition_failed_reasons.items():
                percentage = count / max(1, self.check_count) * 100
                stats.append(f"    {reason}: {count}次 ({percentage:.1f}%)")
        
        return "\n".join(stats)
    
    def reset_timer(self):
        """重置下跳計時器"""
        self.schedule_next_down_jump()
        print("🔄 下跳計時器已重置")
    
    def toggle_debug(self):
        """切換調試模式"""
        self.debug_down_jump = not self.debug_down_jump
        print(f"🔧 隨機下跳調試模式: {'開啟' if self.debug_down_jump else '關閉'}")
    
    def adjust_interval(self, min_interval=None, max_interval=None):
        """動態調整下跳間隔"""
        if min_interval is not None and min_interval > 0:
            old_min = self.min_interval
            self.min_interval = min_interval
            print(f"🔧 調整最小間隔: {old_min}s -> {min_interval}s")
        
        if max_interval is not None and max_interval > self.min_interval:
            old_max = self.max_interval
            self.max_interval = max_interval
            print(f"🔧 調整最大間隔: {old_max}s -> {max_interval}s")
        
        # 重新安排下次下跳時間
        self.schedule_next_down_jump()
    
    def adjust_execute_chance(self, new_chance):
        """動態調整執行機率"""
        if 0.0 <= new_chance <= 1.0:
            old_chance = self.execute_chance
            self.execute_chance = new_chance
            print(f"🔧 調整執行機率: {old_chance*100:.0f}% -> {new_chance*100:.0f}%")
            return True
        return False
    
    def get_time_until_next(self):
        """獲取距離下次下跳的時間"""
        if not self.enabled:
            return float('inf')
        
        return max(0, self.next_down_jump_time - time.time())
    
    def is_ready(self):
        """檢查是否準備執行下跳"""
        if not self.enabled:
            return False
        
        return time.time() >= self.next_down_jump_time and not self.is_down_jumping
    
    def validate_configuration(self):
        """驗證下跳配置"""
        if not self.enabled:
            return ["隨機下跳功能已禁用"]
        
        warnings = []
        
        # 檢查間隔設定
        if self.min_interval >= self.max_interval:
            warnings.append("警告: 最小間隔應小於最大間隔")
        
        if self.min_interval < 5.0:
            warnings.append(f"警告: 最小間隔過短 ({self.min_interval}s < 5.0s)")
        
        if self.max_interval > 300.0:
            warnings.append(f"警告: 最大間隔過長 ({self.max_interval}s > 300s)")
        
        # 檢查保持時間
        if self.hold_time < 0.1:
            warnings.append(f"警告: 按鍵保持時間過短 ({self.hold_time}s < 0.1s)")
        elif self.hold_time > 1.0:
            warnings.append(f"警告: 按鍵保持時間過長 ({self.hold_time}s > 1.0s)")
        
        # 檢查執行機率
        if not 0.0 <= self.execute_chance <= 1.0:
            warnings.append(f"警告: 執行機率不在有效範圍 [0.0, 1.0]: {self.execute_chance}")
        
        return warnings if warnings else ["配置驗證通過"]