"""
符文模式模組 - 處理符文檢測和解謎邏輯
"""
import time
import random
import pyautogui
import keyboard


class RuneMode:
    def __init__(self):
        self.is_active = False
        self.start_time = 0
        self.movement_direction = None
        self.manual_override = False
        self.manual_override_time = 0
        self.search_movement = None
        self.search_start_time = 0
        self.search_duration = 0
        self.is_searching = False

    def enter(self):
        self.is_active = True
        self.start_time = time.time()
        self.is_searching = False
        self.search_movement = None
        print("進入 rune 模式")

    def exit(self):
        self.is_active = False
        if self.movement_direction:
            pyautogui.keyUp(self.movement_direction)
            self.movement_direction = None
        if self.search_movement:
            pyautogui.keyUp(self.search_movement)
            self.search_movement = None
        self.is_searching = False
        print("退出 rune 模式")

    def start_random_search(self):
        if self.search_movement:
            pyautogui.keyUp(self.search_movement)
        
        directions = ['left', 'right']
        self.search_movement = random.choice(directions)
        self.search_duration = random.uniform(10.0, 20.0)
        self.search_start_time = time.time()
        self.is_searching = True
        
        pyautogui.keyDown(self.search_movement)
        print(f"開始隨機搜尋 rune_text.png：方向 {self.search_movement}，持續 {self.search_duration:.1f}秒")

    def update_search(self):
        if not self.is_searching:
            return False
            
        elapsed = time.time() - self.search_start_time
        if elapsed >= self.search_duration:
            if self.search_movement:
                pyautogui.keyUp(self.search_movement)
                self.search_movement = None
            self.is_searching = False
            print("搜尋時間到，準備下一次隨機搜尋")
            return True
        return False

    def handle_rune_symbol_recognition(self, screenshot, client_rect, direction_templates, direction_masks, client_width, client_height, change_templates, medal_template, rune_template):
        """改進的符號識別和驗證邏輯"""
        # 導入函數（避免循環導入）
        from core.utils import capture_screen, recognize_direction_symbols, execute_channel_change
        
        max_attempts = 2  # 最多嘗試2次
        
        for attempt in range(1, max_attempts + 1):
            print(f"=== 符號識別嘗試 {attempt}/{max_attempts} ===")
            
            # 第一步：識別符號
            success, direction_sequence = recognize_direction_symbols(
                screenshot, direction_templates, direction_masks, client_width, client_height
            )
            
            if not success:
                print(f"第 {attempt} 次符號識別失敗")
                if attempt >= max_attempts:
                    print("達到最大嘗試次數，符號識別失敗，按下 esc 鍵 2 次")
                    # 執行換頻道流程
                    execute_channel_change(client_rect, change_templates)
                    self.exit()
                    return False
                else:
                    print(f"等待後重試...")
                    time.sleep(1)
                    screenshot = capture_screen(client_rect)
                    if screenshot is None:
                        continue
                    continue
            
            # 第二步：輸入識別到的序列
            print(f"識別出的方向序列: {direction_sequence}")
            for i, direction in enumerate(direction_sequence, 1):
                pyautogui.keyUp('left')
                pyautogui.keyUp('right')
                pyautogui.keyUp('up')
                pyautogui.keyUp('down')
                print(f"輸入第 {i} 個方向鍵: {direction}")
                pyautogui.press(direction)
                time.sleep(2)  # 每個方向鍵間隔2秒
            
            print("方向序列輸入完成，等待2秒後驗證...")
            time.sleep(2)  # 等待輸入效果生效
            
            # 第三步：驗證是否成功（重新截圖並嘗試識別）
            print("=== 驗證輸入結果 ===")
            verification_screenshot = capture_screen(client_rect)
            if verification_screenshot is None:
                print("驗證截圖失敗，假設成功")
                self.exit()
                return True
            
            # 再次嘗試識別符號
            verify_success, verify_sequence = recognize_direction_symbols(
                verification_screenshot, direction_templates, direction_masks, 
                client_width, client_height
            )
            
            if not verify_success:
                # 識別不到符號 = 成功解除了符號界面
                print("✓ 驗證成功：無法識別到符號，表示 rune 已成功解除")
                self.exit()
                return True
            else:
                # 還能識別到符號 = 輸入失敗，需要重試
                print(f"✗ 驗證失敗：仍能識別到符號 {verify_sequence}，表示輸入錯誤")
                
                if attempt >= max_attempts:
                    print("達到最大嘗試次數，符號輸入失敗，按下 esc 鍵")

                    # 執行換頻道流程
                    execute_channel_change(client_rect, change_templates)
                    self.exit()
                    return False
                
                # 先按 ESC 清除當前狀態，然後重新嘗試
                print("按下 ESC 鍵清除當前符號界面狀態")
                pyautogui.press('esc')
                time.sleep(1)  # 等待界面重置
                
                # 重新對齊 rune_text 位置（使用原本的對齊邏輯）
                print("重新對齊 rune_text 位置...")
                alignment_attempts = 0
                max_alignment_attempts = 10
                aligned = False
                
                while not aligned and alignment_attempts < max_alignment_attempts:
                    alignment_attempts += 1
                    current_screenshot = capture_screen(client_rect)
                    if current_screenshot is None:
                        time.sleep(0.5)
                        continue
                    
                    # 重新檢測角色和 rune_text 位置
                    from core.utils import simple_find_medal
                    from config import MATCH_THRESHOLD
                    
                    medal_found, medal_loc, _ = simple_find_medal(current_screenshot, medal_template, MATCH_THRESHOLD)
                    rune_found, rune_loc, _ = simple_find_medal(current_screenshot, rune_template, MATCH_THRESHOLD)
                    
                    if medal_found and rune_found:
                        medal_center_x = medal_loc[0] + medal_template.shape[1] // 2
                        rune_center_x = rune_loc[0] + rune_template.shape[1] // 2
                        diff = rune_center_x - medal_center_x
                        
                        print(f"對齊檢查: X軸差異 {diff}px")
                        
                        if abs(diff) < 10:
                            print("已對齊 rune_text")
                            aligned = True
                            break
                        else:
                            # 使用原本的對齊邏輯
                            direction = 'left' if diff < 0 else 'right'
                            print(f"朝 {direction} 移動以對齊 rune_text.png")
                            pyautogui.keyDown(direction)
                            time.sleep(0.2)  # 與原本邏輯一致的移動時間
                            pyautogui.keyUp(direction)
                            time.sleep(0.1)
                    else:
                        print(f"對齊嘗試 {alignment_attempts}: 未找到角色或 rune_text")
                        time.sleep(0.5)
                
                if not aligned:
                    print("⚠ 無法重新對齊，但繼續嘗試觸發符號界面")
                
                # 重新觸發符號界面
                print("重新觸發符號界面（按上鍵）")
                pyautogui.press('up')
                time.sleep(1)  # 等待界面出現
                
                # 重新截圖準備下次嘗試
                print(f"準備第 {attempt + 1} 次嘗試...")
                screenshot = capture_screen(client_rect)
                if screenshot is None:
                    print("重新截圖失敗，跳過此次重試")
                    continue
                
                # 繼續下次循環嘗試
                continue
        
        return False

    def handle(self, screenshot, client_rect, medal_template, rune_template, direction_templates, direction_masks, client_width, client_height, search, cliff_detection, client_x, client_y, movement, change_templates):
        # 導入函數和配置（避免循環導入）
        from core.utils import capture_screen, simple_find_medal, execute_channel_change
        from config import MATCH_THRESHOLD, Y_OFFSET, RUNE_HEIGHT_THRESHOLD
        
        if time.time() - self.start_time > 200:
            print("在 Rune 模式下超過200秒未找到 rune_text，執行 esc")
            # 執行換頻道流程
            execute_channel_change(client_rect, change_templates)
            self.exit()
            return

        if self.manual_override and time.time() - self.manual_override_time < 2:
            print("檢測到手動操作，暫停自動移動")
            return

        medal_found, medal_loc, medal_val = simple_find_medal(screenshot, medal_template, MATCH_THRESHOLD)
        print(f"角色檢測匹配度: {medal_val:.2f} (閾值: {MATCH_THRESHOLD})")
        
        if not medal_found:
            search_found, search_loc, search_screenshot = search.search_for_medal(client_rect, medal_template, MATCH_THRESHOLD, movement)
            if search_found:
                medal_found = True
                medal_loc = search_loc
                screenshot = search_screenshot

        if medal_found:
            player_x = medal_loc[0] + medal_template.shape[1] // 2
            player_y = medal_loc[1] + medal_template.shape[0] // 2 - Y_OFFSET
            
            rune_found, rune_loc, rune_val = simple_find_medal(screenshot, rune_template, MATCH_THRESHOLD)
            print(f"rune_text.png 匹配度: {rune_val:.2f} (閾值: {MATCH_THRESHOLD})")
            
            if rune_found:
                if self.is_searching:
                    if self.search_movement:
                        pyautogui.keyUp(self.search_movement)
                        self.search_movement = None
                    self.is_searching = False
                    print("找到 rune_text，停止搜尋")
                
                medal_center_x = medal_loc[0] + medal_template.shape[1] // 2
                rune_center_x = rune_loc[0] + rune_template.shape[1] // 2
                diff = rune_center_x - medal_center_x

                if abs(diff) < 10:
                    rune_center_y = rune_loc[1] + rune_template.shape[0] // 2
                    height_diff = abs(rune_center_y - player_y)
                    
                    if height_diff > RUNE_HEIGHT_THRESHOLD:
                        print(f"rune_text 高度差異 {height_diff} 超過閾值 {RUNE_HEIGHT_THRESHOLD}，觸發 esc")
                        # 執行換頻道流程
                        execute_channel_change(client_rect, change_templates)
                        self.exit()
                        return
                    
                    print("與 rune_text.png 對齊，執行上鍵並開始符號識別流程")
                    pyautogui.press('up')
                    time.sleep(1)
                    screenshot = capture_screen(client_rect)
                    if screenshot is not None:
                        # 使用新的符號識別邏輯
                        success = self.handle_rune_symbol_recognition(
                            screenshot, client_rect, direction_templates, direction_masks, 
                            client_width, client_height, change_templates, medal_template, rune_template
                        )
                        # 無論成功或失敗，都會在函數內處理，這裡直接返回
                        return
                else:
                    direction = 'left' if diff < 0 else 'right'
                    
                    if self.movement_direction != direction:
                        if self.movement_direction:
                            pyautogui.keyUp(self.movement_direction)
                        pyautogui.keyDown(direction)
                        self.movement_direction = direction
                        print(f"朝 {direction} 移動以對齊 rune_text.png")
                        
                        if keyboard.is_pressed('left') or keyboard.is_pressed('right'):
                            self.manual_override = True
                            self.manual_override_time = time.time()
                            print("檢測到手動移動，設定 manual_override")

                    cliff_detection.check(time.time(), screenshot, player_x, player_y, client_width, client_height, medal_template, self.movement_direction, client_x, client_y)
            else:
                if self.movement_direction:
                    pyautogui.keyUp(self.movement_direction)
                    self.movement_direction = None
                
                if self.is_searching:
                    if self.search_movement:
                        cliff_detection.check(time.time(), screenshot, player_x, player_y, client_width, client_height, medal_template, self.search_movement, client_x, client_y)
                    
                    if self.update_search():
                        time.sleep(random.uniform(0.2, 0.8))
                        self.start_random_search()
                else:
                    print("未找到 rune_text.png，開始隨機搜尋")
                    self.start_random_search()