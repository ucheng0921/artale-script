"""
移動模組 - 處理角色移動邏輯 (修復版 - 解決移動類型無法切換問題)
"""
import time
import random
from config import JUMP_KEY, ATTACK_KEY, DASH_SKILL_KEY

class Movement:
    def __init__(self):
        self.direction = None
        self.start_time = 0
        self.duration = 0
        self.is_moving = False
        self.preferred_direction = None
        self.last_scan_time = 0
        self.scan_cooldown = 5  # 增加掃描冷卻時間，減少頻率
        
        # 新增：增強移動相關屬性
        from core.enhanced_movement import EnhancedMovement
        self.enhanced_movement = EnhancedMovement()
        self.current_movement_type = 'normal'  # 當前移動類型
        
        # ★★★ 新增：移動類型切換控制 ★★★
        self.last_type_switch_time = 0  # 上次切換移動類型的時間
        self.min_type_switch_interval = 2.0  # 最小切換間隔（秒）

    def stop(self):
        """完全停止移動並清理所有按鍵狀態"""
        if self.is_moving:
            # 使用增強移動系統停止移動
            self.enhanced_movement.stop_movement(self.direction)
            self.is_moving = False
            self.direction = None
            self.current_movement_type = 'normal'
            print("停止移動")

    def start(self, screenshot, player_x, player_y, client_width, client_height, detector):
        """開始移動 - 修正版，避免按鍵衝突"""
        # ★★★ 關鍵修正：檢查並清理衝突的按鍵狀態 ★★★
        if self.is_moving:
            print(f"⚠️ 已在移動中 ({self.direction}, {self.current_movement_type})，先停止當前移動")
            self.stop()  # 完全停止當前移動，清理所有按鍵

        # 減少掃描時的輸出信息
        if time.time() - self.last_scan_time > self.scan_cooldown:
            direction, target_y = detector.scan_for_direction(screenshot, player_x, player_y, client_width, client_height, self)
            self.last_scan_time = time.time()
        else:
            direction, target_y = None, None
        
        if direction:
            self.preferred_direction = direction
            if target_y is not None:
                height_diff = abs(target_y - player_y)

        # 決定移動方向
        if self.preferred_direction:
            direction = self.preferred_direction
            self.preferred_direction = None
        else:
            options = ['left', 'right']
            direction = random.choice(options)

        # ★★★ 額外安全檢查：確保沒有相反方向的按鍵被按住 ★★★
        self._ensure_clean_movement_state(direction)

        # 決定移動類型和持續時間
        self.current_movement_type = self.enhanced_movement.determine_movement_type()
        duration = random.uniform(3.5, 10)
        
        # 執行增強移動
        self.direction = self.enhanced_movement.execute_movement(direction, self.current_movement_type, duration)
        self.start_time = time.time()
        self.duration = duration
        self.is_moving = True
        
        # ★★★ 重置切換計時器 ★★★
        self.last_type_switch_time = time.time()

        print(f"開始{self.enhanced_movement.get_movement_name(self.current_movement_type)}移動: {direction} ({duration:.1f}秒)")

    def transition(self, screenshot, player_x, player_y, client_width, client_height, detector):
        """移動轉換 - 修復版，解決移動類型無法切換的問題"""
        if not self.is_moving:
            return

        old_direction = self.direction
        old_movement_type = self.current_movement_type
        current_time = time.time()
        
        # 新增：檢查掃描冷卻
        if current_time - self.last_scan_time > self.scan_cooldown:
            direction, target_y = detector.scan_for_direction(screenshot, player_x, player_y, client_width, client_height, self)
            self.last_scan_time = current_time
        else:
            direction, target_y = None, None
            print("切換時跳過掃描（冷卻中）")
        
        if direction:
            self.preferred_direction = direction
            print(f"檢測到遠處怪物，設定偏好方向: {direction}")

        # 決定新的移動方向
        if self.preferred_direction:
            new_direction = self.preferred_direction
            self.preferred_direction = None
            print(f"切換到偏好方向: {new_direction}")
        else:
            options = ['left', 'right']
            new_direction = random.choice(options)
            print(f"未檢測到有效怪物，隨機選擇方向: {new_direction}")

        # ★★★ 關鍵修復：重新決定移動類型，不受舊類型影響 ★★★
        new_movement_type = self.enhanced_movement.determine_movement_type()
        duration = random.uniform(3.5, 7)

        # 檢查是否需要切換
        direction_changed = new_direction != old_direction
        movement_type_changed = new_movement_type != old_movement_type
        
        # ★★★ 新增：檢查是否達到最小切換間隔 ★★★
        time_since_last_switch = current_time - self.last_type_switch_time
        can_switch_type = time_since_last_switch >= self.min_type_switch_interval

        # ★★★ 修復核心邏輯：移除原來的錯誤判斷 ★★★
        # 原來的錯誤邏輯：
        # if not direction_changed and not movement_type_changed:
        #     return  # 這裡會阻止所有切換！
        
        # ★★★ 新的正確邏輯：分情況處理 ★★★
        if not direction_changed and not movement_type_changed:
            # 方向和移動類型都相同，延長移動時間（這是正確的）
            self.start_time = current_time
            self.duration = duration
            print(f"繼續{self.enhanced_movement.get_movement_name(new_movement_type)}移動: {new_direction} ({duration:.1f}秒)")
            return
        
        elif not direction_changed and movement_type_changed:
            # ★★★ 關鍵修復：只有移動類型變化時的處理 ★★★
            if can_switch_type:
                print(f"移動類型切換: {self.enhanced_movement.get_movement_name(old_movement_type)} -> {self.enhanced_movement.get_movement_name(new_movement_type)} (方向保持: {new_direction})")
                
                # 停止舊的移動類型，但保持方向
                self._switch_movement_type_only(old_movement_type, new_movement_type, new_direction)
                
                # 更新狀態
                self.current_movement_type = new_movement_type
                self.start_time = current_time
                self.duration = duration
                self.last_type_switch_time = current_time
                
                print(f"✅ 移動類型切換完成: {new_direction}({self.enhanced_movement.get_movement_name(new_movement_type)})")
                return
            else:
                # 切換間隔未到，保持當前狀態
                remaining_time = self.min_type_switch_interval - time_since_last_switch
                print(f"移動類型切換冷卻中，剩餘 {remaining_time:.1f} 秒")
                self.start_time = current_time
                self.duration = duration
                return
        
        elif direction_changed and not movement_type_changed:
            # 只有方向變化
            print(f"方向切換: {old_direction} -> {new_direction} (類型保持: {self.enhanced_movement.get_movement_name(new_movement_type)})")
        
        else:
            # 方向和移動類型都變化
            print(f"完全切換: {old_direction}({self.enhanced_movement.get_movement_name(old_movement_type)}) -> {new_direction}({self.enhanced_movement.get_movement_name(new_movement_type)})")

        # ★★★ 執行實際的切換操作 ★★★
        
        # 完全停止舊的移動，清理所有按鍵狀態
        self.enhanced_movement.stop_movement(old_direction)
        
        # 額外安全檢查：確保沒有衝突的按鍵狀態
        self._ensure_clean_movement_state(new_direction)
        
        # 開始新的移動
        self.direction = self.enhanced_movement.execute_movement(new_direction, new_movement_type, duration)
        self.current_movement_type = new_movement_type
        self.start_time = current_time
        self.duration = duration
        
        # 如果移動類型有變化，更新切換時間
        if movement_type_changed:
            self.last_type_switch_time = current_time

        print(f"✅ 移動切換完成: {new_direction}({self.enhanced_movement.get_movement_name(new_movement_type)}) ({duration:.1f}秒)")

    def _switch_movement_type_only(self, old_type, new_type, direction):
        """★★★ 新增：只切換移動類型，保持移動方向不變 ★★★"""
        import pyautogui
        
        print(f"🔄 執行移動類型切換: {old_type} -> {new_type}")
        
        # 首先移除舊移動類型的特殊按鍵
        if old_type == 'jump':
            if JUMP_KEY in self.enhanced_movement.current_keys_pressed:
                pyautogui.keyUp(JUMP_KEY)
                self.enhanced_movement.current_keys_pressed.remove(JUMP_KEY)
                print("🔓 釋放跳躍鍵: JUMP_KEY")
        
        elif old_type == 'dash':
            from config import DASH_SKILL_KEY
            if DASH_SKILL_KEY in self.enhanced_movement.current_keys_pressed:
                pyautogui.keyUp(DASH_SKILL_KEY)
                self.enhanced_movement.current_keys_pressed.remove(DASH_SKILL_KEY)
                print(f"🔓 釋放位移技能鍵: {DASH_SKILL_KEY}")
        
        # 確保方向鍵保持按住
        if direction not in self.enhanced_movement.current_keys_pressed:
            pyautogui.keyDown(direction)
            self.enhanced_movement.current_keys_pressed.append(direction)
            print(f"🔒 確保方向鍵按住: {direction}")
        
        # 添加新移動類型的特殊按鍵
        if new_type == 'jump' and self.enhanced_movement.can_jump():
            pyautogui.keyDown(JUMP_KEY)
            self.enhanced_movement.current_keys_pressed.append(JUMP_KEY)
            self.enhanced_movement.last_jump_time = time.time()
            print("🔒 添加跳躍鍵: JUMP_KEY")
        
        elif new_type == 'dash' and self.enhanced_movement.can_use_dash():
            from config import DASH_SKILL_KEY
            pyautogui.keyDown(DASH_SKILL_KEY)
            self.enhanced_movement.current_keys_pressed.append(DASH_SKILL_KEY)
            self.enhanced_movement.last_dash_time = time.time()
            print(f"🔒 添加位移技能鍵: {DASH_SKILL_KEY}")
        
        print(f"✅ 移動類型切換完成，當前按鍵: {self.enhanced_movement.current_keys_pressed}")

    def update(self):
        """更新移動狀態，檢查是否應該停止移動"""
        if self.is_moving:
            elapsed = time.time() - self.start_time
            
            # 在移動過程中持續更新增強移動狀態
            self.enhanced_movement.update_movement(self.current_movement_type)
            
            if elapsed >= self.duration:
                return True  # 移動時間到，需要停止
        return False  # 繼續移動

    def _ensure_clean_movement_state(self, target_direction):
        """確保乾淨的移動狀態，避免按鍵衝突"""
        import pyautogui
        
        # 定義所有可能的移動相關按鍵
        all_movement_keys = ['left', 'right', JUMP_KEY]
        try:
            from config import DASH_SKILL_KEY
            all_movement_keys.append(DASH_SKILL_KEY)
        except:
            all_movement_keys.append(DASH_SKILL_KEY)  # 預設值
        
        # 獲取相反方向
        opposite_direction = 'right' if target_direction == 'left' else 'left'
        
        print(f"🧹 清理移動狀態：目標方向 {target_direction}，檢查衝突按鍵...")
        
        # 檢查增強移動系統記錄的按鍵狀態
        if hasattr(self.enhanced_movement, 'current_keys_pressed'):
            conflicting_keys = []
            
            # 檢查是否有相反方向鍵被按住
            if opposite_direction in self.enhanced_movement.current_keys_pressed:
                conflicting_keys.append(opposite_direction)
            
            # 如果是跳躍模式，保護 JUMP_KEY 鍵不被釋放
            if self.current_movement_type == 'jump':
                print("🦘 跳躍模式中，保護 JUMP_KEY 鍵不被釋放")
                all_movement_keys.remove(JUMP_KEY)  # 移除 JUMP_KEY 鍵以避免釋放
            
            # 如果有衝突，先釋放衝突按鍵
            if conflicting_keys:
                print(f"⚠️ 發現衝突按鍵: {conflicting_keys}，執行選擇性清理")
                
                # 只釋放衝突的按鍵
                for key in conflicting_keys:
                    try:
                        pyautogui.keyUp(key)
                        self.enhanced_movement.remove_key_pressed(key)
                        print(f"🔓 釋放衝突按鍵: {key}")
                    except:
                        pass
                
                # 短暫等待確保按鍵狀態清理完成
                time.sleep(0.02)  # 縮短等待時間以減少延遲
                print("✅ 衝突按鍵清理完成")
            else:
                print("✅ 無按鍵衝突")
        
        # 額外保險：確保相反方向鍵被釋放
        try:
            pyautogui.keyUp(opposite_direction)
            self.enhanced_movement.remove_key_pressed(opposite_direction)
        except:
            pass

    def force_clean_all_keys(self):
        """★★★ 新增：強制清理所有移動相關按鍵（緊急使用）★★★"""
        import pyautogui
        
        print("🚨 執行強制按鍵清理...")
        
        # 所有可能的移動按鍵
        emergency_keys = ['left', 'right', 'up', 'down', JUMP_KEY, DASH_SKILL_KEY, ATTACK_KEY]
        
        for key in emergency_keys:
            try:
                pyautogui.keyUp(key)
            except:
                pass
        
        # 重置所有狀態
        self.enhanced_movement.current_keys_pressed = []
        self.is_moving = False
        self.direction = None
        self.current_movement_type = 'normal'
        
        print("🚨 強制清理完成")
    
    def get_movement_switch_cooldown_status(self):
        """★★★ 新增：獲取移動類型切換冷卻狀態 ★★★"""
        current_time = time.time()
        time_since_last_switch = current_time - self.last_type_switch_time
        
        if time_since_last_switch >= self.min_type_switch_interval:
            return True, 0
        else:
            remaining = self.min_type_switch_interval - time_since_last_switch
            return False, remaining
    
    def set_min_type_switch_interval(self, interval):
        """★★★ 新增：設置最小移動類型切換間隔 ★★★"""
        old_interval = self.min_type_switch_interval
        self.min_type_switch_interval = interval
        print(f"🔧 調整移動類型切換間隔: {old_interval}秒 -> {interval}秒")