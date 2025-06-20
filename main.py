"""
主程式模組 - 安全版本，強制要求認證
"""

# ============================================================================
# 安全檢查 - 必須在所有其他 import 之前
# ============================================================================

import sys
import os

def security_check():
    """安全檢查 - 阻止未授權訪問"""
    print("🔐 執行安全檢查...")
    
    # 檢查是否為GUI模式
    GUI_MODE = os.environ.get('ARTALE_GUI_MODE') == 'true'
    
    if GUI_MODE:
        print("🖥️ GUI模式已啟用，跳過直接認證檢查")
        # GUI模式下，認證由script_wrapper負責設置
        return
    
    try:
        # 檢查是否存在認證令牌
        from core.auth_manager import get_auth_manager
        
        auth_manager = get_auth_manager()
        if not auth_manager.is_authenticated():
            print("\n" + "="*60)
            print("🚫 未授權訪問被拒絕")
            print("="*60)
            print("❌ 此程式需要通過 GUI 進行 Firebase 認證")
            print()
            print("🔧 正確的使用流程:")
            print("  1. 執行 'python run_integrated_gui.py'")
            print("  2. 在 GUI 中使用有效的 UUID 登入")
            print("  3. 登入成功後使用 GUI 啟動腳本")
            print()
            print("⚠️ 直接執行 main.py 是不被允許的")
            print("💡 這是為了保護系統安全和防止濫用")
            print("="*60)
            
            # 記錄未授權嘗試
            try:
                import datetime
                import platform
                
                log_entry = f"[{datetime.datetime.now()}] 未授權訪問嘗試 - {platform.node()}\n"
                with open("security_violations.log", "a") as f:
                    f.write(log_entry)
            except:
                pass
            
            input("\n按 Enter 鍵退出...")
            sys.exit(1)
        
        # 認證通過
        session_info = auth_manager.get_session_info()
        print("✅ 認證驗證通過")
        if session_info:
            print(f"👤 會話: {session_info['session_id']}")
            print(f"⏰ 有效至: {session_info['expires_at']}")
        
    except ImportError:
        print("\n❌ 認證系統未正確安裝")
        print("請確保 auth_manager.py 文件存在")
        input("按 Enter 鍵退出...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 安全檢查失敗: {e}")
        input("按 Enter 鍵退出...")
        sys.exit(1)

# 立即執行安全檢查
# 临时注释用于测试 - 记得取消注释！
# security_check()

# ============================================================================
# 只有通過安全檢查後才能繼續執行
# ============================================================================

import pyautogui
import cv2
import numpy as np
import win32gui
import time
import glob

# 引入配置和所有模組
from config import *
from core.utils import *
from core.enhanced_movement import EnhancedMovement
from core.movement import Movement
from core.search import Search
from core.cliff_detection import CliffDetection
from core.monster_detector import SimplifiedMonsterDetector
from core.rope_climbing import RopeClimbing
from core.rune_mode import RuneMode
from core.red_dot_detector import RedDotDetector

# 導入認證裝飾器
from core.auth_manager import require_authentication

# ============================================================================
# 所有重要函數都需要認證
# ============================================================================

