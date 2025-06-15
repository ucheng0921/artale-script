"""
斷層檢測模組 - 檢測角色是否遇到斷層
"""
import time
import random
import cv2
import numpy as np
import pyautogui
from config import JUMP_KEY


class CliffDetection:
    def __init__(self):
        self.last_check_time = 0
        self.prev_screenshot = None
        self.threshold = 5

    def check(self, current_time, screenshot, player_x, player_y, client_width, client_height, medal_template, movement_direction, client_x, client_y):
        if current_time - self.last_check_time < 0.1:
            return

        self.last_check_time = current_time
        
        # 改為角色前方一小塊區域
        region_width = 50
        region_height = 30
        
        # 根據移動方向調整檢測位置到角色前方
        if movement_direction == 'left':
            # 檢測角色左前方
            region_x = client_x + player_x - region_width - 15
        elif movement_direction == 'right':
            # 檢測角色右前方  
            region_x = client_x + player_x + 15
        else:
            # 不移動時檢測角色正下方
            region_x = client_x + player_x - region_width // 2
        
        region_y = client_y + player_y + medal_template.shape[0] - 20
        region_x = max(client_x, min(region_x, client_x + client_width - region_width))
        region_y = max(client_y, min(region_y, client_y + client_height - region_height))
        
        try:
            current_screenshot = pyautogui.screenshot(region=(region_x, region_y, region_width, region_height))
            if current_screenshot is not None:
                current_screenshot = cv2.cvtColor(np.array(current_screenshot), cv2.COLOR_RGB2BGR)
                if self.prev_screenshot is not None:
                    diff = cv2.absdiff(self.prev_screenshot, current_screenshot)
                    mean_diff = cv2.mean(diff)[0]
                    
                    if mean_diff < 2.0 and movement_direction:
                        random_value = random.random()
                        
                        if random_value < 0.2:
                            action_choice = 1  # 反向移動
                        else:
                            action_choice = 2  # 跳躍
                        
                        # ★ 簡化斷層檢測輸出 ★
                        print(f"🔍 檢測到斷層! 執行{'反向移動' if action_choice == 1 else '跳躍'}")
                        
                        if action_choice == 1:
                            # 反方向移動邏輯保持不變...
                            reverse_direction = 'right' if movement_direction == 'left' else 'left'
                            reverse_duration = random.uniform(1.0, 1.5)
                            
                            pyautogui.keyUp(movement_direction)
                            pyautogui.keyDown(reverse_direction)
                            time.sleep(reverse_duration)
                            pyautogui.keyUp(reverse_direction)
                            pyautogui.keyDown(movement_direction)
                            
                        else:
                            # 跳躍邏輯保持不變...
                            pyautogui.keyUp(movement_direction)
                            pyautogui.keyDown(JUMP_KEY)
                            pyautogui.keyDown(movement_direction)
                            time.sleep(0.03)
                            pyautogui.keyUp(JUMP_KEY)
                            pyautogui.keyUp(movement_direction)
                            pyautogui.keyDown(movement_direction)
                            
                self.prev_screenshot = current_screenshot
            else:
                print("斷層檢測截圖失敗")
        except Exception as e:
            print(f"斷層檢測錯誤: {e}")