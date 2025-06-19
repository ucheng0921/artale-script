"""
紅點偵測模組 - 處理玩家出現時的紅點檢測和換頻邏輯
"""
import cv2
import time
import random
import os


class RedDotDetector:
    def __init__(self):
        self.red_template = None
        self.is_detecting = False
        self.detection_start_time = 0
        self.required_detection_time = 0
        self.detection_count = 0
        self.last_detection_time = 0
        self.detection_interval = 1.0  # 每秒記錄一次
        
        # 偵測狀態
        self.red_dot_found = False
        self.consecutive_detections = 0
        
        # ★★★ 新增：紅點消失追踪 ★★★
        self.consecutive_no_detections = 0  # 連續未檢測到紅點的次數
        self.max_no_detections = 3  # 連續未檢測到3次就重置 (可調整)
        self.last_red_dot_time = 0  # 最後一次檢測到紅點的時間
        
        # 調試標誌
        self.debug_red_detection = True
        
    def load_red_template(self, red_path):
        """載入紅點模板 - 修改版支援多模板"""
        # 先嘗試載入主要模板（保持原有邏輯）
        self.red_template = cv2.imread(red_path, cv2.IMREAD_COLOR)
        if self.red_template is None:
            print(f"❌ 無法載入紅點模板: {red_path}")
            return False
        else:
            print(f"✅ 成功載入紅點模板: {red_path}")
            if self.debug_red_detection:
                h, w = self.red_template.shape[:2]
                print(f"🔧 [調試] 紅點模板尺寸: {w}x{h}")
        
        # 初始化模板列表
        self.red_templates = [self.red_template]
        
        # 檢查是否啟用多紅點模式
        try:
            from config import ENABLE_MULTI_RED_DOT
            if ENABLE_MULTI_RED_DOT:
                # 自動載入 red1.png ~ red4.png
                base_dir = os.path.dirname(red_path)
                for i in range(1, 5):  # red1.png 到 red4.png
                    extra_path = os.path.join(base_dir, f'red{i}.png')
                    if os.path.exists(extra_path):
                        extra_template = cv2.imread(extra_path, cv2.IMREAD_COLOR)
                        if extra_template is not None:
                            self.red_templates.append(extra_template)
                            h, w = extra_template.shape[:2]
                            print(f"✅ 載入額外紅點模板: red{i}.png ({w}x{h})")
                        else:
                            print(f"⚠️ 無法讀取: red{i}.png")
                    else:
                        print(f"⚠️ 檔案不存在: red{i}.png")
                
                print(f"📊 總計載入 {len(self.red_templates)} 個紅點模板")
        except ImportError:
            # 如果沒有 ENABLE_MULTI_RED_DOT 設定，只使用單一模板
            print("使用單一紅點模板模式")
        
        # 載入config中的重置閾值（保持原有邏輯）
        try:
            from config import RED_DOT_RESET_THRESHOLD
            self.max_no_detections = RED_DOT_RESET_THRESHOLD
            print(f"🔧 [Config] 載入紅點消失重置閾值: {RED_DOT_RESET_THRESHOLD} 次")
        except ImportError:
            print("⚠️ 無法載入config重置閾值，使用預設值 3 次")
        
        return True

    def detect_red_dot(self, screenshot, client_width, client_height):
        """檢測左上角的紅點 - 修改版支援多模板"""
        # 使用模板列表而不是單一模板
        templates_to_check = getattr(self, 'red_templates', None)
        if not templates_to_check:
            # 向後相容：如果沒有模板列表，使用單一模板
            if self.red_template is None:
                return False
            templates_to_check = [self.red_template]
        
        # 定義左上角檢測區域
        detection_width = min(300, client_width // 3)
        detection_height = min(200, client_height // 2)
        
        # 提取左上角區域
        top_left_region = screenshot[0:detection_height, 0:detection_width]
        
        if top_left_region.size == 0:
            if self.debug_red_detection:
                print("🔧 [調試] 左上角檢測區域為空")
            return False
        
        try:
            # 從config載入檢測閾值
            try:
                from config import RED_DOT_DETECTION_THRESHOLD
                threshold = RED_DOT_DETECTION_THRESHOLD
            except ImportError:
                threshold = 0.7
                if self.debug_red_detection:
                    print("⚠️ 無法載入config閾值設定，使用預設值 0.7")
            
            # 檢測所有模板
            best_match_val = 0
            best_template_index = -1
            
            for i, template in enumerate(templates_to_check):
                try:
                    result = cv2.matchTemplate(top_left_region, template, cv2.TM_CCOEFF_NORMED)
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > best_match_val:
                        best_match_val = max_val
                        best_template_index = i
                        
                except cv2.error as e:
                    if self.debug_red_detection:
                        print(f"🔧 [調試] 模板 {i+1} 匹配錯誤: {e}")
                    continue
            
            if self.debug_red_detection and best_match_val > 0.4:
                template_name = "red.png" if best_template_index == 0 else f"red{best_template_index}.png"
                print(f"🔧 [調試] 紅點匹配度: {best_match_val:.3f} ({template_name}, 閾值: {threshold})")
            
            if best_match_val >= threshold:
                if self.debug_red_detection:
                    template_name = "red.png" if best_template_index == 0 else f"red{best_template_index}.png"
                    print(f"🔴 檢測到紅點！模板: {template_name}, 匹配度: {best_match_val:.3f}")
                return True
            
            return False
            
        except cv2.error as e:
            if self.debug_red_detection:
                print(f"🔧 [調試] 紅點檢測錯誤: {e}")
            return False
    
    def start_detection_timer(self):
        """開始紅點檢測計時"""
        if self.is_detecting:
            return  # 已經在檢測中
        
        # 導入配置參數
        try:
            from config import RED_DOT_MIN_TIME, RED_DOT_MAX_TIME
            min_time = RED_DOT_MIN_TIME
            max_time = RED_DOT_MAX_TIME
        except ImportError:
            # 如果無法導入配置，使用預設值
            min_time = 15.0
            max_time = 20.0
            print("⚠️ 無法載入config設定，使用預設時間範圍 15-20 秒")
        
        self.is_detecting = True
        self.detection_start_time = time.time()
        self.required_detection_time = random.uniform(min_time, max_time)  # 使用config的設定
        self.detection_count = 0
        self.last_detection_time = time.time()
        
        print(f"🚨 開始紅點檢測計時: {self.required_detection_time:.1f} 秒")
        print(f"⏱️ 每秒記錄一次，達到時間後執行換頻邏輯 (設定範圍: {min_time}-{max_time}秒)")
    
    def update_detection_timer(self):
        """更新檢測計時器"""
        if not self.is_detecting:
            return False
        
        current_time = time.time()
        
        # 檢查是否到了記錄時間
        if current_time - self.last_detection_time >= self.detection_interval:
            self.detection_count += 1
            self.last_detection_time = current_time
            
            elapsed_time = current_time - self.detection_start_time
            remaining_time = self.required_detection_time - elapsed_time
            
            print(f"📊 紅點檢測記錄 #{self.detection_count}: 已過 {elapsed_time:.1f}秒, 剩餘 {remaining_time:.1f}秒")
        
        # 檢查是否達到要求時間
        if current_time - self.detection_start_time >= self.required_detection_time:
            total_elapsed = current_time - self.detection_start_time
            print(f"⏰ 紅點檢測時間達到！總計: {total_elapsed:.1f} 秒 (記錄次數: {self.detection_count})")
            print("🔄 觸發換頻邏輯...")
            self.reset_detection()
            return True
        
        return False
    
    def reset_detection(self):
        """重置檢測狀態"""
        if self.debug_red_detection:
            print("🔧 [調試] 重置紅點檢測狀態")
        
        self.is_detecting = False
        self.detection_start_time = 0
        self.required_detection_time = 0
        self.detection_count = 0
        self.last_detection_time = 0
        self.red_dot_found = False
        self.consecutive_detections = 0
        
        # ★★★ 新增：重置消失追踪 ★★★
        self.consecutive_no_detections = 0
        self.last_red_dot_time = 0
    
    def handle_red_dot_detection(self, screenshot, client_width, client_height):
        """處理紅點檢測邏輯 - 修復版（紅點消失會重置計時）"""
        # 檢測紅點
        red_detected = self.detect_red_dot(screenshot, client_width, client_height)
        current_time = time.time()
        
        if red_detected:
            # ★★★ 檢測到紅點 ★★★
            self.last_red_dot_time = current_time
            self.consecutive_no_detections = 0  # 重置消失計數
            
            if not self.is_detecting:
                # 第一次檢測到紅點，開始計時
                print("🚨 首次檢測到玩家紅點！")
                self.start_detection_timer()
                self.red_dot_found = True
                self.consecutive_detections = 1
            else:
                # 持續檢測到紅點
                self.consecutive_detections += 1
                if self.debug_red_detection and self.consecutive_detections % 5 == 0:
                    print(f"🔴 持續檢測到紅點 (連續 {self.consecutive_detections} 次)")
        else:
            # ★★★ 沒有檢測到紅點 ★★★
            if self.is_detecting:
                self.consecutive_no_detections += 1
                
                # ★★★ 關鍵邏輯：檢查是否應該重置計時器 ★★★
                if self.consecutive_no_detections >= self.max_no_detections:
                    time_since_last_red = current_time - self.last_red_dot_time
                    print(f"⚪ 紅點已消失 {self.consecutive_no_detections} 次 (連續 {time_since_last_red:.1f} 秒未檢測到)")
                    print("🔄 紅點消失太久，重置檢測計時器，避免誤判換頻")
                    self.reset_detection()
                    return False
                else:
                    # 紅點暫時消失，但還在容忍範圍內
                    if self.debug_red_detection:
                        elapsed = current_time - self.detection_start_time
                        remaining = self.required_detection_time - elapsed
                        time_since_last_red = current_time - self.last_red_dot_time
                        print(f"⚪ 紅點暫時消失 ({self.consecutive_no_detections}/{self.max_no_detections}次)")
                        print(f"   距離上次檢測到: {time_since_last_red:.1f}秒, 計時剩餘: {remaining:.1f}秒")
            
            self.consecutive_detections = 0
        
        # 更新計時器
        if self.is_detecting:
            should_change_channel = self.update_detection_timer()
            if should_change_channel:
                return True
        
        return False
    
    def get_detection_status(self):
        """獲取檢測狀態信息"""
        if not self.is_detecting:
            return "紅點檢測: 未啟動"
        
        current_time = time.time()
        elapsed_time = current_time - self.detection_start_time
        remaining_time = self.required_detection_time - elapsed_time
        time_since_last_red = current_time - self.last_red_dot_time if self.last_red_dot_time > 0 else 0
        
        status = f"紅點檢測中: {elapsed_time:.1f}/{self.required_detection_time:.1f}秒"
        status += f" (記錄次數: {self.detection_count})"
        
        if self.red_dot_found:
            status += f" [連續檢測: {self.consecutive_detections}次]"
            if self.consecutive_no_detections > 0:
                status += f" [消失: {self.consecutive_no_detections}/{self.max_no_detections}次]"
                status += f" [距上次: {time_since_last_red:.1f}秒]"
        
        return status
    
    def force_trigger_channel_change(self):
        """強制觸發換頻邏輯 (調試用)"""
        print("🚨 手動觸發換頻邏輯")
        self.reset_detection()
        return True
    
    def adjust_detection_time_range(self, min_time=None, max_time=None):
        """調整檢測時間範圍"""
        # 如果沒有提供參數，嘗試從config載入
        if min_time is None or max_time is None:
            try:
                from config import RED_DOT_MIN_TIME, RED_DOT_MAX_TIME
                if min_time is None:
                    min_time = RED_DOT_MIN_TIME
                if max_time is None:
                    max_time = RED_DOT_MAX_TIME
                print(f"🔧 從config載入檢測時間範圍: {min_time}-{max_time} 秒")
            except ImportError:
                if min_time is None:
                    min_time = 15.0
                if max_time is None:
                    max_time = 20.0
                print(f"⚠️ 無法載入config，使用預設時間範圍: {min_time}-{max_time} 秒")
        else:
            print(f"🔧 手動調整紅點檢測時間範圍: {min_time}-{max_time} 秒")
        
        # 如果正在檢測中，更新當前的要求時間
        if self.is_detecting:
            old_required_time = self.required_detection_time
            self.required_detection_time = random.uniform(min_time, max_time)
            print(f"   當前檢測時間調整: {old_required_time:.1f} -> {self.required_detection_time:.1f} 秒")
    
    def toggle_debug(self):
        """切換調試模式"""
        self.debug_red_detection = not self.debug_red_detection
        print(f"🔧 紅點檢測調試模式: {'開啟' if self.debug_red_detection else '關閉'}")
    
    def set_detection_interval(self, interval):
        """設置檢測間隔"""
        old_interval = self.detection_interval
        self.detection_interval = interval
        print(f"🔧 紅點檢測記錄間隔: {old_interval}秒 -> {interval}秒")
    
    def set_reset_threshold(self, threshold):
        """設置重置閾值 - 連續多少次未檢測到紅點就重置計時器"""
        old_threshold = self.max_no_detections
        self.max_no_detections = threshold
        print(f"🔧 調整紅點消失重置閾值: {old_threshold} -> {threshold} 次")
        print(f"   現在連續 {threshold} 次未檢測到紅點就會重置計時器")
    
    def get_reset_threshold_info(self):
        """獲取重置閾值信息"""
        return f"紅點消失重置閾值: {self.max_no_detections} 次 (當前消失次數: {self.consecutive_no_detections})"
    
    def get_template_info(self):
        """獲取模板信息"""
        if self.red_template is None:
            return "紅點模板: 未載入"
        
        h, w = self.red_template.shape[:2]
        return f"紅點模板: {w}x{h} 像素"
    
    def get_current_config(self):
        """獲取當前配置信息 - 用於驗證config是否正確載入"""
        try:
            from config import (ENABLE_RED_DOT_DETECTION, RED_DOT_PATH, 
                              RED_DOT_MIN_TIME, RED_DOT_MAX_TIME, 
                              RED_DOT_DETECTION_THRESHOLD)
            
            config_info = {
                'enabled': ENABLE_RED_DOT_DETECTION,
                'path': RED_DOT_PATH,
                'min_time': RED_DOT_MIN_TIME,
                'max_time': RED_DOT_MAX_TIME,
                'threshold': RED_DOT_DETECTION_THRESHOLD
            }
            
            print("🔧 [Config驗證] 成功載入紅點檢測配置:")
            print(f"   啟用狀態: {config_info['enabled']}")
            print(f"   圖片路徑: {config_info['path']}")
            print(f"   時間範圍: {config_info['min_time']}-{config_info['max_time']} 秒")
            print(f"   檢測閾值: {config_info['threshold']}")
            
            return config_info
            
        except ImportError as e:
            print(f"❌ [Config驗證] 無法載入配置: {e}")
            return None
    
    def test_config_loading(self):
        """測試config載入功能"""
        print("🧪 測試config配置載入...")
        config = self.get_current_config()
        
        if config:
            # 測試時間設定
            print("\n🧪 測試時間範圍設定...")
            test_time = random.uniform(config['min_time'], config['max_time'])
            print(f"   根據config生成的隨機時間: {test_time:.1f} 秒")
            
            # 測試閾值設定
            print(f"\n🧪 測試檢測閾值設定...")
            print(f"   當前閾值: {config['threshold']}")
            
            return True
        else:
            print("❌ Config測試失敗")
            return False