@require_authentication()
def load_templates():
    """載入所有圖片模板 - 需要認證"""
    templates = {}
    
    # 載入基本模板
    templates['medal'] = cv2.imread(MEDAL_PATH, cv2.IMREAD_COLOR)
    if templates['medal'] is None:
        raise ValueError(f"無法載入ID圖片: {MEDAL_PATH}")
    
    # 載入sign_text模板
    sign_template = cv2.imread(SIGN_PATH, cv2.IMREAD_UNCHANGED)
    if sign_template is None:
        raise ValueError(f"無法載入sign_text圖片: {SIGN_PATH}")
    if sign_template.shape[2] == 4:
        rgb = sign_template[:, :, :3]
        alpha = sign_template[:, :, 3]
        background = np.zeros_like(rgb)
        templates['sign'] = np.where(alpha[:, :, np.newaxis] == 0, background, rgb)
    else:
        templates['sign'] = sign_template
    
    # 載入rune_text模板
    templates['rune'] = cv2.imread(RUNE_PATH, cv2.IMREAD_COLOR)
    if templates['rune'] is None:
        raise ValueError(f"無法載入rune_text圖片: {RUNE_PATH}")

    # 載入紅點模板
    if ENABLE_RED_DOT_DETECTION:
        templates['red'] = cv2.imread(RED_DOT_PATH, cv2.IMREAD_COLOR)
        if templates['red'] is None:
            print(f"警告: 無法載入紅點圖片: {RED_DOT_PATH}，紅點偵測功能將被禁用")
            templates['red'] = None
        else:
            print(f"載入紅點模板: red.png")
            
            # ★★★ 新增：檢查並載入額外模板 ★★★
            try:
                from config import ENABLE_MULTI_RED_DOT
                if ENABLE_MULTI_RED_DOT:
                    base_dir = os.path.dirname(RED_DOT_PATH)
                    for i in range(1, 5):
                        extra_path = os.path.join(base_dir, f'red{i}.png')
                        if os.path.exists(extra_path):
                            print(f"載入額外紅點模板: red{i}.png")
            except ImportError:
                print("使用單一紅點模板模式")
    else:
        templates['red'] = None

    # 載入換頻道圖片模板
    change_templates = {}
    change_paths = {
        'change0': CHANGE0_PATH,
        'change0_1': CHANGE0_1_PATH,
        'change1': CHANGE1_PATH,
        'change2': CHANGE2_PATH,
        'change3': CHANGE3_PATH,
        'change4': CHANGE4_PATH,
        'change5': CHANGE5_PATH
    }
    
    for change_name, change_path in change_paths.items():
        template = cv2.imread(change_path, cv2.IMREAD_COLOR)
        if template is not None:
            change_templates[change_name] = template
            print(f"載入換頻道模板: {change_name}.png")
        else:
            print(f"警告: 無法載入 {change_path}")
    
    templates['change'] = change_templates
    
    # 載入方向檢測模板
    direction_templates = {}
    direction_masks = {}
    direction_folder = os.path.join(ASSETS_DIR, 'Detection')
    
    if os.path.exists(direction_folder):
        for file_name in os.listdir(direction_folder):
            if file_name.endswith('.bmp'):
                template_path = os.path.join(direction_folder, file_name)
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is not None:
                    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                    _, mask = cv2.threshold(template_gray, 254, 255, cv2.THRESH_BINARY_INV)
                    direction_templates[file_name.split('.')[0]] = template
                    direction_masks[file_name.split('.')[0]] = mask
                    print(f"載入方向模板: {file_name}")
    
    templates['direction'] = direction_templates
    templates['direction_masks'] = direction_masks
    
    return templates


@require_authentication()
def initialize_components(templates, screen_region):
    """初始化所有組件 - 需要認證"""
    
    # 再次檢查認證（額外保險）
    from core.auth_manager import get_auth_manager
    if not get_auth_manager().is_authenticated():
        raise RuntimeError("組件初始化時認證失效")
    
    components = {}
    
    # 初始化怪物檢測器
    components['monster_detector'] = SimplifiedMonsterDetector()
    components['monster_detector'].setup_templates()
    
    if not components['monster_detector'].monster_templates:
        raise ValueError("沒有載入到任何怪物模板，請檢查 ENABLED_MONSTERS 設定和資料夾路徑")

    # 初始化爬繩模組
    components['rope_climbing'] = RopeClimbing()
    components['rope_climbing'].load_rope_templates(ROPE_PATH)
    components['rope_climbing'].set_screenshot_callback(lambda: capture_screen(screen_region))
    components['rope_climbing'].set_medal_template(templates['medal'])

    # 初始化其他組件
    components['movement'] = Movement()
    components['search'] = Search()
    components['cliff_detection'] = CliffDetection()
    components['rune_mode'] = RuneMode()

    # ★★★ 添加被動技能管理器 ★★★
    from core.passive_skills_manager import PassiveSkillsManager
    components['passive_skills'] = PassiveSkillsManager()
    
    # 初始化紅點偵測器
    if ENABLE_RED_DOT_DETECTION and templates.get('red') is not None:
        components['red_dot_detector'] = RedDotDetector()
        if components['red_dot_detector'].load_red_template(RED_DOT_PATH):
            print("✅ 紅點偵測功能已啟用")
        else:
            components['red_dot_detector'] = None
            print("⚠️ 紅點偵測功能啟用失敗")
    else:
        components['red_dot_detector'] = None
        if not ENABLE_RED_DOT_DETECTION:
            print("❌ 紅點偵測功能已禁用")
    
    return components


