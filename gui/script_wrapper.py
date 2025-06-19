"""
腳本包裝器 - 整合現有Artale腳本到GUI中 (修復版)
"""
import threading
import queue
import time
import sys
import os
import traceback
import psutil
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import io
import contextlib

class LogCapture:
    """日誌捕獲類 - 重定向print輸出到GUI"""
    
    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def write(self, text):
        """寫入方法"""
        if text.strip():  # 只記錄非空內容
            try:
                self.log_queue.put_nowait(('log', text.strip()))
            except queue.Full:
                pass  # 如果隊列滿了就忽略
        
        # 同時輸出到原始輸出
        self.original_stdout.write(text)
        
    def flush(self):
        """刷新方法"""
        self.original_stdout.flush()

class ScriptWrapper:
    """腳本包裝器類 - 管理Artale腳本的執行"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        
        # 線程和狀態管理
        self.script_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_stopping = False
        
        # 通信隊列
        self.command_queue = queue.Queue(maxsize=10)
        self.status_queue = queue.Queue(maxsize=50)
        self.log_queue = queue.Queue(maxsize=100)
        
        # 腳本狀態 - 移除怪物擊殺統計
        self.script_stats = {
            'start_time': None,
            'total_runtime': 0,
            'current_status': '未運行',
            'last_activity': None,
            'errors': 0,
            'detections': 0
        }
        
        # 性能監控
        self.process = psutil.Process()
        self.performance_stats = {
            'cpu_percent': 0.0,
            'memory_mb': 0.0,
            'threads_count': 0
        }
        
        # 腳本組件引用
        self.script_components = None
        
        # 日誌捕獲
        self.log_capture = None
        
        # 啟動狀態監控線程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def start_script(self) -> bool:
        """啟動腳本"""
        if self.is_running:
            self._send_log("⚠️ 腳本已在運行中")
            return False
            
        try:
            self._send_log("🚀 正在啟動腳本...")
            
            # 重置統計
            self._reset_stats()
            
            # 創建並啟動腳本線程
            self.script_thread = threading.Thread(target=self._script_main_loop, daemon=True)
            self.script_thread.start()
            
            # 等待腳本初始化完成
            time.sleep(1.0)
            
            if self.is_running:
                self._send_log("✅ 腳本啟動成功")
                self._update_status('運行中')
                return True
            else:
                self._send_log("❌ 腳本啟動失敗")
                return False
                
        except Exception as e:
            self._send_log(f"❌ 啟動腳本時發生錯誤: {str(e)}")
            self._send_log(f"詳細錯誤: {traceback.format_exc()}")
            return False
    
    def stop_script(self) -> bool:
        """停止腳本"""
        if not self.is_running:
            self._send_log("⚠️ 腳本未在運行")
            return False
            
        try:
            self._send_log("🛑 正在停止腳本...")
            self.is_stopping = True
            
            # 等待腳本線程結束
            if self.script_thread and self.script_thread.is_alive():
                self.script_thread.join(timeout=5.0)  # 最多等待5秒
                
            # 清理資源
            self._cleanup_script_resources()
            
            self._send_log("✅ 腳本已停止")
            self._update_status('已停止')
            return True
            
        except Exception as e:
            self._send_log(f"❌ 停止腳本時發生錯誤: {str(e)}")
            return False
    
    def _script_main_loop(self):
        """腳本主循環"""
        try:
            self.is_running = True
            self.is_stopping = False
            self.script_stats['start_time'] = time.time()
            
            # 設置日誌捕獲
            self._setup_log_capture()
            
            self._send_log("🔧 初始化腳本組件...")
            
            # 導入並初始化腳本組件
            success = self._initialize_script_components()
            if not success:
                self._send_log("❌ 腳本組件初始化失敗")
                self.is_running = False
                return
            
            self._send_log("✅ 腳本組件初始化完成")
            self._send_log("🎮 開始執行主循環...")
            
            # 執行主循環
            self._execute_main_loop()
            
        except Exception as e:
            self._send_log(f"❌ 腳本執行錯誤: {str(e)}")
            self._send_log(f"詳細錯誤: {traceback.format_exc()}")
            self.script_stats['errors'] += 1
        finally:
            self._cleanup_script_resources()
            self.is_running = False
            self._send_log("🏁 腳本主循環已結束")
    
    def _initialize_script_components(self) -> bool:
        """初始化腳本組件"""
        try:
            # 確保可以導入腳本模組
            script_dir = os.path.dirname(os.path.dirname(__file__))
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            # 逐步導入模組，避免import *
            self._send_log("📦 導入基礎模組...")
            
            # 導入配置
            import config
            self.config = config
            
            # 導入基礎工具
            import pyautogui
            import cv2
            import numpy as np
            import win32gui
            
            # 導入工具函數
            try:
                import utils
                self.utils = utils
            except ImportError:
                # 如果 utils 在 core 資料夾中
                from core import utils
                self.utils = utils
            
            self._send_log("📦 導入腳本組件...")
            
            # 導入腳本組件
            from core.monster_detector import SimplifiedMonsterDetector
            from core.movement import Movement
            from core.enhanced_movement import EnhancedMovement
            from core.search import Search
            from core.cliff_detection import CliffDetection
            from core.rope_climbing import RopeClimbing
            from core.rune_mode import RuneMode
            from core.red_dot_detector import RedDotDetector
            
            self._send_log("📦 模組導入完成")
            
            # 設置基本配置
            pyautogui.FAILSAFE = True
            os.chdir(config.WORKING_DIR)
            
            # 初始化遊戲視窗
            window_info = self._setup_game_window()
            if not window_info:
                return False
            
            # 載入模板
            templates = self._load_templates()
            if not templates:
                return False
            
            # 初始化組件
            components = self._initialize_components(templates, window_info['screen_region'])
            if not components:
                return False
            
            # 保存組件引用
            self.script_components = {
                'window_info': window_info,
                'templates': templates,
                'components': components
            }
            
            return True
            
        except Exception as e:
            self._send_log(f"❌ 初始化組件失敗: {str(e)}")
            self._send_log(f"詳細錯誤: {traceback.format_exc()}")
            return False
    
    def _setup_game_window(self):
        """設置遊戲視窗"""
        try:
            import win32gui
            
            hwnd = win32gui.FindWindow(None, self.config.WINDOW_NAME)
            if not hwnd:
                self._send_log(f"❌ 找不到遊戲視窗: {self.config.WINDOW_NAME}")
                return None

            win32gui.SetForegroundWindow(hwnd)
            self._send_log("✅ 遊戲視窗已聚焦")

            client_rect = win32gui.GetClientRect(hwnd)
            client_width, client_height = client_rect[2], client_rect[3]
            client_x, client_y = win32gui.ClientToScreen(hwnd, (0, 0))
            screen_region = (client_x, client_y, client_width, client_height)
            
            window_info = {
                'hwnd': hwnd,
                'client_rect': client_rect,
                'client_width': client_width,
                'client_height': client_height,
                'client_x': client_x,
                'client_y': client_y,
                'screen_region': screen_region
            }
            
            self._send_log(f"✅ 遊戲視窗設置完成: {client_width}x{client_height}")
            return window_info
            
        except Exception as e:
            self._send_log(f"❌ 設置遊戲視窗失敗: {str(e)}")
            return None
    
    def _load_templates(self):
        """載入模板"""
        try:
            # 使用utils中的函數載入模板
            import cv2
            import numpy as np
            
            templates = {}
            
            # 載入基本模板
            templates['medal'] = cv2.imread(self.config.MEDAL_PATH, cv2.IMREAD_COLOR)
            if templates['medal'] is None:
                raise ValueError(f"無法載入ID圖片: {self.config.MEDAL_PATH}")
            
            # 載入sign_text模板
            sign_template = cv2.imread(self.config.SIGN_PATH, cv2.IMREAD_UNCHANGED)
            if sign_template is None:
                raise ValueError(f"無法載入sign_text圖片: {self.config.SIGN_PATH}")
            if sign_template.shape[2] == 4:
                rgb = sign_template[:, :, :3]
                alpha = sign_template[:, :, 3]
                background = np.zeros_like(rgb)
                templates['sign'] = np.where(alpha[:, :, np.newaxis] == 0, background, rgb)
            else:
                templates['sign'] = sign_template
            
            # 載入rune_text模板
            templates['rune'] = cv2.imread(self.config.RUNE_PATH, cv2.IMREAD_COLOR)
            if templates['rune'] is None:
                raise ValueError(f"無法載入rune_text圖片: {self.config.RUNE_PATH}")

            # 載入紅點模板
            if self.config.ENABLE_RED_DOT_DETECTION:
                templates['red'] = cv2.imread(self.config.RED_DOT_PATH, cv2.IMREAD_COLOR)
                if templates['red'] is None:
                    self._send_log(f"警告: 無法載入紅點圖片: {self.config.RED_DOT_PATH}")
                    templates['red'] = None
                else:
                    self._send_log(f"載入紅點模板: red.png")
            else:
                templates['red'] = None

            # 簡化的換頻道模板載入
            change_templates = {}
            change_paths = {
                'change0': self.config.CHANGE0_PATH,
                'change1': self.config.CHANGE1_PATH,
                'change2': self.config.CHANGE2_PATH,
                'change3': self.config.CHANGE3_PATH,
                'change4': self.config.CHANGE4_PATH,
                'change5': self.config.CHANGE5_PATH
            }
            
            for change_name, change_path in change_paths.items():
                template = cv2.imread(change_path, cv2.IMREAD_COLOR)
                if template is not None:
                    change_templates[change_name] = template
                    self._send_log(f"載入換頻道模板: {change_name}.png")
                else:
                    self._send_log(f"警告: 無法載入 {change_path}")
            
            templates['change'] = change_templates
            
            # 載入方向檢測模板（簡化版）
            direction_templates = {}
            direction_masks = {}
            direction_folder = os.path.join(self.config.ASSETS_DIR, 'Detection')
            
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
                            self._send_log(f"載入方向模板: {file_name}")
            
            templates['direction'] = direction_templates
            templates['direction_masks'] = direction_masks
            
            template_count = len([k for k, v in templates.items() if v is not None])
            self._send_log(f"✅ 模板載入完成，共載入 {template_count} 類模板")
            return templates
            
        except Exception as e:
            self._send_log(f"❌ 載入模板失敗: {str(e)}")
            return None
    
    def _initialize_components(self, templates, screen_region):
        """初始化組件"""
        try:
            from core.monster_detector import SimplifiedMonsterDetector
            from core.movement import Movement
            from core.enhanced_movement import EnhancedMovement
            from core.search import Search
            from core.cliff_detection import CliffDetection
            from core.rope_climbing import RopeClimbing
            from core.rune_mode import RuneMode
            from core.red_dot_detector import RedDotDetector
            
            components = {}
            
            # 初始化怪物檢測器
            components['monster_detector'] = SimplifiedMonsterDetector()
            components['monster_detector'].setup_templates()
            
            if not components['monster_detector'].monster_templates:
                raise ValueError("沒有載入到任何怪物模板，請檢查 ENABLED_MONSTERS 設定和資料夾路徑")

            # 初始化爬繩模組
            components['rope_climbing'] = RopeClimbing()
            components['rope_climbing'].load_rope_templates(self.config.ROPE_PATH)
            components['rope_climbing'].set_screenshot_callback(lambda: self.utils.capture_screen(screen_region))
            components['rope_climbing'].set_medal_template(templates['medal'])

            # 初始化其他組件
            components['movement'] = Movement()
            components['search'] = Search()
            components['cliff_detection'] = CliffDetection()
            components['rune_mode'] = RuneMode()
            
            # 初始化紅點偵測器
            if self.config.ENABLE_RED_DOT_DETECTION and templates.get('red') is not None:
                components['red_dot_detector'] = RedDotDetector()
                if components['red_dot_detector'].load_red_template(self.config.RED_DOT_PATH):
                    self._send_log("✅ 紅點偵測功能已啟用")
                else:
                    components['red_dot_detector'] = None
                    self._send_log("⚠️ 紅點偵測功能啟用失敗")
            else:
                components['red_dot_detector'] = None
                if not self.config.ENABLE_RED_DOT_DETECTION:
                    self._send_log("❌ 紅點偵測功能已禁用")
            
            component_count = len(components)
            self._send_log(f"✅ 組件初始化完成，共初始化 {component_count} 個組件")
            return components
            
        except Exception as e:
            self._send_log(f"❌ 初始化組件失敗: {str(e)}")
            return None
    
    def _execute_main_loop(self):
        """執行主循環"""
        try:
            if not self.script_components:
                self._send_log("❌ 腳本組件未初始化")
                return
            
            window_info = self.script_components['window_info']
            templates = self.script_components['templates']
            components = self.script_components['components']
            
            # 使用簡化的主循環邏輯
            self._execute_artale_main_loop(window_info, templates, components)
            
        except Exception as e:
            self._send_log(f"❌ 主循環執行錯誤: {str(e)}")
            self._send_log(f"詳細錯誤: {traceback.format_exc()}")

    def _setup_authentication_for_script(self):
        """為腳本設置認證令牌"""
        try:
            # 從 Firebase 認證管理器獲取當前用戶信息
            if self.gui.auth_manager and self.gui.auth_manager.is_user_logged_in():
                current_user = self.gui.auth_manager.get_current_user()
                
                if current_user:
                    # 創建本地認證管理器
                    from core.auth_manager import get_auth_manager
                    local_auth = get_auth_manager()
                    
                    # 生成會話令牌
                    user_uuid = "firebase_user"  # 這裡可以用實際的用戶標識
                    token = local_auth.generate_session_token(user_uuid)
                    
                    # 保存令牌供主腳本使用
                    local_auth.save_session_token(token)
                    
                    self._send_log("✅ 認證令牌已設置，腳本可以安全執行")
                    return True
            
            self._send_log("❌ 無法設置認證令牌：用戶未登入")
            return False
            
        except Exception as e:
            self._send_log(f"❌ 設置認證令牌失敗: {str(e)}")
            return False

    def _execute_artale_main_loop(self, window_info, templates, components):
        """執行Artale主循環"""
        # 設置認證令牌
        if not self._setup_authentication_for_script():
            self._send_log("❌ 認證設置失敗，無法啟動腳本")
            return
        player_x = window_info['client_width'] // 2
        player_y = window_info['client_height'] // 2
        last_monster_detection_time = 0
        last_rope_detection_time = 0
        rope_detection_interval = 1.0
        
        no_monster_time = 0
        required_clear_time = 1.5
        
        loop_count = 0
        
        self._send_log("🎮 主循環開始執行")
        
        while self.is_running and not self.is_stopping:
            try:
                loop_count += 1
                current_time = time.time()
                
                # 處理GUI命令
                self._process_commands()
                
                # 更新統計
                if loop_count % 100 == 0:
                    self._update_script_stats()
                
                screenshot = self.utils.capture_screen(window_info['screen_region'])
                if screenshot is None:
                    continue

                # 紅點偵測檢查
                if components.get('red_dot_detector') is not None:
                    should_change_channel = components['red_dot_detector'].handle_red_dot_detection(
                        screenshot, window_info['client_width'], window_info['client_height']
                    )
                    
                    if should_change_channel:
                        self._send_log("🚨 紅點偵測觸發換頻邏輯！")
                        
                        components['movement'].stop()
                        if components['rune_mode'].is_active:
                            components['rune_mode'].exit()
                        if components['rope_climbing'].is_climbing:
                            components['rope_climbing'].stop_climbing()
                        
                        self.utils.execute_channel_change(window_info['screen_region'], templates['change'])
                        time.sleep(2)
                        continue

                # 如果不在特殊模式中
                if not components['rune_mode'].is_active and not components['rope_climbing'].is_climbing:
                    # 檢測 sign_text
                    sign_found, sign_loc, sign_val = self.utils.detect_sign_text(screenshot, templates['sign'])
                    if sign_found:
                        self._send_log(f"檢測到 sign_text (匹配度 {sign_val:.2f})，進入 Rune 模式")
                        components['rune_mode'].enter()
                        components['movement'].stop()
                        continue
                    
                    # 檢測 rune_text
                    rune_found, rune_loc, rune_val = self.utils.simple_find_medal(screenshot, templates['rune'], self.config.MATCH_THRESHOLD)
                    if rune_found:
                        self._send_log(f"直接檢測到 rune_text (匹配度 {rune_val:.2f})，立即進入 Rune 模式")
                        components['rune_mode'].enter()
                        components['movement'].stop()
                        continue

                    # 角色檢測
                    medal_found, medal_loc, match_val = self.utils.simple_find_medal(screenshot, templates['medal'], self.config.MATCH_THRESHOLD)
                    if medal_found:
                        template_height, template_width = templates['medal'].shape[:2]
                        player_x = medal_loc[0] + template_width // 2
                        player_y = medal_loc[1] + template_height // 2 - self.config.Y_OFFSET
                        components['search'].last_medal_found_time = time.time()
                        components['search'].medal_lost_count = 0

                        # 怪物檢測 - 不再記錄擊殺數量
                        monster_found = False
                        if not components['search'].is_searching and current_time - last_monster_detection_time >= self.config.DETECTION_INTERVAL:
                            monster_found = components['monster_detector'].detect_monsters(
                                screenshot, player_x, player_y, window_info['client_width'], window_info['client_height'], 
                                components['movement'], components['cliff_detection'], window_info['client_x'], window_info['client_y']
                            )
                            last_monster_detection_time = current_time
                            
                            if monster_found:
                                self.script_stats['detections'] += 1

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
                                    self._send_log("✅ 區域已清理乾淨，檢測到繩索，開始爬繩邏輯")
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
                        # 搜尋角色邏輯
                        components['search'].medal_lost_count += 1
                        if components['search'].medal_lost_count >= 5 and not components['search'].is_searching:
                            search_found, search_loc, search_screenshot = components['search'].search_for_medal(
                                window_info['screen_region'], templates['medal'], self.config.MATCH_THRESHOLD, components['movement']
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
                    medal_found, medal_loc, match_val = self.utils.simple_find_medal(screenshot, templates['medal'], self.config.MATCH_THRESHOLD)
                    if medal_found:
                        template_height, template_width = templates['medal'].shape[:2]
                        player_x = medal_loc[0] + template_width // 2
                        player_y = medal_loc[1] + template_height // 2 - self.config.Y_OFFSET
                    
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

                time.sleep(self.config.DETECTION_INTERVAL)
                
            except Exception as e:
                self._send_log(f"❌ 主循環迭代錯誤: {str(e)}")
                self.script_stats['errors'] += 1
                time.sleep(1)
                
        self._send_log("🏁 主循環已退出")
    
    def _process_commands(self):
        """處理來自GUI的命令"""
        try:
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
                command_type = command.get('type')
                
                if command_type == 'stop':
                    self.is_stopping = True
                elif command_type == 'update_config':
                    self._update_config(command.get('config', {}))
                elif command_type == 'get_stats':
                    self._send_stats()
                    
        except queue.Empty:
            pass
        except Exception as e:
            self._send_log(f"❌ 處理命令錯誤: {str(e)}")
    
    def _update_config(self, config_updates: Dict[str, Any]):
        """更新配置"""
        try:
            for key, value in config_updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
                    self._send_log(f"⚙️ 配置已更新: {key} = {value}")
                    
        except Exception as e:
            self._send_log(f"❌ 更新配置錯誤: {str(e)}")
    
    def _update_script_stats(self):
        """更新腳本統計"""
        if self.script_stats['start_time']:
            self.script_stats['total_runtime'] = time.time() - self.script_stats['start_time']
            self.script_stats['last_activity'] = time.time()
        
        # 更新性能統計
        try:
            self.performance_stats['cpu_percent'] = self.process.cpu_percent()
            self.performance_stats['memory_mb'] = self.process.memory_info().rss / 1024 / 1024
            self.performance_stats['threads_count'] = self.process.num_threads()
        except:
            pass
    
    def _send_stats(self):
        """發送統計信息到GUI"""
        try:
            stats_data = {
                'script_stats': self.script_stats.copy(),
                'performance_stats': self.performance_stats.copy()
            }
            self.status_queue.put_nowait(('stats', stats_data))
        except queue.Full:
            pass
    
    def _setup_log_capture(self):
        """設置日誌捕獲"""
        try:
            self.log_capture = LogCapture(self.log_queue)
            sys.stdout = self.log_capture
            # sys.stderr = self.log_capture  # 可選：也捕獲錯誤輸出
        except Exception as e:
            self._send_log(f"⚠️ 設置日誌捕獲失敗: {str(e)}")
    
    def _cleanup_script_resources(self):
        """清理腳本資源"""
        try:
            # 恢復原始輸出
            if self.log_capture:
                sys.stdout = self.log_capture.original_stdout
                sys.stderr = self.log_capture.original_stderr
                self.log_capture = None
            
            # 停止所有組件
            if self.script_components and 'components' in self.script_components:
                components = self.script_components['components']
                if 'movement' in components:
                    components['movement'].stop()
                if 'rune_mode' in components:
                    components['rune_mode'].exit()
                if 'rope_climbing' in components:
                    components['rope_climbing'].stop_climbing()
                if 'red_dot_detector' in components and components['red_dot_detector']:
                    components['red_dot_detector'].reset_detection()
            
            self.script_components = None
            self._send_log("🧹 腳本資源清理完成")
            
        except Exception as e:
            self._send_log(f"⚠️ 清理資源時發生錯誤: {str(e)}")
            # 清理認證令牌
            from core.auth_manager import get_auth_manager
            local_auth = get_auth_manager()
            local_auth.clear_session()
            
            self._send_log("🧹 認證令牌已清理")
            
        except Exception as e:
            self._send_log(f"⚠️ 清理認證令牌時發生錯誤: {str(e)}")
    
    def _reset_stats(self):
        """重置統計"""
        self.script_stats = {
            'start_time': None,
            'total_runtime': 0,
            'current_status': '正在啟動',
            'last_activity': None,
            'errors': 0,
            'detections': 0
        }
    
    def _monitor_loop(self):
        """監控循環 - 處理與GUI的通信"""
        while True:
            try:
                # 處理日誌隊列
                while not self.log_queue.empty():
                    try:
                        log_type, message = self.log_queue.get_nowait()
                        if log_type == 'log':
                            # 發送日誌到GUI
                            self.gui.root.after(0, self.gui.log, message)
                    except queue.Empty:
                        break
                
                # 處理狀態隊列
                while not self.status_queue.empty():
                    try:
                        status_type, data = self.status_queue.get_nowait()
                        if status_type == 'stats':
                            # 發送統計到GUI
                            self.gui.root.after(0, self._update_gui_stats, data)
                        elif status_type == 'status':
                            # 更新狀態
                            self.gui.root.after(0, self.gui.update_status, data)
                    except queue.Empty:
                        break
                
                # 定期發送統計信息
                if self.is_running:
                    self._update_script_stats()
                    self._send_stats()
                
                time.sleep(0.1)  # 每100ms檢查一次
                
            except Exception as e:
                print(f"監控循環錯誤: {str(e)}")
                time.sleep(1)
    
    def _update_gui_stats(self, stats_data):
        """更新GUI統計信息 - 移除怪物擊殺顯示"""
        try:
            script_stats = stats_data['script_stats']
            performance_stats = stats_data['performance_stats']
            
            # 更新運行時間
            if script_stats['total_runtime'] > 0:
                runtime_str = str(timedelta(seconds=int(script_stats['total_runtime'])))
                self.gui.runtime_label.configure(text=f"運行時間: {runtime_str}")
            
        except Exception as e:
            print(f"更新GUI統計錯誤: {str(e)}")
    
    def _send_log(self, message: str):
        """發送日誌消息"""
        try:
            self.log_queue.put_nowait(('log', message))
        except queue.Full:
            pass  # 如果隊列滿了就忽略
    
    def _update_status(self, status: str):
        """更新狀態"""
        self.script_stats['current_status'] = status
        try:
            self.status_queue.put_nowait(('status', status))
        except queue.Full:
            pass
    
    def send_command(self, command_type: str, **kwargs):
        """發送命令到腳本"""
        try:
            command = {'type': command_type, **kwargs}
            self.command_queue.put_nowait(command)
            return True
        except queue.Full:
            self._send_log("⚠️ 命令隊列已滿，命令被忽略")
            return False
    
    def update_detection_interval(self, interval: float):
        """更新檢測間隔"""
        self.send_command('update_config', config={'DETECTION_INTERVAL': interval})
    
    def toggle_red_dot_detection(self, enabled: bool):
        """切換紅點偵測"""
        self.send_command('update_config', config={'ENABLE_RED_DOT_DETECTION': enabled})
    
    def toggle_enhanced_movement(self, enabled: bool):
        """切換增強移動"""
        self.send_command('update_config', config={'ENABLE_ENHANCED_MOVEMENT': enabled})
    
    def get_script_stats(self) -> Dict[str, Any]:
        """獲取腳本統計"""
        return {
            'is_running': self.is_running,
            'script_stats': self.script_stats.copy(),
            'performance_stats': self.performance_stats.copy()
        }
    
    def is_script_running(self) -> bool:
        """檢查腳本是否在運行"""
        return self.is_running
    
    def cleanup(self):
        """清理包裝器資源"""
        if self.is_running:
            self.stop_script()
        
        # 清理隊列
        while not self.command_queue.empty():
            try:
                self.command_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.status_queue.empty():
            try:
                self.status_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except queue.Empty:
                break