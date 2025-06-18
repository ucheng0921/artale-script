"""
搜尋模組 - 處理角色遺失時的搜尋邏輯 (改善版)
"""
import time
import random
import pyautogui
from config import JUMP_KEY

class Search:
    def __init__(self):
        self.is_searching = False
        self.search_start_time = 0
        self.last_medal_found_time = time.time()
        self.medal_lost_count = 0

    def search_for_medal(self, client_rect, medal_template, threshold, movement):
        """改善版搜尋 - 減少停頓感"""
        if self.is_searching:
            return False, None, None

        # 導入函數（避免循環導入）
        from core.utils import capture_screen, simple_find_medal

        self.is_searching = True
        self.search_start_time = time.time()

        print(f"角色遺失 {self.medal_lost_count} 次，開始搜尋...")
        
        # ★★★ 改善1：不強制停止移動，而是檢查當前移動狀態 ★★★
        current_direction = getattr(movement, 'direction', None)
        was_moving = getattr(movement, 'is_moving', False)
        
        # 如果正在移動，先嘗試在當前方向檢測
        if was_moving and current_direction:
            print(f"當前正在移動 {current_direction}，先在移動中檢測角色...")
            # 給移動中檢測一個短暫機會
            time.sleep(0.2)
            current_screenshot = capture_screen(client_rect)
            if current_screenshot is not None:
                found, loc, val = simple_find_medal(current_screenshot, medal_template, threshold)
                if found:
                    print(f"移動中找到角色 (匹配度 {val:.2f})，無需額外搜尋")
                    self.is_searching = False
                    self.last_medal_found_time = time.time()
                    self.medal_lost_count = 0
                    return True, loc, current_screenshot

        # ★★★ 改善2：智能搜尋順序 - 優先考慮當前移動方向的反方向 ★★★
        if current_direction:
            # 如果當前向右移動，優先搜尋左邊（可能錯過了）
            opposite_direction = 'left' if current_direction == 'right' else 'right'
            search_order = [opposite_direction, current_direction]
            print(f"智能搜尋順序: {search_order[0]} (反方向優先) → {search_order[1]} (當前方向)")
        else:
            # 隨機搜尋順序
            search_order = random.choice([
                ['left', 'right'],   
                ['right', 'left']    
            ])
            print(f"隨機搜尋順序: {search_order[0]} → {search_order[1]}")

        first_direction = search_order[0]
        second_direction = search_order[1]
        
        # ★★★ 改善3：縮短搜尋時間，增加檢測頻率 ★★★
        first_duration = random.uniform(0.6, 1.0)   # 原本 0.8-1.5，縮短為 0.6-1.0
        second_duration = random.uniform(0.6, 1.0)  # 原本 0.8-1.5，縮短為 0.6-1.0
        
        print(f"搜尋時間: {first_direction} ({first_duration:.1f}秒) → {second_direction} ({second_duration:.1f}秒)")

        # ★★★ 改善4：柔性停止 - 保留增強移動狀態信息 ★★★
        enhanced_movement_backup = None
        current_movement_type_backup = None
        
        if hasattr(movement, 'enhanced_movement') and hasattr(movement, 'current_movement_type'):
            enhanced_movement_backup = movement.enhanced_movement
            current_movement_type_backup = movement.current_movement_type
        
        # 執行柔性停止
        self._soft_stop_movement(movement)

        # ★★★ 改善5：分段搜尋 - 中途檢測 ★★★
        found_result = self._segmented_search(
            client_rect, medal_template, threshold, 
            first_direction, first_duration, 
            second_direction, second_duration
        )

        if found_result[0]:  # 找到角色
            found, loc, screenshot, found_direction, match_val = found_result  # ★★★ 修復：解包5個值 ★★★
            print(f"向{found_direction}移動後找到角色 (匹配度 {match_val:.2f})")
            
            # ★★★ 改善6：立即恢復流暢移動 ★★★
            self._immediate_resume_movement(
                movement, found_direction, 
                enhanced_movement_backup, current_movement_type_backup
            )
            
            self.is_searching = False
            self.last_medal_found_time = time.time()
            self.medal_lost_count = 0
            return True, loc, screenshot

        print("搜尋完成，未找到角色")
        
        # ★★★ 改善7：搜尋失敗後的智能恢復 ★★★
        self._smart_recovery_after_search_failure(
            movement, current_direction, 
            enhanced_movement_backup, current_movement_type_backup
        )
        
        self.is_searching = False
        self.medal_lost_count = 0
        return False, None, None

    def _soft_stop_movement(self, movement):
        """柔性停止移動 - 不完全清除狀態"""
        print("🔄 執行柔性停止移動...")
        
        if hasattr(movement, 'enhanced_movement'):
            # 只釋放按鍵，但保留狀態信息
            movement.enhanced_movement.release_all_keys()
        
        # 標記為非移動狀態，但保留方向信息
        movement.is_moving = False
        # 注意：不清除 movement.direction，保留用於恢復

    def _segmented_search(self, client_rect, medal_template, threshold, 
                         first_direction, first_duration, 
                         second_direction, second_duration):
        """分段搜尋 - 中途檢測角色"""
        from core.utils import capture_screen, simple_find_medal
        import pyautogui
        
        # ★★★ 本地安全按鍵函數 ★★★
        def safe_keyDown(key):
            if key is not None and isinstance(key, str) and len(key) > 0:
                pyautogui.keyDown(key)
            else:
                print(f"⚠️ 跳過無效的 keyDown: {key}")
        
        def safe_keyUp(key):
            if key is not None and isinstance(key, str) and len(key) > 0:
                pyautogui.keyUp(key)
            else:
                print(f"⚠️ 跳過無效的 keyUp: {key}")
        
        # 第一個方向的分段搜尋
        print(f"向{first_direction}搜尋角色...")
        
        safe_keyDown(first_direction)
        
        # 分段檢測：將搜尋時間分成2-3段
        segments = max(2, int(first_duration / 0.4))  # 每0.4秒檢測一次
        segment_time = first_duration / segments
        
        for i in range(segments):
            time.sleep(segment_time)
            
            # 中途檢測
            if i > 0:  # 第一段太短，跳過檢測
                current_screenshot = capture_screen(client_rect)
                if current_screenshot is not None:
                    found, loc, val = simple_find_medal(current_screenshot, medal_template, threshold)
                    if found:
                        safe_keyUp(first_direction)
                        print(f"在{first_direction}方向第{i+1}段找到角色 (匹配度 {val:.2f})")
                        return True, loc, current_screenshot, first_direction, val
        
        safe_keyUp(first_direction)
        
        # 第一方向結束後的最終檢測
        first_screenshot = capture_screen(client_rect)
        if first_screenshot is not None:
            found, loc, val = simple_find_medal(first_screenshot, medal_template, threshold)
            if found:
                print(f"向{first_direction}移動後找到角色 (匹配度 {val:.2f})")
                return True, loc, first_screenshot, first_direction, val

        # 第二個方向的分段搜尋
        print(f"向{second_direction}搜尋角色...")
        
        safe_keyDown(second_direction)
        
        segments = max(2, int(second_duration / 0.4))
        segment_time = second_duration / segments
        
        for i in range(segments):
            time.sleep(segment_time)
            
            # 中途檢測
            if i > 0:
                current_screenshot = capture_screen(client_rect)
                if current_screenshot is not None:
                    found, loc, val = simple_find_medal(current_screenshot, medal_template, threshold)
                    if found:
                        safe_keyUp(second_direction)
                        print(f"在{second_direction}方向第{i+1}段找到角色 (匹配度 {val:.2f})")
                        return True, loc, current_screenshot, second_direction, val
        
        safe_keyUp(second_direction)
        
        # 第二方向結束後的最終檢測
        second_screenshot = capture_screen(client_rect)
        if second_screenshot is not None:
            found, loc, val = simple_find_medal(second_screenshot, medal_template, threshold)
            if found:
                print(f"向{second_direction}移動後找到角色 (匹配度 {val:.2f})")
                return True, loc, second_screenshot, second_direction, val

        return False, None, None, None, 0.0

    def _immediate_resume_movement(self, movement, found_direction, 
                                 enhanced_movement_backup, current_movement_type_backup):
        """立即恢復流暢移動 - 減少停頓"""
        import pyautogui
        
        # ★★★ 本地安全按鍵函數 ★★★
        def safe_keyDown(key):
            if key is not None and isinstance(key, str) and len(key) > 0:
                pyautogui.keyDown(key)
            else:
                print(f"⚠️ 跳過無效的 keyDown: {key}")
        
        print(f"🚀 立即恢復{found_direction}方向移動...")
        
        # 設定移動方向和偏好
        movement.preferred_direction = found_direction
        movement.direction = found_direction
        
        # ★★★ 關鍵改善：立即開始移動，不等待下一個循環 ★★★
        if enhanced_movement_backup and current_movement_type_backup:
            # 嘗試恢復原來的移動類型
            try:
                if current_movement_type_backup == 'normal':
                    safe_keyDown(found_direction)
                    enhanced_movement_backup.current_keys_pressed = [found_direction]
                    movement.current_movement_type = 'normal'
                elif current_movement_type_backup == 'jump' and enhanced_movement_backup.can_jump():
                    safe_keyDown(found_direction)
                    safe_keyDown(JUMP_KEY)
                    enhanced_movement_backup.current_keys_pressed = [found_direction, JUMP_KEY]
                    movement.current_movement_type = 'jump'
                    enhanced_movement_backup.last_jump_time = time.time()
                elif current_movement_type_backup == 'dash' and enhanced_movement_backup.can_use_dash():
                    from config import DASH_SKILL_KEY
                    safe_keyDown(found_direction)
                    safe_keyDown(DASH_SKILL_KEY)
                    enhanced_movement_backup.current_keys_pressed = [found_direction, DASH_SKILL_KEY]
                    movement.current_movement_type = 'dash'
                    enhanced_movement_backup.last_dash_time = time.time()
                else:
                    # 降級為普通移動
                    safe_keyDown(found_direction)
                    enhanced_movement_backup.current_keys_pressed = [found_direction]
                    movement.current_movement_type = 'normal'
                
                movement.is_moving = True
                movement.start_time = time.time()
                movement.duration = random.uniform(3.0, 8.0)  # 設定移動持續時間
                
                print(f"✅ 恢復為{movement.current_movement_type}移動模式")
                
            except Exception as e:
                print(f"⚠️ 恢復移動模式失敗，使用普通移動: {e}")
                safe_keyDown(found_direction)
                movement.current_movement_type = 'normal'
                movement.is_moving = True
        else:
            # 備用方案：簡單的普通移動
            safe_keyDown(found_direction)
            movement.current_movement_type = 'normal'
            movement.is_moving = True
            movement.start_time = time.time()
            movement.duration = random.uniform(3.0, 8.0)

    def _smart_recovery_after_search_failure(self, movement, original_direction, 
                                           enhanced_movement_backup, current_movement_type_backup):
        """搜尋失敗後的智能恢復"""
        import pyautogui
        
        # ★★★ 本地安全按鍵函數 ★★★
        def safe_keyDown(key):
            if key is not None and isinstance(key, str) and len(key) > 0:
                pyautogui.keyDown(key)
            else:
                print(f"⚠️ 跳過無效的 keyDown: {key}")
        
        print("🔄 搜尋失敗，執行智能恢復...")
        
        # 如果原本有移動方向，嘗試恢復
        if original_direction and enhanced_movement_backup:
            try:
                recovery_direction = original_direction
                print(f"嘗試恢復原始移動方向: {recovery_direction}")
                
                # 恢復為普通移動（最安全）
                safe_keyDown(recovery_direction)
                enhanced_movement_backup.current_keys_pressed = [recovery_direction]
                movement.direction = recovery_direction
                movement.current_movement_type = 'normal'
                movement.is_moving = True
                movement.start_time = time.time()
                movement.duration = random.uniform(2.0, 5.0)
                
                print(f"✅ 恢復普通移動: {recovery_direction}")
                
            except Exception as e:
                print(f"⚠️ 智能恢復失敗: {e}")
        else:
            print("⚠️ 無法智能恢復，將在下次循環中重新開始移動")