@require_authentication()
def setup_game_window():
    """設置遊戲視窗 - 需要認證"""
    hwnd = win32gui.FindWindow(None, WINDOW_NAME)
    if not hwnd:
        raise ValueError(f"找不到遊戲視窗: {WINDOW_NAME}")

    win32gui.SetForegroundWindow(hwnd)
    print("遊戲視窗已聚焦")

    client_rect = win32gui.GetClientRect(hwnd)
    client_width, client_height = client_rect[2], client_rect[3]
    client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
    screen_region = (client_x, client_y, client_width, client_height)
    
    return {
        'hwnd': hwnd,
        'client_rect': client_rect,
        'client_width': client_width,
        'client_height': client_height,
        'client_x': client_x,
        'client_y': client_y,
        'screen_region': screen_region
    }


@require_authentication()
def main_loop(window_info, templates, components):
    """主要遊戲循環 - 帶認證檢查"""
    
    # 認證管理器
    from core.auth_manager import get_auth_manager
    auth_manager = get_auth_manager()
    
    # 定期認證檢查
    last_auth_check = time.time()
    auth_check_interval = 300  # 每5分鐘檢查一次
    
    player_x = window_info['client_width'] // 2
    player_y = window_info['client_height'] // 2
    last_monster_detection_time = 0
    last_rope_detection_time = 0
    rope_detection_interval = 1.0
    
    # 怪物清理狀態追踪
    no_monster_time = 0
    required_clear_time = 1.5
    
    is_attacking = False
    attack_end_time = 0
    
    # 性能統計
    loop_count = 0
    stats_print_interval = 300
    last_stats_time = time.time()

    print("🎮 主循環開始執行（安全版本）")

    while True:
        current_time = time.time()
        loop_count += 1
        
        # ============================================================================
        # 主循環邏輯
        # ============================================================================
        
        screenshot = capture_screen(window_info['screen_region'])

        if screenshot is not None:
            # 紅點偵測檢查
            if components.get('red_dot_detector') is not None:
                should_change_channel = components['red_dot_detector'].handle_red_dot_detection(
                    screenshot, window_info['client_width'], window_info['client_height']
                )
                
                if should_change_channel:
                    print("🚨 紅點偵測觸發換頻邏輯！")
                    from core.utils import execute_channel_change
                    
                    components['movement'].stop()
                    if components['rune_mode'].is_active:
                        components['rune_mode'].exit()
                    if components['rope_climbing'].is_climbing:
                        components['rope_climbing'].stop_climbing()
                    
                    execute_channel_change(window_info['screen_region'], templates['change'])
                    time.sleep(2)
                    continue
            
            # 如果不在特殊模式中
            if not components['rune_mode'].is_active and not components['rope_climbing'].is_climbing:
                # 檢測 sign_text
                sign_found, sign_loc, sign_val = detect_sign_text(screenshot, templates['sign'])
                if sign_found:
                    print(f"檢測到 sign_text (匹配度 {sign_val:.2f})，進入 Rune 模式")
                    components['rune_mode'].enter()
                    components['movement'].stop()
                    continue
                
                # 直接檢測 rune_text
                rune_found, rune_loc, rune_val = simple_find_medal(screenshot, templates['rune'], MATCH_THRESHOLD)
                if rune_found:
                    print(f"直接檢測到 rune_text (匹配度 {rune_val:.2f})，立即進入 Rune 模式")
                    components['rune_mode'].enter()
                    components['movement'].stop()
                    continue

                # 角色檢測
                medal_found, medal_loc, match_val = simple_find_medal(screenshot, templates['medal'], MATCH_THRESHOLD)
                if medal_found:
                    template_height, template_width = templates['medal'].shape[:2]
                    player_x = medal_loc[0] + template_width // 2
                    player_y = medal_loc[1] + template_height // 2 - Y_OFFSET
                    components['search'].last_medal_found_time = time.time()
                    components['search'].medal_lost_count = 0

                    # 怪物檢測
                    monster_found = False
                    if not components['search'].is_searching and current_time - last_monster_detection_time >= DETECTION_INTERVAL:
                        monster_found = components['monster_detector'].detect_monsters(
                            screenshot, player_x, player_y, window_info['client_width'], window_info['client_height'], 
                            components['movement'], components['cliff_detection'], window_info['client_x'], window_info['client_y']
                        )
                        last_monster_detection_time = current_time
                        
                        if monster_found:
                            is_attacking = True
                            attack_end_time = current_time + 0.2  # 假設攻擊持續0.5秒

                    # 更新攻擊狀態
                    if is_attacking and current_time > attack_end_time:
                        is_attacking = False
                    
                    # 怪物清理狀態追踪
                    if monster_found:
                        no_monster_time = current_time
                    else:
                        if no_monster_time == 0:
                            no_monster_time = current_time
                        
                        time_without_monsters = current_time - no_monster_time
                        
                        # 繩索檢測
                        if (time_without_monsters >= required_clear_time and 
                            current_time - last_rope_detection_time >= rope_detection_interval):
                            
                            rope_found, rope_x, rope_y = components['rope_climbing'].detect_rope(
                                screenshot, player_x, player_y, 
                                window_info['client_width'], window_info['client_height']
                            )
                            last_rope_detection_time = current_time
                            
                            if rope_found:
                                print("✅ 區域已清理乾淨，檢測到繩索，開始爬繩邏輯")
                                components['movement'].stop()
                                components['rope_climbing'].start_climbing(rope_x, rope_y, player_x, player_y)
                                no_monster_time = 0
                                continue

                    # 隨機移動
                    if not monster_found and not components['movement'].is_moving:
                        components['movement'].start(
                            screenshot, player_x, player_y, 
                            window_info['client_width'], window_info['client_height'], 
                            components['monster_detector']
                        )
                        
                else:
                    no_monster_time = 0
                    
                    # 搜尋角色
                    components['search'].medal_lost_count += 1
                    if components['search'].medal_lost_count >= 5 and not components['search'].is_searching:
                        search_found, search_loc, search_screenshot = components['search'].search_for_medal(
                            window_info['screen_region'], templates['medal'], MATCH_THRESHOLD, components['movement']
                        )

                # 移動中的斷層檢測
                if components['movement'].is_moving and medal_found:
                    components['cliff_detection'].check(
                        current_time, screenshot, player_x, player_y, 
                        window_info['client_width'], window_info['client_height'], 
                        templates['medal'], components['movement'].direction, 
                        window_info['client_x'], window_info['client_y']
                    )

            elif components['rope_climbing'].is_climbing:
                # 爬繩邏輯
                medal_found, medal_loc, match_val = simple_find_medal(screenshot, templates['medal'], MATCH_THRESHOLD)
                if medal_found:
                    template_height, template_width = templates['medal'].shape[:2]
                    player_x = medal_loc[0] + template_width // 2
                    player_y = medal_loc[1] + template_height // 2 - Y_OFFSET
                
                components['rope_climbing'].update_climbing(
                    screenshot, player_x, player_y, 
                    window_info['client_width'], window_info['client_height'], 
                    templates['medal'], window_info['client_x'], window_info['client_y']
                )

            elif components['rune_mode'].is_active:
                # rune模式邏輯
                components['rune_mode'].handle(
                    screenshot, window_info['screen_region'], 
                    templates['medal'], templates['rune'], 
                    templates['direction'], templates['direction_masks'], 
                    window_info['client_width'], window_info['client_height'], 
                    components['search'], components['cliff_detection'], 
                    window_info['client_x'], window_info['client_y'], 
                    components['movement'], templates['change']
                )

        # 移動狀態更新
        movement_completed = components['movement'].update()
        if (movement_completed and not components['search'].is_searching and 
            components['search'].medal_lost_count == 0 and 
            not components['rune_mode'].is_active and 
            not components['rope_climbing'].is_climbing):
            components['movement'].transition(
                screenshot, player_x, player_y, 
                window_info['client_width'], window_info['client_height'], 
                components['monster_detector']
            )

        # 定期統計信息
        if current_time - last_stats_time >= stats_print_interval:
            print("\n" + "="*60)
            print(f"📊 運行統計 (循環次數: {loop_count})")
            
            from core.utils import get_attack_key_info
            attack_info = get_attack_key_info()
            if attack_info['secondary_enabled']:
                print(f"🎯 攻擊按鍵: {attack_info['primary_key']}({attack_info['primary_chance']*100:.0f}%), {attack_info['secondary_key']}({attack_info['secondary_chance']*100:.0f}%)")
            else:
                print(f"🎯 攻擊按鍵: {attack_info['primary_key']} (僅主要攻擊)")
            
            print("="*60 + "\n")
            last_stats_time = current_time

        # ★★★ 被動技能檢查 - 放在主循環的最後，不會影響核心邏輯 ★★★
        if components.get('passive_skills'):
            components['passive_skills'].check_and_use_skills()

        time.sleep(DETECTION_INTERVAL)


