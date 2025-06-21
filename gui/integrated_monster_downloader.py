"""
整合式怪物下載器 - 用於配置面板中的輕量級下載功能（修正版）
保存為: gui/integrated_monster_downloader.py
"""
import customtkinter as ctk
import tkinter as tk
import threading
import requests
import json
import zipfile
import io
import cv2
import numpy as np
from pathlib import Path
import re
import os
import time

class IntegratedMonsterDownloader:
    """整合式怪物下載器類"""
    
    def __init__(self, parent_frame, config_manager=None, on_download_complete=None, on_data_loaded=None):
        self.parent = parent_frame
        self.config_manager = config_manager
        self.on_download_complete = on_download_complete  # 下載完成回調
        self.on_data_loaded = on_data_loaded  # 數據載入完成回調
        
        # API 設置
        self.BASE_URL = "https://maplestory.io"
        self.DEFAULT_REGION = "TMS"
        self.DEFAULT_VERSION = "209"
        
        # 怪物資料快取
        self.all_mobs = []
        self.english_names = {}
        self.filtered_mobs = []
        
        # 下載狀態
        self.is_downloading = False
        
        # 創建界面
        self.create_widgets()
        
        # 載入怪物資料
        self.load_monster_data_async()
    
    def create_widgets(self):
        """創建界面組件"""
        # 搜尋區域
        search_frame = ctk.CTkFrame(self.parent)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        # 搜尋輸入框
        search_input_frame = ctk.CTkFrame(search_frame)
        search_input_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(search_input_frame, text="搜尋:", width=60).pack(side="left", padx=(5, 2), pady=5)
        
        self.search_entry = ctk.CTkEntry(
            search_input_frame,
            placeholder_text="輸入怪物名稱...",
            width=200
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # 清除搜尋按鈕
        clear_button = ctk.CTkButton(
            search_input_frame,
            text="清除",
            command=self.clear_search,
            width=50,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        clear_button.pack(side="right", padx=(2, 5), pady=5)
        
        # 狀態標籤
        self.status_label = ctk.CTkLabel(
            search_frame,
            text="載入中...",
            font=ctk.CTkFont(size=10),
            text_color="orange"
        )
        self.status_label.pack(pady=2)
        
        # 怪物列表區域
        self.monster_list_frame = ctk.CTkScrollableFrame(
            self.parent,
            height=200,
            label_text="選擇要下載的怪物："
        )
        self.monster_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 存儲複選框
        self.monster_checkboxes = {}
        
        # 下載控制區域
        download_frame = ctk.CTkFrame(self.parent)
        download_frame.pack(fill="x", padx=5, pady=5)
        
        # 下載按鈕
        self.download_button = ctk.CTkButton(
            download_frame,
            text="📥 下載選中怪物",
            command=self.start_download,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.download_button.pack(side="left", padx=5, pady=5)
        
        # 下載選項
        self.skip_death_var = ctk.BooleanVar(value=True)
        skip_death_checkbox = ctk.CTkCheckBox(
            download_frame,
            text="跳過死亡動畫",
            variable=self.skip_death_var,
            font=ctk.CTkFont(size=10)
        )
        skip_death_checkbox.pack(side="left", padx=5, pady=5)
        
        # 翻轉說明
        flip_info_label = ctk.CTkLabel(
            download_frame,
            text="💡 自動生成水平翻轉圖",
            font=ctk.CTkFont(size=9),
            text_color="cyan"
        )
        flip_info_label.pack(side="right", padx=5, pady=5)
        
        # 小型日誌區域
        log_frame = ctk.CTkFrame(self.parent)
        log_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        ctk.CTkLabel(log_frame, text="下載日誌:", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5, pady=(5, 0))
        
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=60,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=9)
        )
        self.log_text.pack(fill="x", padx=5, pady=(0, 5))
    
    def get_save_path(self):
        """獲取保存路徑"""
        try:
            if self.config_manager:
                monster_base_path = self.config_manager.get_config('MONSTER_BASE_PATH')
                if monster_base_path:
                    return monster_base_path
            
            # 使用默認路徑
            return os.path.join('.', 'assets', 'game_resources', 'monsters')
        except:
            return './monsters'
    
    def load_monster_data_async(self):
        """異步載入怪物資料"""
        def load_data():
            try:
                self.log("🔄 正在載入怪物資料...")
                
                # 載入英文名稱對照
                self.english_names = self.get_english_names()
                
                # 載入怪物資料
                self.all_mobs = self.get_all_mobs()
                
                if self.all_mobs:
                    self.log(f"✅ 成功載入 {len(self.all_mobs)} 個怪物資料")
                    
                    # 在主線程中更新UI
                    self.parent.after(0, self.update_ui_after_loading)
                else:
                    self.log("❌ 載入怪物資料失敗")
                    self.parent.after(0, lambda: self.status_label.configure(text="載入失敗", text_color="red"))
                    
            except Exception as e:
                self.log(f"❌ 載入怪物資料錯誤: {str(e)}")
                self.parent.after(0, lambda: self.status_label.configure(text="載入錯誤", text_color="red"))
        
        # 在後台線程中載入
        threading.Thread(target=load_data, daemon=True).start()
    
    def update_ui_after_loading(self):
        """載入完成後更新UI"""
        self.status_label.configure(text="就緒", text_color="green")
        self.filtered_mobs = self.all_mobs.copy()
        self.refresh_monster_list()
        
        # 通知數據載入完成
        if self.on_data_loaded:
            self.on_data_loaded()
    
    def get_all_mobs(self):
        """獲取所有怪物資料"""
        url = f"{self.BASE_URL}/api/{self.DEFAULT_REGION}/{self.DEFAULT_VERSION}/mob"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            mob_data = response.json()
            
            return mob_data
            
        except Exception as e:
            self.log(f"❌ 獲取怪物資料失敗: {str(e)}")
            return []
    
    def get_english_names(self):
        """獲取英文怪物名稱對照"""
        url = f"{self.BASE_URL}/api/GMS/255/mob"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            english_mobs = response.json()
            
            # 建立 ID 到英文名稱的對照字典
            id_to_english = {}
            for mob in english_mobs:
                # 將英文名稱轉換為安全的檔案名稱格式
                safe_name = mob['name'].lower().replace(' ', '_').replace('-', '_')
                # 移除特殊字符
                safe_name = re.sub(r'[^\w_]', '', safe_name)
                id_to_english[mob['id']] = {
                    'safe_name': safe_name,
                    'original_name': mob['name']  # 保留原始英文名稱用於顯示
                }
            
            self.log(f"✅ 成功載入 {len(id_to_english)} 個英文怪物名稱")
            return id_to_english
            
        except Exception as e:
            self.log(f"⚠️ 獲取英文名稱失敗: {str(e)}")
            return {}
    
    def on_search_change(self, event=None):
        """搜尋框內容變化時的處理"""
        # 延遲搜尋以避免頻繁觸發
        if hasattr(self, '_search_timer'):
            self.parent.after_cancel(self._search_timer)
        
        self._search_timer = self.parent.after(300, self.search_monsters)
    
    def search_monsters(self, event=None):
        """搜尋怪物"""
        search_term = self.search_entry.get().strip()
        
        if not search_term:
            # 如果搜尋框為空，顯示所有怪物
            self.filtered_mobs = self.all_mobs.copy()
        else:
            # 搜尋匹配的怪物
            self.filtered_mobs = []
            for mob in self.all_mobs:
                if (search_term.lower() in mob["name"].lower() or 
                    search_term in mob["name"]):
                    self.filtered_mobs.append(mob)
        
        self.refresh_monster_list()
    
    def clear_search(self):
        """清除搜尋"""
        self.search_entry.delete(0, tk.END)
        self.filtered_mobs = self.all_mobs.copy()
        self.refresh_monster_list()
    
    def refresh_monster_list(self):
        """刷新怪物列表顯示"""
        # 清除舊的複選框
        for widget in self.monster_list_frame.winfo_children():
            widget.destroy()
        self.monster_checkboxes.clear()
        
        # 創建新的複選框 - 限制顯示前50個結果
        for mob in self.filtered_mobs[:50]:
            self.create_monster_checkbox(mob)
        
        if len(self.filtered_mobs) > 50:
            # 如果結果太多，顯示提示
            info_label = ctk.CTkLabel(
                self.monster_list_frame,
                text=f"... 還有 {len(self.filtered_mobs) - 50} 個結果，請使用更具體的搜尋條件",
                font=ctk.CTkFont(size=9),
                text_color="orange"
            )
            info_label.pack(pady=2)
    
    def create_monster_checkbox(self, mob):
        """為單個怪物創建複選框"""
        mob_frame = ctk.CTkFrame(self.monster_list_frame)
        mob_frame.pack(fill="x", padx=2, pady=1)
        
        # 複選框
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            mob_frame,
            text="",
            variable=var,
            width=20
        )
        checkbox.pack(side="left", padx=(5, 2), pady=2)
        
        # 怪物信息標籤
        english_data = self.english_names.get(mob['id'])
        if english_data:
            english_name = english_data['original_name']
            safe_filename = english_data['safe_name']
        else:
            english_name = f"mob_{mob['id']}"
            safe_filename = f"mob_{mob['id']}"
        
        # 顯示格式：中文名 -> 英文名 (等級: xxx)
        info_text = f"{mob['name']} -> {english_name} (等級: {mob['level']})"
        
        info_label = ctk.CTkLabel(
            mob_frame,
            text=info_text,
            font=ctk.CTkFont(size=9),
            anchor="w"
        )
        info_label.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        
        # 存儲複選框引用
        self.monster_checkboxes[mob['id']] = {
            'checkbox': checkbox,
            'var': var,
            'mob': mob,
            'frame': mob_frame,
            'safe_filename': safe_filename
        }
    
    def get_selected_monsters(self):
        """獲取選中的怪物"""
        selected = []
        for mob_id, data in self.monster_checkboxes.items():
            if data['var'].get():
                selected.append(data['mob'])
        return selected
    
    def start_download(self):
        """開始下載"""
        if self.is_downloading:
            self.log("⚠️ 下載已在進行中")
            return
        
        selected_monsters = self.get_selected_monsters()
        if not selected_monsters:
            self.log("❌ 請至少選擇一個怪物進行下載")
            return
        
        # 開始下載
        self.is_downloading = True
        self.download_button.configure(state="disabled", text="⏳ 下載中...")
        
        self.log(f"🚀 開始下載 {len(selected_monsters)} 個怪物...")
        
        # 在後台線程中下載
        threading.Thread(
            target=self.download_monsters_thread,
            args=(selected_monsters,),
            daemon=True
        ).start()
    
    def download_monsters_thread(self, monsters):
        """下載怪物線程"""
        try:
            total_count = len(monsters)
            success_count = 0
            error_count = 0
            
            for i, mob in enumerate(monsters, 1):
                if not self.is_downloading:
                    self.log("🛑 下載被停止")
                    break
                
                self.log(f"📥 ({i}/{total_count}): {mob['name']}")
                
                try:
                    # 確定檔案名稱 - 始終使用英文安全檔名
                    english_data = self.english_names.get(mob['id'])
                    if english_data:
                        safe_filename = english_data['safe_name']
                    else:
                        safe_filename = f"mob_{mob['id']}"
                    
                    # 下載怪物圖片
                    success = self.save_mob(mob['id'], safe_filename, mob['name'])
                    
                    if success:
                        success_count += 1
                        self.log(f"✅ 完成: {mob['name']}")
                    else:
                        error_count += 1
                        self.log(f"❌ 失敗: {mob['name']}")
                        
                except Exception as e:
                    error_count += 1
                    self.log(f"❌ {mob['name']}: {str(e)}")
                
                # 短暫延遲
                time.sleep(0.3)
            
            # 完成報告
            self.log(f"🎉 下載完成！成功: {success_count}, 失敗: {error_count}")
            
            # 通知下載完成
            if self.on_download_complete and success_count > 0:
                self.parent.after(0, self.on_download_complete)
            
        except Exception as e:
            self.log(f"❌ 下載過程發生錯誤: {str(e)}")
        finally:
            # 在主線程中更新UI
            self.parent.after(0, self.download_finished)
    
    def download_finished(self):
        """下載完成後的UI更新"""
        self.is_downloading = False
        self.download_button.configure(state="normal", text="📥 下載選中怪物")
    
    def save_mob(self, mob_id, folder_name, mob_name):
        """下載並保存怪物圖片（包含水平翻轉）- 修正版"""
        try:
            # 創建輸出目錄
            output_dir = Path(self.get_save_path()) / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 下載 URL
            download_url = f"{self.BASE_URL}/api/{self.DEFAULT_REGION}/{self.DEFAULT_VERSION}/mob/{mob_id}/download"
            
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            if len(response.content) < 100:
                return False
            
            # 處理 ZIP 檔案
            try:
                zip_bytes = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_bytes) as zip_file:
                    file_list = zip_file.namelist()
                    
                    if len(file_list) == 0:
                        return False
                    
                    index = 1
                    saved_count = 0
                    
                    for file_name in file_list:
                        # 跳過死亡動畫
                        if self.skip_death_var.get() and "die1" in file_name.lower():
                            continue
                        
                        try:
                            with zip_file.open(file_name) as file:
                                image_data = file.read()
                                
                                if len(image_data) == 0:
                                    continue
                                
                                np_arr = np.frombuffer(image_data, np.uint8)
                                img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
                                
                                if img is None:
                                    continue
                                
                                # 處理透明背景（替換為綠色）
                                processed_img = img.copy()
                                if len(processed_img.shape) >= 3 and processed_img.shape[2] == 4:
                                    alpha_channel = processed_img[:, :, 3]
                                    transparent_pixels = (alpha_channel == 0)
                                    processed_img[transparent_pixels, 0] = 0    # Blue
                                    processed_img[transparent_pixels, 1] = 255  # Green
                                    processed_img[transparent_pixels, 2] = 0    # Red
                                    processed_img[transparent_pixels, 3] = 255  # Alpha
                                
                                # 保存原始圖片
                                original_filename = f"{folder_name}_{index}.png"
                                original_save_path = output_dir / original_filename
                                
                                cv2.imwrite(str(original_save_path), processed_img)
                                saved_count += 1
                                self.log(f"    保存原圖: {original_filename}")
                                
                                # 創建水平翻轉圖片
                                flipped_img = cv2.flip(processed_img, 1)  # 1 表示水平翻轉
                                flipped_filename = f"{folder_name}_{index}_flipped.png"
                                flipped_save_path = output_dir / flipped_filename
                                
                                cv2.imwrite(str(flipped_save_path), flipped_img)
                                saved_count += 1
                                self.log(f"    保存翻轉: {flipped_filename}")
                                
                                index += 1
                                
                        except Exception as e:
                            self.log(f"    處理檔案失敗 {file_name}: {str(e)}")
                            continue
                    
                    if saved_count > 0:
                        self.log(f"  ✅ {mob_name}: 保存了 {saved_count} 張圖片到 {output_dir}")
                        return True
                    else:
                        self.log(f"  ❌ {mob_name}: 沒有成功保存任何圖片")
                        return False
                        
            except zipfile.BadZipFile:
                # 嘗試作為單張圖片處理
                self.log(f"  🔄 {mob_name}: 非 ZIP 格式，嘗試作為單張圖片處理")
                try:
                    np_arr = np.frombuffer(response.content, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        # 處理透明背景
                        processed_img = img.copy()
                        if len(processed_img.shape) >= 3 and processed_img.shape[2] == 4:
                            alpha_channel = processed_img[:, :, 3]
                            transparent_pixels = (alpha_channel == 0)
                            processed_img[transparent_pixels, 0] = 0    # Blue
                            processed_img[transparent_pixels, 1] = 255  # Green
                            processed_img[transparent_pixels, 2] = 0    # Red
                            processed_img[transparent_pixels, 3] = 255  # Alpha
                        
                        # 保存原圖
                        original_save_path = output_dir / f"{folder_name}_single.png"
                        cv2.imwrite(str(original_save_path), processed_img)
                        self.log(f"    保存原圖: {folder_name}_single.png")
                        
                        # 保存翻轉圖
                        flipped_img = cv2.flip(processed_img, 1)
                        flipped_save_path = output_dir / f"{folder_name}_single_flipped.png"
                        cv2.imwrite(str(flipped_save_path), flipped_img)
                        self.log(f"    保存翻轉: {folder_name}_single_flipped.png")
                        
                        self.log(f"  ✅ {mob_name}: 保存為 2 張圖片（含翻轉版本）")
                        return True
                    else:
                        self.log(f"  ❌ {mob_name}: 無法解碼圖片")
                        return False
                except Exception as e:
                    self.log(f"  ❌ {mob_name}: 處理單張圖片失敗 - {str(e)}")
                    return False
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                self.log(f"  ⚠️ {mob_name}: 沒有圖片資源 (404)")
                return False
            else:
                self.log(f"  ❌ {mob_name}: HTTP 錯誤 {e}")
                return False
            
        except Exception as e:
            self.log(f"  ❌ {mob_name}: 下載失敗 - {str(e)}")
            return False
    
    def log(self, message):
        """添加日誌消息"""
        import datetime
        
        # 生成時間戳
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # 在主線程中更新UI
        if threading.current_thread() == threading.main_thread():
            self._update_log_text(formatted_message)
        else:
            self.parent.after(0, self._update_log_text, formatted_message)
    
    def _update_log_text(self, message):
        """更新日誌文本（主線程中執行）"""
        self.log_text.insert(tk.END, message)
        
        # 自動滾動到底部
        self.log_text.see(tk.END)
        
        # 限制日誌長度
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:  # 保留最新的100行
            lines_to_keep = '\n'.join(lines[-100:])
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", lines_to_keep)
    
    def stop_download(self):
        """停止下載"""
        self.is_downloading = False
        self.log("🛑 下載已停止")
    
    def clear_log(self):
        """清空日誌"""
        self.log_text.delete("1.0", tk.END)