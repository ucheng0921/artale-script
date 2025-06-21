"""
腳本包裝器 - 整合main.py功能到GUI中
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
    """腳本包裝器類 - 使用main.py的功能"""
    
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
        
        # 腳本狀態
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
        
        # main.py 相關組件
        self.main_components = None
        self.main_window_info = None
        self.main_templates = None
        
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
        """腳本主循環 - 使用main.py的功能"""
        try:
            self.is_running = True
            self.is_stopping = False
            self.script_stats['start_time'] = time.time()
            
            # 設置日誌捕獲
            self._setup_log_capture()
            
            self._send_log("🔧 初始化腳本組件...")
            
            # 使用main.py的初始化函數
            success = self._initialize_main_components()
            if not success:
                self._send_log("❌ 腳本組件初始化失敗")
                self.is_running = False
                return
            
            self._send_log("✅ 腳本組件初始化完成")
            self._send_log("🎮 開始執行主循環...")
            
            # 執行main.py的主循環邏輯
            self._execute_main_loop_logic()
            
        except Exception as e:
            self._send_log(f"❌ 腳本執行錯誤: {str(e)}")
            self._send_log(f"詳細錯誤: {traceback.format_exc()}")
            self.script_stats['errors'] += 1
        finally:
            self._cleanup_script_resources()
            self.is_running = False
            self._send_log("🏁 腳本主循環已結束")
    
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
    
    def _initialize_main_components(self) -> bool:
        """使用main.py的初始化函數"""
        try:
            # 設置認證令牌
            if not self._setup_authentication_for_script():
                self._send_log("❌ 認證設置失敗，無法啟動腳本")
                return False
            
            # 設置環境變數以確保能夠通過認證檢查
            os.environ['ARTALE_GUI_MODE'] = 'true'
            
            # 導入main.py的函數
            from main import setup_game_window, load_templates, initialize_components
            
            self._send_log("📦 設置遊戲視窗...")
            
            # 使用main.py的函數設置遊戲視窗
            self.main_window_info = setup_game_window()
            
            self._send_log("📦 載入模板...")
            
            # 使用main.py的函數載入模板
            self.main_templates = load_templates()
            
            self._send_log("📦 初始化組件...")
            
            # 使用main.py的函數初始化組件
            self.main_components = initialize_components(
                self.main_templates, 
                self.main_window_info['screen_region']
            )

            # ★★★ 添加：初始化被動技能管理器 ★★★
            try:
                from core.passive_skills_manager import PassiveSkillsManager
                self.main_components['passive_skills'] = PassiveSkillsManager()
                self._send_log("✅ 被動技能管理器已初始化")
            except Exception as e:
                self._send_log(f"⚠️ 被動技能管理器初始化失敗: {str(e)}")
                # 不影響主要功能，繼續執行
                self.main_components['passive_skills'] = None
            
            self._send_log("✅ 所有組件初始化完成")
            return True
            
        except Exception as e:
            self._send_log(f"❌ 初始化main.py組件失敗: {str(e)}")
            self._send_log(f"詳細錯誤: {traceback.format_exc()}")
            return False
    
    def _execute_main_loop_logic(self):
        """執行main.py的主循環邏輯（修改版）"""
        if not all([self.main_window_info, self.main_templates, self.main_components]):
            self._send_log("❌ 組件未正確初始化")
            return
        
        # 導入main.py的配置
        import config
        from core.utils import capture_screen, detect_sign_text, simple_find_medal
        
        # 認證管理器
        from core.auth_manager import get_auth_manager
        auth_manager = get_auth_manager()
        
        # 主循環變數（與main.py相同）
        player_x = self.main_window_info['client_width'] // 2
        player_y = self.main_window_info['client_height'] // 2
        last_monster_detection_time = 0
        last_rope_detection_time = 0
        rope_detection_interval = 1.0
        
        no_monster_time = 0
        required_clear_time = 1.5
        
        is_attacking = False
        attack_end_time = 0
        
        loop_count = 0
        last_auth_check = time.time()
        auth_check_interval = 300  # 每5分鐘檢查一次
        
        self._send_log("🎮 主循環開始執行（GUI模式）")
        
        while self.is_running and not self.is_stopping:
            try:
                current_time = time.time()
                loop_count += 1
                
                # 處理GUI命令
                self._process_commands()
                
                # 更新統計
                if loop_count % 100 == 0:
                    self._update_script_stats()
                
                # 使用main.py的邏輯進行遊戲循環
                screenshot = capture_screen(self.main_window_info['screen_region'])
                if screenshot is None:
                    continue
                
                # === 以下是main.py主循環的核心邏輯 ===
                
                # 紅點偵測檢查
                if self.main_components.get('red_dot_detector') is not None:
                    should_change_channel = self.main_components['red_dot_detector'].handle_red_dot_detection(
                        screenshot, self.main_window_info['client_width'], self.main_window_info['client_height']
                    )
                    
                    if should_change_channel:
                        self._send_log("🚨 紅點偵測觸發換頻邏輯！")
                        from core.utils import execute_channel_change
                        
                        self.main_components['movement'].stop()
                        if self.main_components['rune_mode'].is_active:
                            self.main_components['rune_mode'].exit()
                        if self.main_components['rope_climbing'].is_climbing:
                            self.main_components['rope_climbing'].stop_climbing()
                        
                        execute_channel_change(self.main_window_info['screen_region'], self.main_templates['change'])
                        time.sleep(2)
                        continue
                
                # 如果不在特殊模式中
                if not self.main_components['rune_mode'].is_active and not self.main_components['rope_climbing'].is_climbing:
                    # 檢測 sign_text
                    sign_found, sign_loc, sign_val = detect_sign_text(screenshot, self.main_templates['sign'])
                    if sign_found:
                        self._send_log(f"檢測到 sign_text (匹配度 {sign_val:.2f})，進入 Rune 模式")
                        self.main_components['rune_mode'].enter()
                        self.main_components['movement'].stop()
                        continue
                    
                    # 直接檢測 rune_text
                    rune_found, rune_loc, rune_val = simple_find_medal(screenshot, self.main_templates['rune'], config.MATCH_THRESHOLD)
                    if rune_found:
                        self._send_log(f"直接檢測到 rune_text (匹配度 {rune_val:.2f})，立即進入 Rune 模式")
                        self.main_components['rune_mode'].enter()
                        self.main_components['movement'].stop()
                        continue

                    # 角色檢測
                    medal_found, medal_loc, match_val = simple_find_medal(screenshot, self.main_templates['medal'], config.MATCH_THRESHOLD)
                    if medal_found:
                        template_height, template_width = self.main_templates['medal'].shape[:2]
                        player_x = medal_loc[0] + template_width // 2
                        player_y = medal_loc[1] + template_height // 2 - config.Y_OFFSET
                        self.main_components['search'].last_medal_found_time = time.time()
                        self.main_components['search'].medal_lost_count = 0

                        # 怪物檢測
                        monster_found = False
                        if not self.main_components['search'].is_searching and current_time - last_monster_detection_time >= config.DETECTION_INTERVAL:
                            monster_found = self.main_components['monster_detector'].detect_monsters(
                                screenshot, player_x, player_y, self.main_window_info['client_width'], self.main_window_info['client_height'], 
                                self.main_components['movement'], self.main_components['cliff_detection'], 
                                self.main_window_info['client_x'], self.main_window_info['client_y']
                            )
                            last_monster_detection_time = current_time
                            
                            if monster_found:
                                is_attacking = True
                                attack_end_time = current_time + 0.2
                                self.script_stats['detections'] += 1

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
                                
                                rope_found, rope_x, rope_y = self.main_components['rope_climbing'].detect_rope(
                                    screenshot, player_x, player_y, 
                                    self.main_window_info['client_width'], self.main_window_info['client_height']
                                )
                                last_rope_detection_time = current_time
                                
                                if rope_found:
                                    self._send_log("✅ 區域已清理乾淨，檢測到繩索，開始爬繩邏輯")
                                    self.main_components['movement'].stop()
                                    self.main_components['rope_climbing'].start_climbing(rope_x, rope_y, player_x, player_y)
                                    no_monster_time = 0
                                    continue

                        # 隨機移動
                        if not monster_found and not self.main_components['movement'].is_moving:
                            self.main_components['movement'].start(
                                screenshot, player_x, player_y, 
                                self.main_window_info['client_width'], self.main_window_info['client_height'], 
                                self.main_components['monster_detector']
                            )
                            
                    else:
                        no_monster_time = 0
                        
                        # 搜尋角色
                        self.main_components['search'].medal_lost_count += 1
                        if self.main_components['search'].medal_lost_count >= 5 and not self.main_components['search'].is_searching:
                            search_found, search_loc, search_screenshot = self.main_components['search'].search_for_medal(
                                self.main_window_info['screen_region'], self.main_templates['medal'], config.MATCH_THRESHOLD, self.main_components['movement']
                            )

                    # 移動中的斷層檢測
                    if self.main_components['movement'].is_moving and medal_found:
                        self.main_components['cliff_detection'].check(
                            current_time, screenshot, player_x, player_y, 
                            self.main_window_info['client_width'], self.main_window_info['client_height'], 
                            self.main_templates['medal'], self.main_components['movement'].direction, 
                            self.main_window_info['client_x'], self.main_window_info['client_y']
                        )

                elif self.main_components['rope_climbing'].is_climbing:
                    # 爬繩邏輯
                    medal_found, medal_loc, match_val = simple_find_medal(screenshot, self.main_templates['medal'], config.MATCH_THRESHOLD)
                    if medal_found:
                        template_height, template_width = self.main_templates['medal'].shape[:2]
                        player_x = medal_loc[0] + template_width // 2
                        player_y = medal_loc[1] + template_height // 2 - config.Y_OFFSET
                    
                    self.main_components['rope_climbing'].update_climbing(
                        screenshot, player_x, player_y, 
                        self.main_window_info['client_width'], self.main_window_info['client_height'], 
                        self.main_templates['medal'], self.main_window_info['client_x'], self.main_window_info['client_y']
                    )

                elif self.main_components['rune_mode'].is_active:
                    # rune模式邏輯
                    self.main_components['rune_mode'].handle(
                        screenshot, self.main_window_info['screen_region'], 
                        self.main_templates['medal'], self.main_templates['rune'], 
                        self.main_templates['direction'], self.main_templates['direction_masks'], 
                        self.main_window_info['client_width'], self.main_window_info['client_height'], 
                        self.main_components['search'], self.main_components['cliff_detection'], 
                        self.main_window_info['client_x'], self.main_window_info['client_y'], 
                        self.main_components['movement'], self.main_templates['change']
                    )

                # 移動狀態更新
                movement_completed = self.main_components['movement'].update()
                if (movement_completed and not self.main_components['search'].is_searching and 
                    self.main_components['search'].medal_lost_count == 0 and 
                    not self.main_components['rune_mode'].is_active and 
                    not self.main_components['rope_climbing'].is_climbing):
                    self.main_components['movement'].transition(
                        screenshot, player_x, player_y, 
                        self.main_window_info['client_width'], self.main_window_info['client_height'], 
                        self.main_components['monster_detector']
                    )
                # ★★★ 添加：被動技能檢查 - 與main.py保持一致 ★★★
                if self.main_components.get('passive_skills'):
                    self.main_components['passive_skills'].check_and_use_skills()

                time.sleep(config.DETECTION_INTERVAL)
                
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
            import config
            for key, value in config_updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
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
            if self.main_components:
                if 'movement' in self.main_components:
                    self.main_components['movement'].stop()
                if 'rune_mode' in self.main_components:
                    self.main_components['rune_mode'].exit()
                if 'rope_climbing' in self.main_components:
                    self.main_components['rope_climbing'].stop_climbing()
                if 'red_dot_detector' in self.main_components and self.main_components['red_dot_detector']:
                    self.main_components['red_dot_detector'].reset_detection()
                # ★★★ 添加：清理被動技能管理器 ★★★
                if 'passive_skills' in self.main_components and self.main_components['passive_skills']:
                    # 被動技能管理器通常不需要特殊清理，但可以記錄最終狀態
                    try:
                        stats = self.main_components['passive_skills'].get_simple_stats()
                        self._send_log(f"🎯 被動技能最終統計: 總使用{stats['total_uses']}次")
                    except:
                        pass
            
            self.main_components = None
            self.main_window_info = None
            self.main_templates = None
            
            # 清理認證令牌
            try:
                from core.auth_manager import get_auth_manager
                local_auth = get_auth_manager()
                local_auth.clear_session()
                self._send_log("🧹 認證令牌已清理")
            except Exception as e:
                self._send_log(f"⚠️ 清理認證令牌時發生錯誤: {str(e)}")
            
            # 清理環境變數
            if 'ARTALE_GUI_MODE' in os.environ:
                del os.environ['ARTALE_GUI_MODE']
            
            self._send_log("🧹 腳本資源清理完成")
            
        except Exception as e:
            self._send_log(f"⚠️ 清理資源時發生錯誤: {str(e)}")
    
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
        """更新GUI統計信息"""
        try:
            script_stats = stats_data['script_stats']
            performance_stats = stats_data['performance_stats']
            
            # 更新運行時間
            if script_stats['total_runtime'] > 0:
                runtime_str = str(timedelta(seconds=int(script_stats['total_runtime'])))
                self.gui.runtime_label.configure(text=f"運行時間: {runtime_str}")
            
            # 更新檢測次數
            if hasattr(self.gui, 'detection_label'):
                self.gui.detection_label.configure(text=f"檢測次數: {script_stats['detections']}")
            
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