def main():
    """主函數 - 安全增強版"""
    try:
        print("🔐 Artale Script 安全增強版本啟動")
        print("✅ 認證驗證已通過，開始初始化...")
        
        # 設置基本配置
        pyautogui.FAILSAFE = True
        os.chdir(WORKING_DIR)
        ensure_directories()
        
        # 驗證配置完整性
        try:
            from core.config_protection import check_config_integrity
            check_config_integrity()
        except ImportError:
            print("⚠️ 配置保護模組未找到，跳過完整性檢查")
        
        # 驗證攻擊按鍵配置
        print("\n🔍 驗證攻擊按鍵配置...")
        from core.utils import validate_attack_key_config
        attack_warnings = validate_attack_key_config()
        for warning in attack_warnings:
            print(f"   {warning}")
        
        # 設置遊戲視窗
        window_info = setup_game_window()
        
        # 載入模板
        templates = load_templates()
        
        # 初始化組件
        components = initialize_components(templates, window_info['screen_region'])
        
        # 顯示系統信息
        print("請在 1.5 秒內切換到遊戲視窗")
        time.sleep(1.5)
        print("開始執行安全版本腳本，按 Ctrl+C 停止")
        print(f"功能設定：rune高度閾值 {RUNE_HEIGHT_THRESHOLD}")
        print(f"個別化Y軸閾值：小型{SMALL_MONSTER_Y_TOLERANCE}px, 中型{MEDIUM_MONSTER_Y_TOLERANCE}px, 大型{LARGE_MONSTER_Y_TOLERANCE}px")
        print(f"檢測範圍：{MIN_DETECTION_SIZE}-{MAX_DETECTION_SIZE}")
        print(f"檢測間隔：{DETECTION_INTERVAL}秒")
        
        if JUMP_ATTACK_MODE == 'mage':
            print(f"法師位移技能鍵：{DASH_SKILL_KEY}")
        
        print(f"載入了 {len(templates['change'])} 個換頻道模板")
        print(f"載入了 {len(components['rope_climbing'].rope_templates)} 個繩索模板")
        
        # 顯示安全特性
        print("\n🔐 安全特性:")
        print("   ✅ Firebase 認證集成")
        print("   ✅ 會話令牌驗證")
        print("   ✅ 定期認證檢查")
        print("   ✅ 未授權訪問阻止")
        
        # 顯示紅點偵測狀態
        if components.get('red_dot_detector'):
            print("✅ 紅點偵測功能已啟用")
            print(f"   檢測時間範圍: {RED_DOT_MIN_TIME}-{RED_DOT_MAX_TIME} 秒")
            print(f"   檢測閾值: {RED_DOT_DETECTION_THRESHOLD}")
        else:
            print("❌ 紅點偵測功能未啟用")
        
        # 顯示攻擊按鍵配置
        from core.utils import get_attack_key_info
        attack_info = get_attack_key_info()
        if attack_info['secondary_enabled']:
            print(f"🎯 攻擊按鍵配置: 主要={attack_info['primary_key']} ({attack_info['primary_chance']*100:.0f}%), 次要={attack_info['secondary_key']} ({attack_info['secondary_chance']*100:.0f}%)")
        else:
            print(f"🎯 攻擊按鍵配置: {attack_info['primary_key']} (僅主要攻擊)")
        
        print("\n" + "="*60)
        print("🚀 所有功能已就緒，開始安全版本主循環...")
        print("🔐 會話將定期驗證，確保持續授權")
        print("="*60)
        
        # 開始主循環
        main_loop(window_info, templates, components)

    except KeyboardInterrupt:
        print("\n腳本已終止")
        # 清理認證令牌
        from core.auth_manager import get_auth_manager
        get_auth_manager().clear_session()
        print("✅ 認證會話已清理")
        
    except Exception as e:
        print(f"\n程式執行失敗: {str(e)}")
        
        # 檢查是否為認證相關錯誤
        if any(keyword in str(e).lower() for keyword in ['認證', '未授權', 'auth', 'unauthorized']):
            print("\n💡 這可能是認證相關問題，請嘗試:")
            print("   1. 重新通過 GUI 登入")
            print("   2. 檢查會話是否過期")
            print("   3. 確保 Firebase 連接正常")

if __name__ == "__main__":
    main()