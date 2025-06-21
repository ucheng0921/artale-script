"""
怪物圖片下載器 GUI 模組 - 獨立文件
保存為: gui/monster_downloader.py
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
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
import sys
import time

class MonsterDownloaderPanel:
    """怪物圖片下載器面板"""
    
    def __init__(self, parent_frame, config_manager=None):
        self.parent = parent_frame
        self.config_manager = config_manager
        
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
        self.download_thread = None
        
        # 不使用預定義的映射，直接使用 API 數據進行 ID 對照
        
        # 創建界面
        self.create_widgets()
        
        # 載入怪物資料
        self.load_monster_data_async()
    
    def create_widgets(self):
        """創建界面組件"""
        # 主框架
        self.main_frame = ctk.CTkScrollableFrame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 標題區域
        self.create_header()
        
        # 搜尋區域
        self.create_search_section()
        
        # 怪物列表區域
        self.create_monster_list_section()
        
        # 下載控制區域
        self.create_download_section()
        
        # 日誌區域
        self.create_log_section()
    
    def create_header(self):
        """創建標題區域"""
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # 標題
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎮 MapleStory 怪物圖片下載器",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=15, pady=15)
        
        # 狀態標籤
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="載入中...",
            font=ctk.CTkFont(size=12),
            text_color="orange"
        )
        self.status_label.pack(side="right", padx=15, pady=15)
        
        # 信息標籤
        info_frame = ctk.CTkFrame(header_frame)
        info_frame.pack(side="bottom", fill="x", padx=15, pady=(0, 10))
        
        info_text = "💡 功能說明：下載 MapleStory TMS 怪物圖片，自動處理透明背景並保存為 PNG 格式"
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            text_color="cyan",
            wraplength=600
        )
        info_label.pack(pady=5)
    
    def create_search_section(self):
        """創建搜尋區域"""
        search_frame = ctk.CTkFrame(self.main_frame)
        search_frame.pack(fill="x", pady=(0, 10))
        
        # 搜尋標題
        search_title = ctk.CTkLabel(
            search_frame,
            text="🔍 搜尋怪物",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        search_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        # 搜尋控制區域
        search_control_frame = ctk.CTkFrame(search_frame)
        search_control_frame.pack(fill="x", padx=15, pady=(5, 15))
        
        # 搜尋輸入框
        search_input_frame = ctk.CTkFrame(search_control_frame)
        search_input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(search_input_frame, text="怪物名稱:", width=80).pack(side="left", padx=(10, 5), pady=5)
        
        self.search_entry = ctk.CTkEntry(
            search_input_frame,
            placeholder_text="輸入怪物名稱進行搜尋 (例如: 嫩寶、藍寶、菇菇)",
            width=300
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        self.search_entry.bind('<Return>', self.search_monsters)
        
        # 搜尋按鈕
        search_button = ctk.CTkButton(
            search_input_frame,
            text="🔍 搜尋",
            command=self.search_monsters,
            width=80,
            height=30
        )
        search_button.pack(side="right", padx=(5, 10), pady=5)
        
        # 清除搜尋按鈕
        clear_button = ctk.CTkButton(
            search_input_frame,
            text="🗑️ 清除",
            command=self.clear_search,
            width=80,
            height=30,
            fg_color="gray",
            hover_color="darkgray"
        )
        clear_button.pack(side="right", padx=5, pady=5)
        
        # 快速搜尋按鈕
        quick_search_frame = ctk.CTkFrame(search_control_frame)
        quick_search_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkLabel(quick_search_frame, text="快速搜尋:", width=80).pack(side="left", padx=(10, 5), pady=5)
        
        quick_searches = ["嫩寶", "藍寶", "菇菇", "肥肥", "石頭人", "木妖"]
        for search_term in quick_searches:
            quick_btn = ctk.CTkButton(
                quick_search_frame,
                text=search_term,
                command=lambda term=search_term: self.quick_search(term),
                width=60,
                height=25,
                font=ctk.CTkFont(size=10)
            )
            quick_btn.pack(side="left", padx=2, pady=5)
    
    def create_monster_list_section(self):
        """創建怪物列表區域"""
        list_frame = ctk.CTkFrame(self.main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 列表標題
        list_title = ctk.CTkLabel(
            list_frame,
            text="📋 怪物列表",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        # 列表控制區域
        list_control_frame = ctk.CTkFrame(list_frame)
        list_control_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        # 結果統計
        self.result_count_label = ctk.CTkLabel(
            list_control_frame,
            text="總共 0 個怪物",
            font=ctk.CTkFont(size=12)
        )
        self.result_count_label.pack(side="left", padx=10, pady=5)
        
        # 全選/全不選按鈕
        select_all_button = ctk.CTkButton(
            list_control_frame,
            text="全選",
            command=self.select_all_monsters,
            width=60,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        select_all_button.pack(side="right", padx=2, pady=5)
        
        select_none_button = ctk.CTkButton(
            list_control_frame,
            text="全不選",
            command=self.select_none_monsters,
            width=60,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        select_none_button.pack(side="right", padx=2, pady=5)
        
        # 怪物列表（滾動框）
        self.monster_listbox_frame = ctk.CTkScrollableFrame(
            list_frame,
            height=300,
            label_text="選擇要下載的怪物 (可多選)："
        )
        self.monster_listbox_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # 存儲複選框
        self.monster_checkboxes = {}
    
    def create_download_section(self):
        """創建下載控制區域"""
        download_frame = ctk.CTkFrame(self.main_frame)
        download_frame.pack(fill="x", pady=(0, 10))
        
        # 下載標題
        download_title = ctk.CTkLabel(
            download_frame,
            text="⬇️ 下載控制",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        download_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        # 下載設置
        download_settings_frame = ctk.CTkFrame(download_frame)
        download_settings_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        # 保存路徑顯示
        path_frame = ctk.CTkFrame(download_settings_frame)
        path_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(path_frame, text="保存路徑:", width=80).pack(side="left", padx=(10, 5), pady=5)
        
        self.save_path_label = ctk.CTkLabel(
            path_frame,
            text=self.get_save_path(),
            font=ctk.CTkFont(size=10),
            text_color="cyan",
            anchor="w"
        )
        self.save_path_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # 下載選項
        options_frame = ctk.CTkFrame(download_settings_frame)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.skip_death_var = ctk.BooleanVar(value=True)
        skip_death_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="跳過死亡動畫 (die1)",
            variable=self.skip_death_var
        )
        skip_death_checkbox.pack(side="left", padx=10, pady=5)
        
        self.use_english_names_var = ctk.BooleanVar(value=True)
        english_names_checkbox = ctk.CTkCheckBox(
            options_frame,
            text="使用英文檔案名稱",
            variable=self.use_english_names_var
        )
        english_names_checkbox.pack(side="left", padx=20, pady=5)
        
        # 下載按鈕
        download_button_frame = ctk.CTkFrame(download_settings_frame)
        download_button_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        self.download_button = ctk.CTkButton(
            download_button_frame,
            text="📥 開始下載選中的怪物",
            command=self.start_download,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="darkgreen"
        )
        self.download_button.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        
        self.stop_download_button = ctk.CTkButton(
            download_button_frame,
            text="⏹️ 停止下載",
            command=self.stop_download,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_download_button.pack(side="right", padx=(5, 10), pady=5)
    
    def create_log_section(self):
        """創建日誌區域"""
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True)
        
        # 日誌標題
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 下載日誌",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.pack(anchor="w", padx=15, pady=(15, 5))
        
        # 日誌控制
        log_control_frame = ctk.CTkFrame(log_frame)
        log_control_frame.pack(fill="x", padx=15, pady=(5, 10))
        
        clear_log_button = ctk.CTkButton(
            log_control_frame,
            text="🗑️ 清空日誌",
            command=self.clear_log,
            width=100,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        clear_log_button.pack(side="left", padx=10, pady=5)
        
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        auto_scroll_checkbox = ctk.CTkCheckBox(
            log_control_frame,
            text="自動滾動",
            variable=self.auto_scroll_var
        )
        auto_scroll_checkbox.pack(side="right", padx=10, pady=5)
        
        # 日誌文本框
        self.log_text = ctk.CTkTextbox(
            log_frame,
            height=200,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=11)
        )
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
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
    
    def get_all_mobs(self):
        """獲取所有怪物資料"""
        url = f"{self.BASE_URL}/api/{self.DEFAULT_REGION}/{self.DEFAULT_VERSION}/mob"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            mob_data = response.json()
            
            # 顯示前幾個怪物作為範例
            if mob_data:
                self.log("前 5 個怪物範例:")
                for i, mob in enumerate(mob_data[:5]):
                    self.log(f"  ID: {mob['id']}, 名稱: {mob['name']}, 等級: {mob['level']}")
            
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
    
    def quick_search(self, search_term):
        """快速搜尋"""
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, search_term)
        self.search_monsters()
    
    def clear_search(self):
        """清除搜尋"""
        self.search_entry.delete(0, tk.END)
        self.filtered_mobs = self.all_mobs.copy()
        self.refresh_monster_list()
    
    def refresh_monster_list(self):
        """刷新怪物列表顯示"""
        # 清除舊的複選框
        for widget in self.monster_listbox_frame.winfo_children():
            widget.destroy()
        self.monster_checkboxes.clear()
        
        # 更新結果統計
        self.result_count_label.configure(text=f"找到 {len(self.filtered_mobs)} 個怪物")
        
        # 創建新的複選框
        for mob in self.filtered_mobs[:100]:  # 限制顯示前100個結果
            self.create_monster_checkbox(mob)
        
        if len(self.filtered_mobs) > 100:
            # 如果結果太多，顯示提示
            info_label = ctk.CTkLabel(
                self.monster_listbox_frame,
                text=f"... 還有 {len(self.filtered_mobs) - 100} 個結果，請使用更具體的搜尋條件",
                font=ctk.CTkFont(size=10),
                text_color="orange"
            )
            info_label.pack(pady=5)
    
    def create_monster_checkbox(self, mob):
        """為單個怪物創建複選框"""
        mob_frame = ctk.CTkFrame(self.monster_listbox_frame)
        mob_frame.pack(fill="x", padx=5, pady=2)
        
        # 複選框
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            mob_frame,
            text="",
            variable=var,
            width=20
        )
        checkbox.pack(side="left", padx=(10, 5), pady=5)
        
        # 怪物信息標籤 - 使用真實的 API 數據對照
        english_data = self.english_names.get(mob['id'])
        if english_data:
            english_name = english_data['original_name']
            safe_filename = english_data['safe_name']
        else:
            english_name = f"mob_{mob['id']}"
            safe_filename = f"mob_{mob['id']}"
        
        # 顯示格式：中文名 -> 英文名 (ID: xxx, 等級: xxx)
        info_text = f"{mob['name']} -> {english_name} (ID: {mob['id']}, 等級: {mob['level']})"
        
        info_label = ctk.CTkLabel(
            mob_frame,
            text=info_text,
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        info_label.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # 存儲複選框引用
        self.monster_checkboxes[mob['id']] = {
            'checkbox': checkbox,
            'var': var,
            'mob': mob,
            'frame': mob_frame,
            'safe_filename': safe_filename  # 存儲安全檔名
        }
    
    def select_all_monsters(self):
        """全選怪物"""
        for mob_id, data in self.monster_checkboxes.items():
            data['var'].set(True)
        self.log(f"✅ 已選擇所有 {len(self.monster_checkboxes)} 個怪物")
    
    def select_none_monsters(self):
        """全不選怪物"""
        for mob_id, data in self.monster_checkboxes.items():
            data['var'].set(False)
        self.log("🗑️ 已取消選擇所有怪物")
    
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
            messagebox.showwarning("提示", "請至少選擇一個怪物進行下載")
            return
        
        # 確認下載
        result = messagebox.askyesno(
            "確認下載",
            f"確定要下載 {len(selected_monsters)} 個怪物的圖片嗎？\n\n"
            f"保存路徑: {self.get_save_path()}"
        )
        
        if not result:
            return
        
        # 開始下載
        self.is_downloading = True
        self.download_button.configure(state="disabled")
        self.stop_download_button.configure(state="normal")
        
        self.download_thread = threading.Thread(
            target=self.download_monsters_thread,
            args=(selected_monsters,),
            daemon=True
        )
        self.download_thread.start()
    
    def stop_download(self):
        """停止下載"""
        self.is_downloading = False
        self.download_button.configure(state="normal")
        self.stop_download_button.configure(state="disabled")
        self.log("🛑 下載已停止")
    
    def download_monsters_thread(self, monsters):
        """下載怪物線程"""
        try:
            total_count = len(monsters)
            success_count = 0
            error_count = 0
            
            self.log(f"🚀 開始下載 {total_count} 個怪物...")
            
            for i, mob in enumerate(monsters, 1):
                if not self.is_downloading:
                    self.log("🛑 下載被用戶停止")
                    break
                
                self.log(f"📥 正在下載 ({i}/{total_count}): {mob['name']} (ID: {mob['id']})")
                
                try:
                    # 確定檔案名稱
                    if self.use_english_names_var.get():
                        # 使用英文安全檔名
                        english_data = self.english_names.get(mob['id'])
                        if english_data:
                            safe_filename = english_data['safe_name']
                        else:
                            safe_filename = f"mob_{mob['id']}"
                    else:
                        # 使用中文名稱但轉為安全檔名
                        safe_filename = re.sub(r'[^\w\u4e00-\u9fff]', '_', mob['name'])
                    
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
                    self.log(f"❌ 下載 {mob['name']} 時發生錯誤: {str(e)}")
                
                # 短暫延遲避免請求過於頻繁
                time.sleep(0.5)
            
            # 完成報告
            self.log("=" * 50)
            self.log(f"🎉 下載完成！成功: {success_count}, 失敗: {error_count}")
            self.log(f"📁 保存位置: {self.get_save_path()}")
            
        except Exception as e:
            self.log(f"❌ 下載過程發生錯誤: {str(e)}")
        finally:
            # 在主線程中更新UI
            self.parent.after(0, self.download_finished)
    
    def download_finished(self):
        """下載完成後的UI更新"""
        self.is_downloading = False
        self.download_button.configure(state="normal")
        self.stop_download_button.configure(state="disabled")
    
    def save_mob(self, mob_id, folder_name, mob_name):
        """下載並保存怪物圖片"""
        try:
            # 創建輸出目錄
            output_dir = Path(self.get_save_path()) / folder_name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 下載 URL
            download_url = f"{self.BASE_URL}/api/{self.DEFAULT_REGION}/{self.DEFAULT_VERSION}/mob/{mob_id}/download"
            
            response = requests.get(download_url, timeout=60)
            response.raise_for_status()
            
            if len(response.content) < 100:
                self.log(f"⚠️ {mob_name}: 回應內容太小，可能沒有圖片資源")
                return False
            
            # 處理 ZIP 檔案
            try:
                zip_bytes = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_bytes) as zip_file:
                    file_list = zip_file.namelist()
                    
                    if len(file_list) == 0:
                        self.log(f"⚠️ {mob_name}: ZIP 檔案是空的")
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
                                if len(img.shape) >= 3 and img.shape[2] == 4:
                                    alpha_channel = img[:, :, 3]
                                    transparent_pixels = (alpha_channel == 0)
                                    img[transparent_pixels, 0] = 0    # Blue
                                    img[transparent_pixels, 1] = 255  # Green
                                    img[transparent_pixels, 2] = 0    # Red
                                    img[transparent_pixels, 3] = 255  # Alpha
                                
                                # 保存圖片
                                new_filename = f"{folder_name}_{index}.png"
                                save_path = output_dir / new_filename
                                
                                success, encoded_img = cv2.imencode('.png', img)
                                if success:
                                    with open(save_path, 'wb') as f:
                                        f.write(encoded_img.tobytes())
                                    saved_count += 1
                                
                                index += 1
                                
                        except Exception as e:
                            continue
                    
                    if saved_count > 0:
                        self.log(f"  ✅ {mob_name}: 保存了 {saved_count} 張圖片到 {output_dir}")
                        return True
                    else:
                        self.log(f"  ❌ {mob_name}: 沒有成功保存任何圖片")
                        return False
                        
            except zipfile.BadZipFile:
                # 嘗試作為單張圖片處理
                try:
                    np_arr = np.frombuffer(response.content, np.uint8)
                    img = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
                    if img is not None:
                        save_path = output_dir / f"{folder_name}_single.png"
                        cv2.imwrite(str(save_path), img)
                        self.log(f"  ✅ {mob_name}: 保存為單張圖片")
                        return True
                    else:
                        self.log(f"  ❌ {mob_name}: 無法解碼圖片")
                        return False
                except Exception as e:
                    self.log(f"  ❌ {mob_name}: 處理單張圖片失敗")
                    return False
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                self.log(f"  ⚠️ {mob_name}: 沒有圖片資源 (404)")
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
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
        
        # 限制日誌長度
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 500:  # 保留最新的500行
            lines_to_keep = '\n'.join(lines[-500:])
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", lines_to_keep)
    
    def clear_log(self):
        """清空日誌"""
        self.log_text.delete("1.0", tk.END)
        self.log("📋 日誌已清空")