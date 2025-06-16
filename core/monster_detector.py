"""
怪物檢測模組 - 處理怪物的檢測和攻擊邏輯
"""
import cv2
import os
import glob


class SimplifiedMonsterDetector:
    def __init__(self):
        self.monster_templates = []
        self.monster_templates_edges = []
        self.template_sizes = []
        self.template_categories = []

    def load_selected_monsters(self):
        """載入選定的怪物模板"""
        from config import ENABLED_MONSTERS, MONSTER_BASE_PATH
        
        monster_templates = []
        image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.webp']
        
        print(f"載入選定怪物: {ENABLED_MONSTERS}")
        
        for monster_name in ENABLED_MONSTERS:
            monster_folder = os.path.join(MONSTER_BASE_PATH, monster_name)
            
            if not os.path.exists(monster_folder):
                print(f"警告: 找不到怪物資料夾 {monster_name}")
                continue
            
            loaded_count = 0
            for ext in image_extensions:
                for file_path in glob.glob(os.path.join(monster_folder, ext)):
                    template = cv2.imread(file_path, cv2.IMREAD_COLOR)
                    if template is not None:
                        monster_templates.append(template)
                        loaded_count += 1
                        print(f"載入: {monster_name}/{os.path.basename(file_path)}")
            
            print(f"{monster_name}: 載入 {loaded_count} 張圖片")
        
        print(f"總計載入 {len(monster_templates)} 個怪物模板")
        return monster_templates
        
    def setup_templates(self, monster_templates=None):
        """設置怪物模板並分析尺寸"""
        # 如果沒有提供模板，就載入選定的怪物
        if monster_templates is None:
            monster_templates = self.load_selected_monsters()
            
        self.monster_templates = monster_templates
        self.monster_templates_edges = []
        self.template_sizes = []
        self.template_categories = []
        
        print("分析怪物模板尺寸...")
        for i, template in enumerate(monster_templates, 1):
            # 生成邊緣檢測模板
            edges = cv2.Canny(template, 50, 150)
            self.monster_templates_edges.append(edges)
            
            # 記錄模板尺寸
            h, w = template.shape[:2]
            self.template_sizes.append((w, h))
            
            # 簡化分類標準：140x140 以上為大型
            max_size = max(w, h)
            if max_size < 100:
                from config import SMALL_MONSTER_Y_TOLERANCE
                category = {
                    "type": "小型", 
                    "y_tolerance": SMALL_MONSTER_Y_TOLERANCE,
                    "jump_strategy": "conservative"
                }
            elif max_size < 140:
                from config import MEDIUM_MONSTER_Y_TOLERANCE
                category = {
                    "type": "中型", 
                    "y_tolerance": MEDIUM_MONSTER_Y_TOLERANCE,
                    "jump_strategy": "balanced"
                }
            else:  # >= 140 像素
                from config import LARGE_MONSTER_Y_TOLERANCE
                category = {
                    "type": "大型", 
                    "y_tolerance": LARGE_MONSTER_Y_TOLERANCE,
                    "jump_strategy": "selective"
                }
            
            self.template_categories.append(category)
            print(f"怪物模板 {i}: {w}x{h} ({category['type']}) - Y軸閾值: {category['y_tolerance']}px")
        
        print("已完成怪物模板分析")
        
    def get_detection_size(self, movement_state):
        """根據怪物模板尺寸決定檢測範圍"""
        from config import MIN_DETECTION_SIZE, MAX_DETECTION_SIZE
        
        if not self.template_sizes:
            return 400
            
        # 找出最大的模板尺寸
        max_template_size = max(max(w, h) for w, h in self.template_sizes)

        # 基礎檢測範圍
        from config import ATTACK_RANGE_X
        base_size = max(ATTACK_RANGE_X, max_template_size + 100)
        
        # 移動時適度增加範圍
        if movement_state:
            detection_size = base_size + 50
        else:
            detection_size = base_size
            
        # 限制範圍
        detection_size = max(MIN_DETECTION_SIZE, min(MAX_DETECTION_SIZE, detection_size))
        
        return detection_size

    def detect_monsters(self, screenshot, player_x, player_y, client_width, client_height, movement, cliff_detection, client_x, client_y):
        """智能Y軸限制的怪物檢測"""
        from core.utils import preprocess_screenshot, quick_attack_monster
        from config import Y_LAYER_THRESHOLD, JUMP_ATTACK_MODE
        
        detection_size = self.get_detection_size(movement.is_moving)
        
        region_x = max(0, min(player_x - detection_size // 2, client_width - detection_size))
        region_y = max(0, min(player_y - detection_size // 2, client_height - detection_size))
        
        region_x_end = min(region_x + detection_size, client_width)
        region_y_end = min(region_y + detection_size, client_height)
        actual_width = region_x_end - region_x
        actual_height = region_y_end - region_y
        
        detection_region = screenshot[region_y:region_y_end, region_x:region_x_end]
        
        if detection_region.size == 0:
            return False
        
        detection_region_edges = preprocess_screenshot(detection_region)
        
        # 簡化檢測邏輯 - 直接按順序檢測
        for i, template_edges in enumerate(self.monster_templates_edges, 1):
            category = self.template_categories[i-1]
            
            template_h, template_w = template_edges.shape[:2]
            if template_h > actual_height or template_w > actual_width:
                continue
            
            try:
                result = cv2.matchTemplate(detection_region_edges, template_edges, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                threshold = 0.3 if movement.is_moving else 0.35
                
                if max_val > threshold:
                    original_template_h, original_template_w = self.monster_templates[i-1].shape[:2]
                    monster_x = region_x + max_loc[0] + original_template_w // 2
                    monster_y = region_y + max_loc[1] + original_template_h // 2
                    y_diff = abs(monster_y - player_y)
                    
                    # 智能Y軸限制邏輯
                    monster_height_radius = original_template_h // 2
                    attack_tolerance = monster_height_radius + 50
                    max_attack_tolerance = min(attack_tolerance, Y_LAYER_THRESHOLD)
                    
                    if y_diff > max_attack_tolerance:
                        continue  # 跳過這個怪物
                    
                    # ★ 簡化輸出 - 只保留關鍵信息 ★
                    print(f"🎯 攻擊{category['type']}怪物 (匹配度:{max_val:.2f}, Y差:{y_diff}px)")
                    
                    # 預計算攻擊參數
                    attack_direction = 'left' if monster_x < player_x else 'right'
                    monster_above = monster_y < player_y
                    
                    # 預判攻擊類型
                    attack_type = 'normal'
                    
                    if JUMP_ATTACK_MODE != 'disabled' and monster_above and y_diff > category['y_tolerance']:
                        if category['jump_strategy'] == "conservative" and y_diff > category['y_tolerance']:
                            attack_type = 'jump'
                        elif category['jump_strategy'] == "balanced" and y_diff > category['y_tolerance']:
                            attack_type = 'jump'
                        elif category['jump_strategy'] == "selective" and y_diff > category['y_tolerance'] and y_diff > 50:
                            attack_type = 'jump'
                    
                    quick_attack_monster(monster_x, monster_y, player_x, player_y, movement, cliff_detection, attack_direction, attack_type)
                    return True
                    
            except cv2.error as e:
                continue
        
        return False

    def scan_for_direction(self, screenshot, player_x, player_y, client_width, client_height, movement):
        """帶智能Y軸限制的遠距離掃描"""
        from core.utils import preprocess_screenshot
        from config import Y_LAYER_THRESHOLD
        
        # 動態掃描範圍
        if self.template_sizes:
            max_monster_height = max(h for w, h in self.template_sizes)
            scan_height = max(300, min(600, max_monster_height * 3))
        else:
            scan_height = 400
        
        scan_width = 1500
        
        region_x = max(0, min(player_x - scan_width // 2, client_width - scan_width))
        region_y = max(0, min(player_y - scan_height // 2, client_height - scan_height))
        
        region_x_end = min(region_x + scan_width, client_width)
        region_y_end = min(region_y + scan_height, client_height)
        actual_width = region_x_end - region_x
        actual_height = region_y_end - region_y
        
        detection_region = screenshot[region_y:region_y_end, region_x:region_x_end]
        
        if detection_region.size == 0:
            return None, None
        
        detection_region_edges = preprocess_screenshot(detection_region)
        
        best_val = 0
        best_direction = None
        best_monster_y = None
        valid_monsters_found = 0
        total_monsters_detected = 0
        
        # ★ 簡化掃描輸出 ★
        # print(f"🔍 遠距離掃描範圍: {actual_width}x{actual_height}")
        
        for i, template_edges in enumerate(self.monster_templates_edges, 1):
            template_h, template_w = template_edges.shape[:2]
            if template_h > actual_height or template_w > actual_width:
                continue
            
            try:
                result = cv2.matchTemplate(detection_region_edges, template_edges, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(result)
                
                threshold = 0.3 if movement.is_moving else 0.35
                
                if max_val > threshold:
                    total_monsters_detected += 1
                    
                    original_template = self.monster_templates[i-1]
                    original_template_h, original_template_w = original_template.shape[:2]
                    category = self.template_categories[i-1]
                    
                    monster_x = region_x + max_loc[0] + original_template_w // 2
                    monster_y = region_y + max_loc[1] + original_template_h // 2
                    
                    y_diff = abs(monster_y - player_y)
                    
                    monster_height_radius = original_template_h // 2
                    attack_tolerance = monster_height_radius + 50
                    max_attack_tolerance = min(attack_tolerance, Y_LAYER_THRESHOLD)
                    
                    if y_diff <= max_attack_tolerance:
                        valid_monsters_found += 1
                        
                        if max_val > best_val:
                            best_val = max_val
                            best_direction = 'left' if monster_x < player_x else 'right'
                            best_monster_y = monster_y
            
            except cv2.error as e:
                continue
        
        # ★ 簡化掃描結果輸出 ★
        if valid_monsters_found > 0:
            print(f"🔍 發現遠距怪物 → {best_direction} (匹配度:{best_val:.2f})")
        # 移除其他詳細統計信息
        
        return best_direction, best_monster_y