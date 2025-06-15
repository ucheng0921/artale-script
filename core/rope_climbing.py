"""
爬繩模組 - 處理繩索檢測和爬繩邏輯 (修復版 - 實時更新繩索位置)
"""
import cv2
import os
import glob
import time
import random
import pyautogui
from config import JUMP_KEY, DASH_SKILL_KEY, ATTACK_KEY

class RopeClimbing:
    def __init__(self):
        self.is_climbing = False
        self.rope_templates = []
        self.detection_size = 200
        self.min_distance = 60
        self.max_distance = 70
        self.max_attempts = 2
        self.current_attempt = 0
        self.climbing_phase = "detecting"
        self.target_rope_x = None
        self.target_rope_y = None
        self.last_foot_area = None
        self.movement_direction = None
        self.approaching_start_time = 0
        self.max_approaching_time = 2
        
        # ★★★ 新增：繩索位置更新相關 ★★★
        self.last_rope_update_time = 0
        self.rope_update_interval = 0.5  # 每0.5秒更新一次繩索位置
        self.rope_detection_size_for_update = 200  # 更新時使用較小的檢測範圍
        
        # ★★★ 修復：初始化為0，讓程式啟動時就能爬繩 ★★★
        self.last_climb_time = 0
        
        # ★★★ 新增：調試標誌 ★★★
        self.debug_rope_detection = True
        
        # ★★★ 新增：最長爬繩時間限制 ★★★
        self.max_climbing_duration = 15.0  # 最長爬繩時間 15 秒
        self.climbing_start_time = 0  # 開始爬繩的時間

    def can_climb(self):
        """檢查是否可以爬繩（冷卻檢查）- 修復版"""
        from config import ROPE_COOLDOWN_TIME
        current_time = time.time()
        
        # ★★★ 修復：簡化冷卻檢查邏輯 ★★★
        if ROPE_COOLDOWN_TIME <= 0:
            # 如果冷卻時間設為0或負數，總是允許爬繩
            if self.debug_rope_detection:
                print(f"🔧 [調試] 冷卻時間為 {ROPE_COOLDOWN_TIME}，允許爬繩")
            return True
        
        time_since_last_climb = current_time - self.last_climb_time
        if time_since_last_climb < ROPE_COOLDOWN_TIME:
            remaining = ROPE_COOLDOWN_TIME - time_since_last_climb
            if self.debug_rope_detection:
                print(f"🕒 [調試] 爬繩冷卻中，剩餘 {remaining:.1f} 秒")
            return False
        
        if self.debug_rope_detection:
            print(f"✅ [調試] 冷卻完成，可以爬繩 (上次爬繩: {time_since_last_climb:.1f} 秒前)")
        return True
    
    def load_rope_templates(self, rope_folder):
        """載入繩索模板"""
        self.rope_templates = []
        
        if not os.path.exists(rope_folder):
            print(f"警告: 繩索資料夾不存在: {rope_folder}")
            return
            
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']
        for ext in image_extensions:
            for file_path in glob.glob(os.path.join(rope_folder, ext)):
                template = cv2.imread(file_path, cv2.IMREAD_COLOR)
                if template is not None:
                    self.rope_templates.append(template)
                    print(f"載入繩索模板: {os.path.basename(file_path)}")
                else:
                    print(f"警告: 無法載入 {file_path}")
        
        if not self.rope_templates:
            print(f"警告: 未找到任何繩索模板")
        else:
            print(f"成功載入 {len(self.rope_templates)} 個繩索模板")
    
    def detect_rope(self, screenshot, player_x, player_y, client_width, client_height):
        """檢測繩索位置（修復版）"""
        if not self.rope_templates:
            if self.debug_rope_detection:
                print("🔧 [調試] 無繩索模板，跳過檢測")
            return False, None, None
        
        # ★★★ 修復：使用簡化的冷卻檢查 ★★★
        if not self.can_climb():
            return False, None, None
        
        if self.debug_rope_detection:
            print(f"🔧 [調試] 開始繩索檢測，角色位置: ({player_x}, {player_y})")
        
        return self._detect_rope_internal(screenshot, player_x, player_y, client_width, client_height, self.detection_size)
    
    def _detect_rope_internal(self, screenshot, player_x, player_y, client_width, client_height, detection_size):
        """內部繩索檢測函數"""
        region_x = max(0, min(player_x - detection_size // 2, client_width - detection_size))
        region_y = max(0, min(player_y - detection_size, client_height - detection_size))
        
        region_x_end = min(region_x + detection_size, client_width)
        region_y_end = min(region_y + detection_size, client_height)
        
        detection_region = screenshot[region_y:region_y_end, region_x:region_x_end]
        
        if detection_region.size == 0:
            if self.debug_rope_detection:
                print("🔧 [調試] 檢測區域為空")
            return False, None, None
        
        best_val = 0
        best_rope_x = None
        best_rope_y = None
        
        for i, template in enumerate(self.rope_templates, 1):
            template_h, template_w = template.shape[:2]
            if template_h > detection_region.shape[0] or template_w > detection_region.shape[1]:
                continue
            
            try:
                result = cv2.matchTemplate(detection_region, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                threshold = 0.75
                if max_val > threshold and max_val > best_val:
                    best_val = max_val
                    best_rope_x = region_x + max_loc[0] + template_w // 2
                    best_rope_y = region_y + max_loc[1] + template_h // 2
                    
                    if self.debug_rope_detection:
                        print(f"🔧 [調試] 繩索模板 {i} 匹配度: {max_val:.3f}")
                        
            except cv2.error as e:
                continue
        
        if best_rope_x is not None:
            return True, best_rope_x, best_rope_y
        else:
            if self.debug_rope_detection:
                print("🔧 [調試] 未檢測到繩索")
            return False, None, None
    
    def update_rope_position(self, screenshot, player_x, player_y, client_width, client_height):
        """★★★ 新增：實時更新繩索位置 ★★★"""
        current_time = time.time()
        
        # 檢查是否需要更新
        if current_time - self.last_rope_update_time < self.rope_update_interval:
            return False
        
        self.last_rope_update_time = current_time
        
        if self.debug_rope_detection:
            print(f"🔄 更新繩索位置檢測...")
        
        # 使用較小的檢測範圍進行更新（提高效率）
        rope_found, new_rope_x, new_rope_y = self._detect_rope_internal(
            screenshot, player_x, player_y, client_width, client_height, 
            self.rope_detection_size_for_update
        )
        
        if rope_found:
            # 計算位置變化
            old_x, old_y = self.target_rope_x or 0, self.target_rope_y or 0
            x_change = abs(new_rope_x - old_x) if self.target_rope_x else 0
            y_change = abs(new_rope_y - old_y) if self.target_rope_y else 0
            
            # 更新目標位置
            self.target_rope_x = new_rope_x
            self.target_rope_y = new_rope_y
            
            if self.debug_rope_detection:
                print(f"✅ 繩索位置已更新: ({new_rope_x}, {new_rope_y})")
                if x_change > 0 or y_change > 0:
                    print(f"   位置變化: X軸 {x_change}px, Y軸 {y_change}px")
            
            return True
        else:
            if self.debug_rope_detection:
                print("⚠️ 無法更新繩索位置，使用舊位置繼續")
            return False
    
    def capture_head_area(self, screenshot, player_x, player_y, client_width, client_height, medal_template):
        """截取角色頭上區域（避免腳下怪物干擾）"""
        try:
            region_width = 40
            region_height = 50
            region_x = max(0, min(player_x - region_width // 2, client_width - region_width))
            region_y = max(0, min(player_y - 20, client_height - region_height))
            
            region_x_end = min(region_x + region_width, client_width)
            region_y_end = min(region_y + region_height, client_height)
            
            head_area = screenshot[region_y:region_y_end, region_x:region_x_end]
            return head_area
        except Exception as e:
            print(f"截取頭上區域錯誤: {e}")
            return None

    def capture_foot_area(self, screenshot, player_x, player_y, client_width, client_height, medal_template):
        """截取角色腳下區域（用於到達頂層檢測）"""
        try:
            region_width = 100
            region_height = 60
            region_x = max(0, min(player_x - region_width // 2, client_width - region_width))
            region_y = max(0, min(player_y + medal_template.shape[0], client_height - region_height))
            
            region_x_end = min(region_x + region_width, client_width)
            region_y_end = min(region_y + region_height, client_height)
            
            foot_area = screenshot[region_y:region_y_end, region_x:region_x_end]
            return foot_area
        except Exception as e:
            print(f"截取腳下區域錯誤: {e}")
            return None
    
    def is_in_climbing_range(self, rope_x, player_x):
        """判斷是否在可爬繩範圍內"""
        x_diff = abs(rope_x - player_x)
        
        if x_diff < self.min_distance:
            print(f"❌ 太靠近繩索: X差異 {x_diff}px < 最小距離 {self.min_distance}px")
            return False
        elif x_diff > self.max_distance:
            print(f"❌ 距離繩索太遠: X差異 {x_diff}px > 最大距離 {self.max_distance}px")
            return False
        else:
            print(f"✅ 在可爬繩範圍內: X差異 {x_diff}px (範圍: {self.min_distance}-{self.max_distance}px)")
            return True
    
    def start_climbing(self, rope_x, rope_y, player_x, player_y):
        """開始爬繩流程（修復版）"""
        from config import ROPE_COOLDOWN_TIME
        print("🧗 === 開始爬繩邏輯 ===")
        
        # ★★★ 新增：強制停止當前所有移動，確保爬繩對齊精確性 ★★★
        self.force_stop_all_movement()
        
        # ★★★ 修復：只有在冷卻時間大於0時才記錄時間 ★★★
        if ROPE_COOLDOWN_TIME > 0:
            self.last_climb_time = time.time()
            print(f"設置爬繩冷卻：{ROPE_COOLDOWN_TIME} 秒")
        else:
            print("爬繩冷卻已關閉，不設置冷卻時間")
        
        self.is_climbing = True
        self.climbing_phase = "approaching"
        self.current_attempt = 1
        self.target_rope_x = rope_x
        self.target_rope_y = rope_y
        self.last_foot_area = None
        self.movement_direction = None
        self.approaching_start_time = time.time()
        
        # ★★★ 新增：記錄開始爬繩的時間 ★★★
        self.climbing_start_time = time.time()
        
        # ★★★ 新增：重置繩索位置更新計時器 ★★★
        self.last_rope_update_time = time.time()
        
        print(f"目標繩索位置: ({rope_x}, {rope_y})")
        print(f"角色位置: ({player_x}, {player_y})")
        print(f"開始第 {self.current_attempt}/{self.max_attempts} 次嘗試")
        print(f"最長爬繩時間: {self.max_climbing_duration} 秒")
        
        return True
    
    def force_stop_all_movement(self):
        """★★★ 新增：強制停止所有移動，為爬繩做準備 ★★★"""
        print("🚨 爬繩模式：強制停止所有移動")
        
        # 停止當前爬繩相關的移動
        self.stop_movement()
        
        # ★★★ 關鍵：強制釋放所有可能影響爬繩的按鍵 ★★★
        problem_keys = ['left', 'right', JUMP_KEY, DASH_SKILL_KEY, ATTACK_KEY, 'up', 'down']
        for key in problem_keys:
            try:
                pyautogui.keyUp(key)
                print(f"🚨 爬繩準備：釋放 {key}")
            except:
                pass
        
        # 短暫等待，確保按鍵狀態穩定
        time.sleep(0.1)
        print("✅ 爬繩準備：所有移動已停止")
    
    def start_movement(self, direction):
        """開始移動"""
        if self.movement_direction != direction:
            if self.movement_direction:
                pyautogui.keyUp(self.movement_direction)
            pyautogui.keyDown(direction)
            self.movement_direction = direction
            print(f"🔄 開始朝 {direction} 移動")
    
    def stop_movement(self):
        """停止移動"""
        if self.movement_direction:
            pyautogui.keyUp(self.movement_direction)
            print(f"🛑 停止 {self.movement_direction} 移動")
            self.movement_direction = None
    
    def check_climbing_timeout(self):
        """★★★ 新增：檢查爬繩是否超時 ★★★"""
        if not self.is_climbing or self.climbing_start_time == 0:
            return False
        
        current_time = time.time()
        elapsed_time = current_time - self.climbing_start_time
        
        if elapsed_time >= self.max_climbing_duration:
            print(f"⏰ 爬繩超時！已經過 {elapsed_time:.1f} 秒 (最大: {self.max_climbing_duration} 秒)")
            print("🦘 執行超時跳躍動作後停止爬繩")
            self.perform_exit_jump()
            self.stop_climbing()
            return True
        
        return False
    
    def execute_climb_attempt(self, player_x, screenshot, player_y, client_width, client_height, medal_template):
        """執行爬繩嘗試"""
        print(f"🎪 === 執行第 {self.current_attempt} 次爬繩嘗試 ===")
        
        # 先停止當前移動
        self.stop_movement()
        
        rope_on_left = self.target_rope_x < player_x
        direction = 'left' if rope_on_left else 'right'
        
        print(f"繩索在角色{direction}邊，執行 {direction}+跳+上")
        print(f"🚀 執行動作序列: {direction} + JUMP_KEY + up")
        
        # 執行爬繩動作
        pyautogui.keyDown(direction)
        pyautogui.keyDown(JUMP_KEY)
        pyautogui.keyUp(direction)
        pyautogui.keyUp(JUMP_KEY)
        pyautogui.keyDown('up')  # 按下 up 鍵並保持
        time.sleep(0.1)  # 動作保持 0.1 秒
        pyautogui.keyUp('up')
        
        # 短暫等待讓動作生效
        time.sleep(0.5)
        
        # 驗證爬繩成功
        self.verify_climb_success(screenshot, player_x, player_y, client_width, client_height, medal_template)
    
    def verify_climb_success(self, screenshot, player_x, player_y, client_width, client_height, medal_template):
        """通過攻擊驗證爬繩成功"""
        print("🔍 === 驗證爬繩成功 ===")
        
        # 獲取當前截圖和角色位置
        current_screenshot = self.get_current_screenshot()
        if current_screenshot is None:
            print("❌ 獲取驗證截圖失敗")
            pyautogui.keyUp('up')
            self.retry_climb()
            return
        
        # 重新檢測角色位置
        medal_template_ref = self.get_medal_template()
        if medal_template_ref is not None:
            result = cv2.matchTemplate(current_screenshot, medal_template_ref, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.6:
                template_height, template_width = medal_template_ref.shape[:2]
                current_player_x = max_loc[0] + template_width // 2
                current_player_y = max_loc[1] + template_height // 2 - 50
                
                print(f"📍 檢測到角色位置: ({current_player_x}, {current_player_y})")
                
                # 截取攻擊前的頭上區域
                print("📸 截取攻擊前的頭上區域...")
                before_attack_head_area = self.capture_head_area(
                    current_screenshot, current_player_x, current_player_y, 
                    client_width, client_height, medal_template_ref
                )
                
                if before_attack_head_area is None:
                    print("❌ 截取攻擊前頭上區域失敗")
                    pyautogui.keyUp('up')
                    self.retry_climb()
                    return
                
                print(f"✅ 已截取攻擊前頭上區域: {before_attack_head_area.shape}")
                
                # 執行攻擊驗證
                print("🗡️ 執行攻擊驗證")
                pyautogui.keyDown(ATTACK_KEY)
                time.sleep(0.1)
                pyautogui.keyUp(ATTACK_KEY)
                
                # 短暫等待攻擊動畫完成
                time.sleep(0.1)
                
                # 獲取攻擊後的截圖
                after_attack_screenshot = self.get_current_screenshot()
                if after_attack_screenshot is None:
                    print("❌ 獲取攻擊後截圖失敗")
                    pyautogui.keyUp('up')
                    self.retry_climb()
                    return
                
                # 重新檢測攻擊後的角色位置
                result_after = cv2.matchTemplate(after_attack_screenshot, medal_template_ref, cv2.TM_CCOEFF_NORMED)
                _, max_val_after, _, max_loc_after = cv2.minMaxLoc(result_after)
                
                if max_val_after >= 0.6:
                    after_player_x = max_loc_after[0] + template_width // 2
                    after_player_y = max_loc_after[1] + template_height // 2 - 50
                    
                    print(f"📍 攻擊後角色位置: ({after_player_x}, {after_player_y})")
                    
                    # 截取攻擊後的頭上區域
                    after_attack_head_area = self.capture_head_area(
                        after_attack_screenshot, after_player_x, after_player_y, 
                        client_width, client_height, medal_template_ref
                    )
                    
                    if after_attack_head_area is not None and before_attack_head_area.shape == after_attack_head_area.shape:
                        # 比較攻擊前後的頭上區域差異
                        diff = cv2.absdiff(before_attack_head_area, after_attack_head_area)
                        mean_diff = cv2.mean(diff)[0]
                        
                        print(f"📊 頭上區域攻擊檢測:")
                        print(f"   攻擊前後差異: {mean_diff:.2f}")
                        print(f"   檢測閾值: 25.0")
                        
                        if mean_diff < 25.0:
                            print("👍 頭上區域無明顯變化，成功上繩!")
                            print("   攻擊時角色沒有移動，表示已固定在繩索上")
                            pyautogui.keyDown('up')
                            self.start_going_up()
                            return True
                        else:
                            print("❌ 頭上區域有明顯變化，爬繩失敗")
                            print("   攻擊時角色發生移動，表示未成功上繩")
                            print(f"   角色攻擊前位置: ({current_player_x}, {current_player_y})")
                            print(f"   角色攻擊後位置: ({after_player_x}, {after_player_y})")
                            
                            # ★★★ 新增：爬繩失敗時執行隨機跳躍動作 ★★★
                            print("🦘 爬繩失敗，執行隨機方向跳躍動作")
                            self.perform_exit_jump()
                            
                    else:
                        print("⚠️ 前後截圖尺寸不一致或截取失敗，無法比較")
                        if before_attack_head_area is not None and after_attack_head_area is not None:
                            print(f"   攻擊前: {before_attack_head_area.shape}")
                            print(f"   攻擊後: {after_attack_head_area.shape}")
                        
                        # ★★★ 新增：截圖比較失敗時也執行隨機跳躍動作 ★★★
                        print("🦘 截圖比較失敗，執行隨機方向跳躍動作")
                        self.perform_exit_jump()
                        
                else:
                    print("❌ 攻擊後未找到角色")
                    # ★★★ 新增：找不到角色時也執行隨機跳躍動作 ★★★
                    print("🦘 攻擊後找不到角色，執行隨機方向跳躍動作")
                    self.perform_exit_jump()
                    
            else:
                print("❌ 驗證時未找到角色")
                # ★★★ 新增：驗證時找不到角色也執行隨機跳躍動作 ★★★
                print("🦘 驗證時找不到角色，執行隨機方向跳躍動作")
                self.perform_exit_jump()
        
        pyautogui.keyUp('up')
        self.retry_climb()
    
    def retry_climb(self):
        """重新嘗試爬繩"""
        if self.current_attempt < self.max_attempts:
            self.current_attempt += 1
            print(f"🔄 準備第 {self.current_attempt}/{self.max_attempts} 次嘗試")
            self.climbing_phase = "approaching"
            self.approaching_start_time = time.time()
        else:
            print(f"❌ 已達最大嘗試次數 ({self.max_attempts})，放棄爬繩")
            # ★★★ 新增：達到最大嘗試次數時也執行隨機跳躍動作 ★★★
            print("🦘 達到最大嘗試次數，執行隨機方向跳躍動作後停止爬繩")
            self.perform_exit_jump()
            self.stop_climbing()
    
    def start_going_up(self):
        """開始向上爬"""
        print("⬆️ === 階段: 持續向上爬 ===")
        self.climbing_phase = "going_up"
        print("開始持續按住上鍵向上爬...")
    
    def check_reach_top(self, screenshot, player_x, player_y, client_width, client_height, medal_template):
        """檢查是否到達頂層（使用連續檢測機制）"""
        current_foot_area = self.capture_foot_area(screenshot, player_x, player_y, client_width, client_height, medal_template)
        
        if self.last_foot_area is not None and current_foot_area is not None:
            if current_foot_area.shape == self.last_foot_area.shape:
                diff = cv2.absdiff(self.last_foot_area, current_foot_area)
                mean_diff = cv2.mean(diff)[0]
                
                # 初始化連續檢測計數器
                if not hasattr(self, 'low_change_count'):
                    self.low_change_count = 0
                
                print(f"檢查頂層: 腳下區域變化 {mean_diff:.2f}")
                
                if mean_diff < 4.0:  # 保持原來的閾值 4.0
                    self.low_change_count += 1
                    print(f"變化小於閾值，連續次數: {self.low_change_count}/2")
                    
                    # 需要連續 3 次都小於閾值才算到達頂層
                    if self.low_change_count >= 2:
                        print("🏆 到達頂層！連續2次腳下區域變化都很小")
                        pyautogui.keyUp('up')
                        self.climbing_phase = "finished"
                        self.stop_climbing()
                        return True
                else:
                    # 只要有一次變化大，就重置計數器
                    if self.low_change_count > 0:
                        print(f"變化較大 ({mean_diff:.2f})，重置計數器")
                    self.low_change_count = 0
        
        self.last_foot_area = current_foot_area
        return False
    
    def perform_exit_jump(self):
        """執行結束跳躍動作：隨機方向鍵+跳"""
        print("🦘 === 執行隨機方向跳躍動作 ===")
        
        # 確保先停止所有移動和爬繩相關按鍵
        self.stop_movement()
        pyautogui.keyUp('up')
        pyautogui.keyUp(JUMP_KEY)
        
        # 隨機選擇左或右
        random_direction = random.choice(['left', 'right'])
        print(f"選擇隨機方向: {random_direction}")
        
        # 執行方向鍵+跳躍
        print(f"執行動作: {random_direction} + JUMP_KEY")
        pyautogui.keyDown(random_direction)
        pyautogui.keyDown(JUMP_KEY)
        time.sleep(0.1)  # 保持0.1秒
        pyautogui.keyUp(JUMP_KEY)
        pyautogui.keyUp(random_direction)
        
        print("✅ 隨機方向跳躍動作完成")
    
    def update_climbing(self, screenshot, player_x, player_y, client_width, client_height, medal_template, client_x, client_y):
        """更新爬繩狀態 - 修復版，加入實時繩索位置更新和超時檢查"""
        if not self.is_climbing:
            return
        
        # ★★★ 新增：檢查爬繩超時 ★★★
        if self.check_climbing_timeout():
            return
        
        if self.climbing_phase == "approaching":
            # ★★★ 關鍵修復：在接近階段實時更新繩索位置 ★★★
            self.update_rope_position(screenshot, player_x, player_y, client_width, client_height)
            
            # 檢查是否超時
            if time.time() - self.approaching_start_time > self.max_approaching_time:
                print(f"⏰ 接近繩索超時 ({self.max_approaching_time}秒)，放棄此次嘗試")
                self.retry_climb()
                return
            
            # ★★★ 現在使用實時更新的繩索位置進行距離檢查 ★★★
            if self.target_rope_x is None:
                print("⚠️ 繩索位置遺失，重新檢測...")
                rope_found, new_rope_x, new_rope_y = self.detect_rope(screenshot, player_x, player_y, client_width, client_height)
                if rope_found:
                    self.target_rope_x = new_rope_x
                    self.target_rope_y = new_rope_y
                    print(f"✅ 重新獲得繩索位置: ({new_rope_x}, {new_rope_y})")
                else:
                    print("❌ 無法重新檢測到繩索，放棄此次嘗試")
                    self.retry_climb()
                    return
            
            # 檢查距離狀態
            x_diff = abs(self.target_rope_x - player_x)
            
            if self.is_in_climbing_range(self.target_rope_x, player_x):
                print("✅ 到達爬繩範圍，開始執行爬繩動作")
                self.climbing_phase = "executing"
                self.execute_climb_attempt(player_x, screenshot, player_y, client_width, client_height, medal_template)
            elif x_diff < self.min_distance:
                if self.target_rope_x < player_x:
                    required_direction = 'right'
                else:
                    required_direction = 'left'
                
                if self.movement_direction != required_direction:
                    print(f"太靠近繩索，遠離方向移動: {required_direction}，X差異: {x_diff}px")
                    self.start_movement(required_direction)
            elif x_diff > self.max_distance:
                if self.target_rope_x > player_x:
                    required_direction = 'right'
                else:
                    required_direction = 'left'
                
                if self.movement_direction != required_direction:
                    print(f"距離繩索太遠，靠近方向移動: {required_direction}，X差異: {x_diff}px")
                    self.start_movement(required_direction)
                
        elif self.climbing_phase == "executing":
            pass
            
        elif self.climbing_phase == "going_up":
            self.check_reach_top(screenshot, player_x, player_y, client_width, client_height, medal_template)
    
    def stop_climbing(self):
        """★★★ 修復版：停止爬繩邏輯，不重置冷卻時間 ★★★"""
        print("🏁 === 爬繩邏輯結束 ===")
        
        self.stop_movement()
        pyautogui.keyUp('up')
        pyautogui.keyUp(JUMP_KEY)
        
        self.is_climbing = False
        self.climbing_phase = "detecting"
        self.current_attempt = 0
        self.target_rope_x = None
        self.target_rope_y = None
        self.last_foot_area = None
        self.movement_direction = None
        self.approaching_start_time = 0
        
        # ★★★ 重置繩索位置更新相關狀態 ★★★
        self.last_rope_update_time = 0
        
        # ★★★ 重置爬繩計時相關狀態 ★★★
        self.climbing_start_time = 0
        
        if hasattr(self, 'low_change_count'):
            self.low_change_count = 0

        # ★★★ 關鍵修復：不重置 last_climb_time，讓冷卻機制正常運作 ★★★
        # self.last_climb_time = 0  # 移除這行，保持冷卻時間
        
        # ★★★ 新增：結束後執行跳躍動作確保脫離繩索 ★★★
        print("🦘 執行結束跳躍動作，確保脫離繩索")
        random_direction = random.choice(['left', 'right'])
        print(f"執行動作: {random_direction} + JUMP_KEY")
        pyautogui.keyDown(random_direction)
        pyautogui.keyDown(JUMP_KEY)
        time.sleep(0.1)  # 保持0.1秒
        pyautogui.keyUp(JUMP_KEY)
        pyautogui.keyUp(random_direction)
        
        print("爬繩邏輯已重置，冷卻時間保持")
        

    def reset_climb_cooldown(self):
        """★★★ 新增：手動重置爬繩冷卻（僅供調試使用）★★★"""
        self.last_climb_time = 0
        print("🔄 手動重置爬繩冷卻時間")

    def get_climb_cooldown_status(self):
        """★★★ 修復版：獲取爬繩冷卻狀態 ★★★"""
        from config import ROPE_COOLDOWN_TIME
        current_time = time.time()
        
        # ★★★ 特殊處理：如果冷卻時間為0或負數，總是允許爬繩 ★★★
        if ROPE_COOLDOWN_TIME <= 0:
            return True, 0
        
        # ★★★ 特殊處理：如果 last_climb_time 是初始值，直接允許爬繩 ★★★
        if self.last_climb_time <= 0:
            return True, 0
        
        if current_time - self.last_climb_time < ROPE_COOLDOWN_TIME:
            remaining = ROPE_COOLDOWN_TIME - (current_time - self.last_climb_time)
            return False, remaining
        return True, 0
    
    def set_screenshot_callback(self, screenshot_func):
        """設定截圖回調函數"""
        self.screenshot_func = screenshot_func
    
    def set_medal_template(self, medal_template):
        """設定角色模板"""
        self.medal_template = medal_template
    
    def get_current_screenshot(self):
        """獲取當前截圖"""
        if hasattr(self, 'screenshot_func'):
            return self.screenshot_func()
        return None
    
    def get_medal_template(self):
        """獲取角色模板"""
        if hasattr(self, 'medal_template'):
            return self.medal_template
        return None
    
    # ★★★ 新增：調試方法 ★★★
    def toggle_debug(self):
        """切換調試模式"""
        self.debug_rope_detection = not self.debug_rope_detection
        print(f"🔧 繩索檢測調試模式: {'開啟' if self.debug_rope_detection else '關閉'}")
    
    def force_enable_rope_detection(self):
        """強制啟用繩索檢測（忽略冷卻）"""
        print("🚨 強制重置繩索檢測冷卻")
        self.last_climb_time = 0
        self.is_climbing = False
        print("✅ 強制重置完成，下次檢測將立即生效")
    
    # ★★★ 新增：調整繩索檢測範圍的方法 ★★★
    def adjust_climbing_range(self, min_distance=None, max_distance=None):
        """調整爬繩距離範圍"""
        if min_distance is not None:
            old_min = self.min_distance
            self.min_distance = min_distance
            print(f"🔧 調整最小距離: {old_min}px -> {min_distance}px")
        
        if max_distance is not None:
            old_max = self.max_distance
            self.max_distance = max_distance
            print(f"🔧 調整最大距離: {old_max}px -> {max_distance}px")
        
        print(f"當前爬繩範圍: {self.min_distance}-{self.max_distance}px")
    
    def get_current_rope_info(self, player_x, player_y):
        """★★★ 新增：獲取當前繩索資訊（用於調試）★★★"""
        if self.target_rope_x is None or self.target_rope_y is None:
            return "無繩索目標"
        
        x_diff = abs(self.target_rope_x - player_x)
        status = ""
        
        if x_diff < self.min_distance:
            status = "太靠近"
        elif x_diff > self.max_distance:
            status = "太遠"
        else:
            status = "範圍內"
        
        return f"繩索位置: ({self.target_rope_x}, {self.target_rope_y}), 角色位置: ({player_x}, {player_y}), X差異: {x_diff}px, 狀態: {status}"
    
    # ★★★ 新增：爬繩時間相關方法 ★★★
    def set_max_climbing_duration(self, duration):
        """設定最長爬繩時間"""
        old_duration = self.max_climbing_duration
        self.max_climbing_duration = duration
        print(f"🔧 調整最長爬繩時間: {old_duration}秒 -> {duration}秒")
    
    def get_climbing_duration_info(self):
        """獲取爬繩時間資訊"""
        if not self.is_climbing or self.climbing_start_time == 0:
            return "未在爬繩中"
        
        current_time = time.time()
        elapsed_time = current_time - self.climbing_start_time
        remaining_time = self.max_climbing_duration - elapsed_time
        
        return f"已爬繩時間: {elapsed_time:.1f}秒, 剩餘時間: {remaining_time:.1f}秒 (最大: {self.max_climbing_duration}秒)"