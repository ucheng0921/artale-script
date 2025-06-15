"""
增強移動模組 - 處理跳躍和位移技能移動 (修復版 - 解決按鍵殘留)
"""
import time
import random
import pyautogui
from config import JUMP_KEY


class EnhancedMovement:
    def __init__(self):
        self.last_dash_time = 0  # 上次使用位移技能的時間
        self.last_jump_time = 0  # 上次跳躍的時間
        self.current_keys_pressed = []  # 當前按下的按鍵列表
        self.protected_keys = []  # 受保護的按鍵（攻擊時不會被釋放）
        
    def can_use_dash(self):
        """檢查是否可以使用位移技能（冷卻檢查）"""
        # 導入配置（避免循環導入）
        from config import ENABLE_ENHANCED_MOVEMENT, ENABLE_DASH_MOVEMENT, DASH_SKILL_COOLDOWN
        
        if not ENABLE_ENHANCED_MOVEMENT or not ENABLE_DASH_MOVEMENT:
            return False
        
        current_time = time.time()
        if current_time - self.last_dash_time < DASH_SKILL_COOLDOWN:
            remaining = DASH_SKILL_COOLDOWN - (current_time - self.last_dash_time)
            print(f"🕒 位移技能冷卻中，剩餘 {remaining:.1f} 秒")
            return False
        return True
    
    def can_jump(self):
        """檢查是否可以跳躍（避免跳躍過於頻繁）"""
        # 導入配置（避免循環導入）
        from config import ENABLE_ENHANCED_MOVEMENT, ENABLE_JUMP_MOVEMENT
        
        if not ENABLE_ENHANCED_MOVEMENT or not ENABLE_JUMP_MOVEMENT:
            return False
        
        current_time = time.time()
        # 跳躍間隔較短，但避免過於頻繁
        if current_time - self.last_jump_time < 0.5:  # 0.5秒跳躍間隔
            return False
        return True
    
    def determine_movement_type(self):
        """決定移動類型：normal, jump, dash"""
        # 導入配置（避免循環導入）
        from config import (ENABLE_ENHANCED_MOVEMENT, ENABLE_JUMP_MOVEMENT, ENABLE_DASH_MOVEMENT,
                           MOVEMENT_PRIORITY, JUMP_MOVEMENT_CHANCE, DASH_MOVEMENT_CHANCE)
        
        if not ENABLE_ENHANCED_MOVEMENT:
            return 'normal'
        
        # 生成隨機數決定移動類型
        random_value = random.random()
        
        # 檢查各種移動類型的可用性
        available_types = ['normal']  # 普通移動總是可用
        
        if ENABLE_JUMP_MOVEMENT and self.can_jump():
            available_types.append('jump')
        
        if ENABLE_DASH_MOVEMENT and self.can_use_dash():
            available_types.append('dash')
        
        # 根據優先級和機率決定移動類型
        cumulative_chance = 0
        
        # 計算各類型的實際機率
        for movement_type in MOVEMENT_PRIORITY:
            if movement_type not in available_types:
                continue
                
            if movement_type == 'jump':
                cumulative_chance += JUMP_MOVEMENT_CHANCE
                if random_value < cumulative_chance:
                    return 'jump'
            elif movement_type == 'dash':
                cumulative_chance += DASH_MOVEMENT_CHANCE
                if random_value < cumulative_chance:
                    return 'dash'
        
        # 預設返回普通移動
        return 'normal'
    
    def execute_movement(self, direction, movement_type, duration):
        """執行增強移動 - 修復版，確保按鍵狀態正確"""
        print(f"🏃 執行{self.get_movement_name(movement_type)}移動: {direction} ({duration:.1f}秒)")
        
        # ★★★ 修復1：詳細的移動前狀態檢查 ★★★
        print(f"🔧 移動前狀態: {self.current_keys_pressed}")
        
        # ★★★ 修復2：強制清空之前的按鍵，確保釋放成功 ★★★
        self.release_all_keys_with_verification()
        self.protected_keys = []  # 清空保護列表
        
        if movement_type == 'normal':
            # 普通移動：只按方向鍵
            pyautogui.keyDown(direction)
            self.current_keys_pressed = [direction]
            print(f"✅ 普通移動設置完成: {self.current_keys_pressed}")
            
        elif movement_type == 'jump':
            # 跳躍移動：持續按住方向鍵 + 空白鍵
            print(f"🦘 持續跳躍移動: {direction} + JUMP_KEY (持續按住)")
            pyautogui.keyDown(direction)
            pyautogui.keyDown(JUMP_KEY)
            self.current_keys_pressed = [direction, JUMP_KEY]
            self.last_jump_time = time.time()
            print(f"✅ 跳躍移動設置完成: {self.current_keys_pressed}")
            
        elif movement_type == 'dash':
            # 位移技能移動：持續按住方向鍵 + 位移技能鍵
            from config import DASH_SKILL_KEY
            print(f"⚡ 持續位移技能移動: {direction} + {DASH_SKILL_KEY} (持續按住)")
            pyautogui.keyDown(direction)
            pyautogui.keyDown(DASH_SKILL_KEY)
            self.current_keys_pressed = [direction, DASH_SKILL_KEY]
            self.last_dash_time = time.time()
            print(f"✅ 位移技能移動設置完成: {self.current_keys_pressed}")
        
        return direction  # 返回當前的主要移動方向
    
    def release_all_keys_with_verification(self, exclude_protected=True):
        """★★★ 修復版：釋放所有按鍵並驗證釋放成功 ★★★"""
        print(f"🔧 開始釋放按鍵，當前狀態: {self.current_keys_pressed}")
        
        keys_to_release = []
        
        for key in self.current_keys_pressed[:]:  # 複製列表以避免修改時出錯
            # 檢查是否需要保護此按鍵
            if exclude_protected and key in self.protected_keys:
                print(f"🛡️ 保護按鍵不釋放: {key}")
                continue
            
            keys_to_release.append(key)
        
        # ★★★ 關鍵修復：逐個釋放並驗證 ★★★
        successfully_released = []
        for key in keys_to_release:
            try:
                print(f"🔓 正在釋放按鍵: {key}")
                pyautogui.keyUp(key)
                
                # 短暫等待確保按鍵釋放生效
                time.sleep(0.01)
                
                # 從列表中移除
                if key in self.current_keys_pressed:
                    self.current_keys_pressed.remove(key)
                    successfully_released.append(key)
                    print(f"✅ 成功釋放按鍵: {key}")
                else:
                    print(f"⚠️ 按鍵 {key} 不在當前列表中")
                    
            except Exception as e:
                print(f"❌ 釋放按鍵 {key} 失敗: {e}")
        
        print(f"🔧 釋放完成，成功釋放: {successfully_released}")
        print(f"🔧 剩餘按鍵: {self.current_keys_pressed}")
        
        # ★★★ 新增：額外安全檢查，確保沒有遺漏 ★★★
        if self.current_keys_pressed:
            print(f"⚠️ 警告：仍有未釋放的按鍵: {self.current_keys_pressed}")
            # 強制清理
            for remaining_key in self.current_keys_pressed[:]:
                try:
                    pyautogui.keyUp(remaining_key)
                    print(f"🚨 強制釋放遺漏按鍵: {remaining_key}")
                except:
                    pass
            self.current_keys_pressed.clear()
    
    def release_all_keys(self, exclude_protected=True):
        """★★★ 舊方法重定向到新方法 ★★★"""
        return self.release_all_keys_with_verification(exclude_protected)
    
    def protect_keys(self, keys_list):
        """★★★ 新增：保護特定按鍵不被釋放 ★★★"""
        self.protected_keys = keys_list.copy() if keys_list else []
        print(f"🛡️ 設置保護按鍵: {self.protected_keys}")
    
    def clear_protection(self):
        """★★★ 新增：清除按鍵保護 ★★★"""
        self.protected_keys = []
        print("🔓 清除所有按鍵保護")
    
    def stop_movement(self, direction):
        """停止移動（釋放所有按鍵）"""
        print(f"🛑 停止移動: 釋放所有按鍵")
        self.clear_protection()  # 停止時清除保護
        self.release_all_keys_with_verification(exclude_protected=False)  # 強制釋放所有按鍵
    
    def get_movement_name(self, movement_type):
        """獲取移動類型的中文名稱"""
        names = {
            'normal': '普通',
            'jump': '跳躍',
            'dash': '位移技能'
        }
        return names.get(movement_type, '未知')
    
    def update_movement(self, movement_type):
        """持續更新移動狀態（用於處理持續技能）"""
        current_time = time.time()
        
        if movement_type == 'jump':
            # 跳躍移動中，檢查是否需要重新跳躍
            if current_time - self.last_jump_time > 0.8:  # 每0.8秒重新跳躍
                if JUMP_KEY in self.current_keys_pressed:
                    print("🦘 重新觸發跳躍")
                    pyautogui.keyUp(JUMP_KEY)
                    time.sleep(0.05)  # 短暫釋放
                    pyautogui.keyDown(JUMP_KEY)
                    self.last_jump_time = current_time
                    
        elif movement_type == 'dash':
            # 位移技能移動中，檢查是否需要重新觸發技能
            from config import DASH_SKILL_KEY
            if current_time - self.last_dash_time > 1.0:  # 每1秒重新觸發位移技能
                if DASH_SKILL_KEY in self.current_keys_pressed:
                    print("⚡ 重新觸發位移技能")
                    pyautogui.keyUp(DASH_SKILL_KEY)
                    time.sleep(0.05)  # 短暫釋放
                    pyautogui.keyDown(DASH_SKILL_KEY)
                    self.last_dash_time = current_time
    
    # ★★★ 新增：設置按鍵狀態的方法（用於攻擊後同步狀態）★★★
    def set_keys_pressed(self, keys_list):
        """設置當前按下的按鍵列表（用於攻擊後狀態同步）"""
        self.current_keys_pressed = keys_list.copy() if keys_list else []
        print(f"🔄 同步按鍵狀態: {self.current_keys_pressed}")
    
    def add_key_pressed(self, key):
        """添加一個按下的按鍵到列表中"""
        if key not in self.current_keys_pressed:
            self.current_keys_pressed.append(key)
            print(f"➕ 添加按鍵: {key}, 當前狀態: {self.current_keys_pressed}")
    
    def remove_key_pressed(self, key):
        """從列表中移除一個按鍵"""
        if key in self.current_keys_pressed:
            self.current_keys_pressed.remove(key)
            print(f"➖ 移除按鍵: {key}, 當前狀態: {self.current_keys_pressed}")
    
    def is_key_pressed(self, key):
        """檢查某個按鍵是否正在按下"""
        return key in self.current_keys_pressed
    
    # ★★★ 新增：狀態診斷方法 ★★★
    def diagnose_key_state(self):
        """診斷當前按鍵狀態"""
        print(f"🔍 按鍵狀態診斷:")
        print(f"   記錄的按鍵: {self.current_keys_pressed}")
        print(f"   保護的按鍵: {self.protected_keys}")
        print(f"   上次跳躍時間: {self.last_jump_time}")
        print(f"   上次位移時間: {self.last_dash_time}")
    
    def force_release_specific_key(self, key):
        """強制釋放特定按鍵"""
        try:
            pyautogui.keyUp(key)
            if key in self.current_keys_pressed:
                self.current_keys_pressed.remove(key)
            print(f"🚨 強制釋放特定按鍵: {key}")
            return True
        except Exception as e:
            print(f"❌ 強制釋放 {key} 失敗: {e}")
            return False