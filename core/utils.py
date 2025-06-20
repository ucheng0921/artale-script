"""
工具模組 - 修復版攻擊函數，避免停頓問題 (增強版：支援可配置攻擊按鍵)
"""
import cv2
import numpy as np
import pyautogui
import time
import random
from config import JUMP_KEY


def capture_screen(client_rect):
    """截取螢幕指定區域"""
    try:
        screenshot_pil = pyautogui.screenshot(region=client_rect)
        screenshot = cv2.cvtColor(np.array(screenshot_pil), cv2.COLOR_RGB2BGR)
        return screenshot
    except Exception as e:
        print(f"截圖錯誤: {e}")
        return None

def preprocess_screenshot(screenshot):
    """預處理截圖 - 高斯模糊和邊緣檢測"""
    blurred = cv2.GaussianBlur(screenshot, (1, 1), 0)
    edges = cv2.Canny(blurred, 50, 150)
    return edges

def simple_find_medal(screenshot, template, threshold):
    """簡單的模板匹配函數 - 修改版（只搜索下半畫面）"""
    
    # ★★★ 關鍵修改：只搜索下半畫面 ★★★
    height = screenshot.shape[0]
    half_height = height // 2
    
    # 裁剪為下半畫面
    lower_half = screenshot[half_height:, :]
    
    # 在下半畫面進行模板匹配
    result = cv2.matchTemplate(lower_half, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    found = max_val >= threshold
    
    if found:
        # ★★★ 重要：調整座標到完整畫面的位置 ★★★
        actual_loc = (max_loc[0], max_loc[1] + half_height)
        return found, actual_loc, max_val
    else:
        return found, max_loc, max_val

def detect_sign_text(screenshot, sign_template, threshold=0.5):
    """檢測sign_text在螢幕上方區域"""
    upper_height = int(screenshot.shape[0] * 0.5)
    upper_region = screenshot[0:upper_height, :]
    result = cv2.matchTemplate(upper_region, sign_template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val >= threshold, max_loc, max_val

def get_attack_key():
    """★★★ 新增：獲取攻擊按鍵（支援主要/次要攻擊按鍵選擇）★★★"""
    try:
        from config import (
            ATTACK_KEY, SECONDARY_ATTACK_KEY, ENABLE_SECONDARY_ATTACK,
            PRIMARY_ATTACK_CHANCE, SECONDARY_ATTACK_CHANCE
        )
        
        # 如果沒有啟用次要攻擊，直接返回主要攻擊按鍵
        if not ENABLE_SECONDARY_ATTACK:
            return ATTACK_KEY
        
        # 根據機率選擇攻擊按鍵
        random_value = random.random()
        if random_value < PRIMARY_ATTACK_CHANCE:
            return ATTACK_KEY
        else:
            return SECONDARY_ATTACK_KEY
            
    except ImportError:
        # 如果配置載入失敗，使用預設值
        return ATTACK_KEY

def execute_attack_key(attack_key=None):
    """★★★ 新增：執行攻擊按鍵按壓 ★★★"""
    if attack_key is None:
        attack_key = get_attack_key()
    
    try:
        pyautogui.keyDown(attack_key)
        pyautogui.keyUp(attack_key)
        return True
    except Exception as e:
        print(f"❌ 攻擊按鍵 {attack_key} 執行失敗: {e}")
        return False

def sync_movement_state(movement, direction, movement_type, keys_pressed=None):
    """★★★ 同步所有移動狀態，避免不一致 ★★★"""
    movement.direction = direction
    movement.current_movement_type = movement_type
    movement.is_moving = True
    movement.start_time = time.time()
    movement.duration = random.uniform(3.0, 8.0)
    
    # ★★★ 修復：實際按下按鍵，而不只是設置列表 ★★★
    if keys_pressed and hasattr(movement, 'enhanced_movement'):
        # 先清理當前按鍵
        movement.enhanced_movement.release_all_keys()
        # 實際按下需要的按鍵
        for key in keys_pressed:
            pyautogui.keyDown(key)
        # 更新列表
        movement.enhanced_movement.current_keys_pressed = keys_pressed.copy()
    
    print(f"✅ 狀態同步: {direction}({movement_type}), 按鍵: {keys_pressed}")

def attack_with_key_preservation(attack_type, preserved_keys=None):
    """執行攻擊但保持指定按鍵不變 - 增強版（支援可配置攻擊按鍵）"""
    if attack_type == 'jump':
        from config import JUMP_ATTACK_MODE, DASH_SKILL_KEY
        
        if JUMP_ATTACK_MODE == 'mage':
            print(f"🧙‍♂️ 法師跳躍攻擊")
            pyautogui.keyDown('up')
            pyautogui.keyDown(DASH_SKILL_KEY)
            time.sleep(0.1)
            pyautogui.keyUp('up')
            pyautogui.keyUp(DASH_SKILL_KEY)
            time.sleep(0.05)
            # ★★★ 使用可配置的攻擊按鍵 ★★★
            attack_key = get_attack_key()
            execute_attack_key(attack_key)
            
        elif JUMP_ATTACK_MODE == 'original':
            print(f"⚔️ 跳躍攻擊")
            pyautogui.keyDown(JUMP_KEY)
            time.sleep(0.1)
            # ★★★ 使用可配置的攻擊按鍵 ★★★
            attack_key = get_attack_key()
            execute_attack_key(attack_key)
            pyautogui.keyUp(JUMP_KEY)
    else:
        # ★★★ 普通攻擊也使用可配置的攻擊按鍵 ★★★
        attack_key = get_attack_key()
        execute_attack_key(attack_key)
    
    # preserved_keys 保持按住不變
    print(f"攻擊完成，保持按鍵: {preserved_keys}")

def smart_direction_switch(movement, old_direction, new_direction):
    """智能方向切換，最小化按鍵中斷"""
    if old_direction == new_direction:
        return  # 無需切換
    
    print(f"🔄 智能方向切換: {old_direction} -> {new_direction}")
    
    # 安全釋放舊方向
    if old_direction and hasattr(movement, 'enhanced_movement'):
        if old_direction in movement.enhanced_movement.current_keys_pressed:
            pyautogui.keyUp(old_direction)
            movement.enhanced_movement.current_keys_pressed.remove(old_direction)
    
    # 按下新方向
    if new_direction:
        pyautogui.keyDown(new_direction)
        if hasattr(movement, 'enhanced_movement'):
            if new_direction not in movement.enhanced_movement.current_keys_pressed:
                movement.enhanced_movement.current_keys_pressed.append(new_direction)

def maintain_movement_type(movement, target_type, direction):
    """維持或恢復指定的移動類型"""
    if target_type == 'jump' and hasattr(movement, 'enhanced_movement'):
        if movement.enhanced_movement.can_jump():
            if JUMP_KEY not in movement.enhanced_movement.current_keys_pressed:
                pyautogui.keyDown(JUMP_KEY)
                movement.enhanced_movement.current_keys_pressed.append(JUMP_KEY)
            print("🦘 恢復跳躍移動")
            return True
        else:
            print("⚠️ 跳躍冷卻中，維持普通移動")
            return False
            
    elif target_type == 'dash' and hasattr(movement, 'enhanced_movement'):
        if movement.enhanced_movement.can_use_dash():
            from config import DASH_SKILL_KEY
            if DASH_SKILL_KEY not in movement.enhanced_movement.current_keys_pressed:
                pyautogui.keyDown(DASH_SKILL_KEY)
                movement.enhanced_movement.current_keys_pressed.append(DASH_SKILL_KEY)
            print("⚡ 恢復位移技能移動")
            return True
        else:
            print("⚠️ 位移技能冷卻中，維持普通移動")
            return False
    
    return target_type == 'normal'

def quick_attack_monster(monster_x, monster_y, player_x, player_y, movement, cliff_detection, attack_direction, attack_type):
    """★★★ 修復版智能攻擊函數 - 避免停頓 (增強版：支援可配置攻擊按鍵) ★★★"""
    # 獲取當前狀態
    current_direction = getattr(movement, 'direction', None)
    current_movement_type = getattr(movement, 'current_movement_type', 'normal')
    need_direction_change = current_direction != attack_direction
    
    # ★★★ 新增：顯示使用的攻擊按鍵 ★★★
    attack_key = get_attack_key()
    print(f"🎯 攻擊: {current_direction}({current_movement_type}) -> {attack_direction}({attack_type}) [按鍵: {attack_key}]")
    
    # ★★★ 關鍵修復：避免不必要的按鍵中斷 ★★★
    
    if current_movement_type == 'normal':
        # 情況1：普通移動攻擊
        if need_direction_change:
            print("普通移動 - 方向切換攻擊")
            smart_direction_switch(movement, current_direction, attack_direction)
            attack_with_key_preservation(attack_type, [attack_direction])
            sync_movement_state(movement, attack_direction, 'normal', [attack_direction])
        else:
            print("普通移動 - 同方向攻擊")
            attack_with_key_preservation(attack_type, [current_direction])
            # 不改變任何移動狀態
            
    elif current_movement_type == 'jump':
        # 情況2：跳躍移動攻擊
        if need_direction_change:
            print("跳躍移動 - 方向切換攻擊")
            # 先切換方向
            smart_direction_switch(movement, current_direction, attack_direction)
            # 攻擊
            attack_with_key_preservation(attack_type, [attack_direction])
            # ★★★ 關鍵：嘗試恢復跳躍移動，而不是強制降級 ★★★
            if maintain_movement_type(movement, 'jump', attack_direction):
                sync_movement_state(movement, attack_direction, 'jump', [attack_direction, JUMP_KEY])
            else:
                sync_movement_state(movement, attack_direction, 'normal', [attack_direction])
        else:
            print("跳躍移動 - 同方向攻擊")
            # 暫停跳躍進行攻擊
            current_keys = movement.enhanced_movement.current_keys_pressed.copy()
            if JUMP_KEY in current_keys:
                pyautogui.keyUp(JUMP_KEY)
                current_keys.remove(JUMP_KEY)
            
            attack_with_key_preservation(attack_type, current_keys)
            
            # 立即恢復跳躍
            if maintain_movement_type(movement, 'jump', current_direction):
                movement.enhanced_movement.current_keys_pressed = [current_direction, JUMP_KEY]
                print("🦘 攻擊後立即恢復跳躍")
            
    elif current_movement_type == 'dash':
        # 情況3：位移技能移動攻擊
        if need_direction_change:
            print("位移技能移動 - 方向切換攻擊")
            smart_direction_switch(movement, current_direction, attack_direction)
            attack_with_key_preservation(attack_type, [attack_direction])
            # 嘗試恢復位移技能移動
            if maintain_movement_type(movement, 'dash', attack_direction):
                from config import DASH_SKILL_KEY
                sync_movement_state(movement, attack_direction, 'dash', [attack_direction, DASH_SKILL_KEY])
            else:
                sync_movement_state(movement, attack_direction, 'normal', [attack_direction])
        else:
            print("位移技能移動 - 同方向攻擊")
            # 暫停位移技能進行攻擊
            from config import DASH_SKILL_KEY
            current_keys = movement.enhanced_movement.current_keys_pressed.copy()
            if DASH_SKILL_KEY in current_keys:
                pyautogui.keyUp(DASH_SKILL_KEY)
                current_keys.remove(DASH_SKILL_KEY)
            
            attack_with_key_preservation(attack_type, current_keys)
            
            # 立即恢復位移技能
            if maintain_movement_type(movement, 'dash', current_direction):
                #movement.enhanced_movement.current_keys_pressed = [current_direction, DASH_SKILL_KEY]
                print("⚡ 攻擊後立即恢復位移技能")
    
    # 重置斷層檢測狀態
    cliff_detection.prev_screenshot = None
    cliff_detection.last_check_time = time.time()
    
    print(f"✅ 攻擊完成: {movement.direction}({movement.current_movement_type})")
    time.sleep(0.1) # 攻擊斷點

def attack_monster_with_category(monster_x, monster_y, player_x, player_y, movement, cliff_detection, monster_category):
    """★★★ 修復版分類攻擊函數 ★★★"""
    # 導入配置（避免循環導入）
    from config import JUMP_ATTACK_MODE
    
    direction = 'left' if monster_x < player_x else 'right'
    y_diff = abs(monster_y - player_y)
    y_tolerance = monster_category['y_tolerance']
    monster_type = monster_category['type']
    jump_strategy = monster_category['jump_strategy']
    
    # 判斷怪物是否在角色上方
    monster_above = monster_y < player_y
    
    print(f"攻擊{monster_type}怪物: Y差異={y_diff}, 閾值={y_tolerance}, 位置={'上方' if monster_above else '下方或同高'}")
    
    # 決定攻擊類型
    attack_type = 'normal'
    if JUMP_ATTACK_MODE != 'disabled' and monster_above:
        should_jump_attack = False
        if jump_strategy == "conservative":
            should_jump_attack = y_diff > y_tolerance
        elif jump_strategy == "balanced":
            should_jump_attack = y_diff > y_tolerance
        elif jump_strategy == "selective":
            should_jump_attack = y_diff > y_tolerance and y_diff > 50
            
        if should_jump_attack:
            attack_type = 'jump'
    
    # 使用修復版攻擊函數
    quick_attack_monster(monster_x, monster_y, player_x, player_y, movement, cliff_detection, direction, attack_type)

def recognize_direction_symbols(screenshot, direction_templates, direction_masks, client_width, client_height, threshold=0.4):
    """識別方向符號"""
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    symbol_region_width = 700
    symbol_region_height = 130
    symbol_region_x = (client_width - symbol_region_width) // 2
    symbol_region_y = (client_height - symbol_region_height) // 2
    symbol_region_x = max(0, symbol_region_x)
    symbol_region_y = max(0, symbol_region_y)
    symbol_region_x_end = min(client_width, symbol_region_x + symbol_region_width)
    symbol_region_y_end = min(client_height, symbol_region_y + symbol_region_height)

    symbol_region = screenshot[symbol_region_y:symbol_region_y_end, symbol_region_x:symbol_region_x_end]
    symbol_region_gray = screenshot_gray[symbol_region_y:symbol_region_y_end, symbol_region_x:symbol_region_x_end]

    symbol_width = symbol_region_width // 4
    symbols = []
    for i in range(4):
        symbol_x_start = i * symbol_width
        symbol_x_end = min((i + 1) * symbol_width, symbol_region_width)
        symbol_img = symbol_region[:, symbol_x_start:symbol_x_end]
        symbol_img_gray = symbol_region_gray[:, symbol_x_start:symbol_x_end]

        if symbol_img.size == 0:
            print(f"第 {i+1} 個符號區域為空，無法識別")
            return False, []

        best_val = 0
        best_template = None
        for template_name, template in direction_templates.items():
            mask = direction_masks[template_name]
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            if (template_gray.shape[0] <= symbol_img_gray.shape[0] and 
                template_gray.shape[1] <= symbol_img_gray.shape[1] and 
                mask.shape[0] <= symbol_img_gray.shape[0] and 
                mask.shape[1] <= symbol_img_gray.shape[1]):
                result = cv2.matchTemplate(symbol_img_gray, template_gray, cv2.TM_CCOEFF_NORMED, mask=mask)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                if max_val > best_val:
                    best_val = max_val
                    best_template = template_name
        
        if best_val >= threshold:
            direction = best_template.split('_')[0]
            if direction == 'u':
                symbols.append('up')
            elif direction == 'd':
                symbols.append('down')
            elif direction == 'l':
                symbols.append('left')
            elif direction == 'r':
                symbols.append('right')
        else:
            print(f"無法識別第 {i+1} 個符號，匹配度 {best_val:.2f} 低於閾值 {threshold}")
            return False, []
    
    return True, symbols

def execute_channel_change(client_rect, change_templates):
    """執行換頻道流程 - 處理change0特殊情況"""
    print("開始執行換頻道流程...")
    
    # 定義換頻道順序
    change_order = ['change0', 'change1', 'change2', 'change3', 'change4', 'change5']
    
    for i, change_name in enumerate(change_order, 1):
        if change_name not in change_templates:
            print(f"警告: 找不到 {change_name}.png 模板，跳過此步驟")
            continue
            
        template = change_templates[change_name]
        print(f"步驟 {i}: 處理 {change_name}.png")
        
        # 第一階段：等待圖片出現
        found = False
        search_attempts = 0
        max_search_attempts = 50  # 最多等待25秒讓圖片出現
        
        print(f"等待 {change_name}.png 出現...")
        while not found and search_attempts < max_search_attempts:
            search_attempts += 1
            screenshot = capture_screen(client_rect)
            
            if screenshot is not None:
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= 0.7:
                    found = True
                    print(f"✓ 找到 {change_name}.png (匹配度: {max_val:.3f})")
                else:
                    if search_attempts % 10 == 0:  # 每5秒報告一次
                        print(f"等待中... (嘗試 {search_attempts}, 最高匹配度: {max_val:.3f})")
                    time.sleep(0.5)
            else:
                print("截圖失敗，重試中...")
                time.sleep(0.3)
        
        if not found:
            print(f"✗ 超時未找到 {change_name}.png，跳過此步驟")
            continue
        
        # ★★★ 特殊處理：change0 的邏輯 ★★★
        if change_name == 'change0':
            print("特殊處理 change0：點擊後等待 change0_1 出現")
            
            # 點擊 change0
            template_h, template_w = template.shape[:2]
            click_x = client_rect[0] + max_loc[0] + template_w // 2
            click_y = client_rect[1] + max_loc[1] + template_h // 2
            
            print(f"點擊 change0，位置: ({click_x}, {click_y})")
            pyautogui.click(click_x, click_y)
            time.sleep(0.5)  # 等待界面響應
            
            # 等待 change0_1 出現（如果有的話）
            if 'change0_1' in change_templates:
                print("等待 change0_1 出現...")
                change0_1_template = change_templates['change0_1']
                change0_1_found = False
                wait_attempts = 0
                max_wait_attempts = 20  # 等待10秒
                
                while not change0_1_found and wait_attempts < max_wait_attempts:
                    wait_attempts += 1
                    screenshot = capture_screen(client_rect)
                    
                    if screenshot is not None:
                        result = cv2.matchTemplate(screenshot, change0_1_template, cv2.TM_CCOEFF_NORMED)
                        _, max_val, _, _ = cv2.minMaxLoc(result)
                        
                        if max_val >= 0.7:
                            change0_1_found = True
                            print(f"✓ change0_1 已出現 (匹配度: {max_val:.3f})")
                        else:
                            time.sleep(0.5)
                
                if not change0_1_found:
                    print("⚠ change0_1 未出現，但繼續下一步")
            else:
                print("未定義 change0_1 模板，跳過檢測")
                time.sleep(1)  # 給一點時間讓界面穩定
            
            # change0 處理完成，繼續下一個
            continue
        
        # ★★★ 正常處理：change1~change5 的消失機制 ★★★
        else:
            print(f"正常處理 {change_name}：點擊直到消失")
            
            click_attempts = 0
            max_click_attempts = 200  # 最多點擊20次
            image_disappeared = False
            
            print(f"開始點擊 {change_name}.png 直到消失...")
            
            while not image_disappeared and click_attempts < max_click_attempts:
                click_attempts += 1
                
                # 重新定位圖片位置（可能會移動）
                current_screenshot = capture_screen(client_rect)
                if current_screenshot is None:
                    print("截圖失敗，重試...")
                    time.sleep(0.2)
                    continue
                
                # 檢查圖片是否還存在
                result = cv2.matchTemplate(current_screenshot, template, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                if max_val < 0.6:  # 圖片消失了
                    image_disappeared = True
                    print(f"✓ {change_name}.png 已消失，點擊成功！")
                    break
                
                # 圖片還在，執行點擊
                template_h, template_w = template.shape[:2]
                click_x = client_rect[0] + max_loc[0] + template_w // 2
                click_y = client_rect[1] + max_loc[1] + template_h // 2
                
                print(f"第 {click_attempts} 次點擊 {change_name}.png，位置: ({click_x}, {click_y}), 匹配度: {max_val:.3f}")
                pyautogui.click(click_x, click_y)
                
                # 點擊後短暫等待界面響應
                time.sleep(0.3)
                
                # 檢查點擊後圖片是否立即消失
                immediate_check = capture_screen(client_rect)
                if immediate_check is not None:
                    immediate_result = cv2.matchTemplate(immediate_check, template, cv2.TM_CCOEFF_NORMED)
                    _, immediate_max_val, _, _ = cv2.minMaxLoc(immediate_result)
                    
                    if immediate_max_val < 0.6:
                        image_disappeared = True
                        print(f"✓ {change_name}.png 點擊後立即消失！")
                        break
            
            if not image_disappeared:
                print(f"⚠ {change_name}.png 經過 {max_click_attempts} 次點擊仍未消失，可能需要手動處理")
            
            # 步驟完成後稍微等待，讓下一個界面元素出現
            if image_disappeared:
                time.sleep(0.5)  # 給界面一點時間切換
    
    print("換頻道流程完成")

# ★★★ 新增：攻擊按鍵相關的工具函數 ★★★

def get_attack_key_info():
    """獲取攻擊按鍵配置信息"""
    try:
        from config import (
            ATTACK_KEY, SECONDARY_ATTACK_KEY, ENABLE_SECONDARY_ATTACK,
            PRIMARY_ATTACK_CHANCE, SECONDARY_ATTACK_CHANCE
        )
        
        info = {
            'primary_key': ATTACK_KEY,
            'secondary_key': SECONDARY_ATTACK_KEY,
            'secondary_enabled': ENABLE_SECONDARY_ATTACK,
            'primary_chance': PRIMARY_ATTACK_CHANCE,
            'secondary_chance': SECONDARY_ATTACK_CHANCE
        }
        
        return info
        
    except ImportError:
        return {
            'primary_key': 'z',
            'secondary_key': 'x',
            'secondary_enabled': False,
            'primary_chance': 1.0,
            'secondary_chance': 0.0
        }

def test_attack_keys():
    """測試攻擊按鍵配置"""
    info = get_attack_key_info()
    
    print("🧪 攻擊按鍵測試:")
    print(f"   主要攻擊按鍵: {info['primary_key']} ({info['primary_chance']*100:.0f}%)")
    
    if info['secondary_enabled']:
        print(f"   次要攻擊按鍵: {info['secondary_key']} ({info['secondary_chance']*100:.0f}%)")
        
        # 測試按鍵選擇機率
        test_count = 100
        primary_count = 0
        secondary_count = 0
        
        for _ in range(test_count):
            key = get_attack_key()
            if key == info['primary_key']:
                primary_count += 1
            elif key == info['secondary_key']:
                secondary_count += 1
        
        print(f"   測試結果 ({test_count}次):")
        print(f"     {info['primary_key']}: {primary_count}次 ({primary_count/test_count*100:.1f}%)")
        print(f"     {info['secondary_key']}: {secondary_count}次 ({secondary_count/test_count*100:.1f}%)")
    else:
        print(f"   次要攻擊按鍵: 已禁用")

def validate_attack_key_config():
    """驗證攻擊按鍵配置"""
    info = get_attack_key_info()
    warnings = []
    
    # 檢查機率總和
    if info['secondary_enabled']:
        total_chance = info['primary_chance'] + info['secondary_chance']
        if abs(total_chance - 1.0) > 0.01:
            warnings.append(f"警告: 攻擊按鍵機率總和不等於1.0 ({total_chance:.3f})")
    
    # 檢查按鍵是否相同
    if info['primary_key'] == info['secondary_key'] and info['secondary_enabled']:
        warnings.append("警告: 主要和次要攻擊按鍵相同")
    
    # 檢查機率範圍
    if not 0.0 <= info['primary_chance'] <= 1.0:
        warnings.append(f"警告: 主要攻擊機率超出範圍 [0.0, 1.0]: {info['primary_chance']}")
    
    if not 0.0 <= info['secondary_chance'] <= 1.0:
        warnings.append(f"警告: 次要攻擊機率超出範圍 [0.0, 1.0]: {info['secondary_chance']}")
    
    return warnings if warnings else ["攻擊按鍵配置驗證通過"]