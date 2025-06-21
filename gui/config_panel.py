"""
配置設定面板 - 提供完整的配置設定界面（整合怪物下載功能）
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Any, Callable, Tuple
import datetime
import os
from pathlib import Path
import re

class ConfigPanel:
    """配置設定面板類"""
    
    def __init__(self, parent_frame, config_manager, on_config_changed: Callable = None):
        self.parent = parent_frame
        self.config_manager = config_manager
        self.on_config_changed = on_config_changed
        
        # 存儲各種控件的引用
        self.widgets = {}
        self.current_values = {}
        
        # 怪物相關
        self.downloaded_monsters = {}  # 已下載的怪物
        self.monster_downloader = None  # 怪物下載器
        
        # 創建界面
        self.create_widgets()
        
        # 載入當前配置值
        self.load_current_config()
        
        # 掃描已下載的怪物（初始掃描，稍後會通過回調重新掃描獲取中文名稱）
        self.scan_downloaded_monsters()
    
    def create_widgets(self):
        """創建配置設定界面"""
        # 主框架
        self.main_frame = ctk.CTkScrollableFrame(self.parent)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 標題和控制按鈕
        self.create_header()
        
        # 獲取配置描述
        descriptions = self.config_manager.get_config_descriptions()
        types = self.config_manager.get_config_types()
        choices = self.config_manager.get_config_choices()
        
        # 為每個分類創建設定區域
        for category, category_configs in descriptions.items():
            if category == "怪物檢測與攻擊配置":
                self.create_monster_category_section(category, category_configs, types, choices)
            elif category == "被動技能系統配置":
                self.create_passive_skills_section(category, category_configs, types, choices)
            else:
                self.create_category_section(category, category_configs, types, choices)
    
    def create_header(self):
        """創建頂部控制區域"""
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        
        # 標題
        title_label = ctk.CTkLabel(
            header_frame,
            text="⚙️ 配置設定",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=15, pady=15)
        
        # 控制按鈕框架
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right", padx=15, pady=10)
        
        # 保存按鈕（保存到外部配置文件）
        quick_save_button = ctk.CTkButton(
            button_frame,
            text="💾 保存設定",
            command=self.quick_save_config,
            width=80,
            height=30,
            fg_color="green",
            hover_color="darkgreen"
        )
        quick_save_button.pack(side="left", padx=5, pady=5)
        
        # 重置按鈕
        reset_button = ctk.CTkButton(
            button_frame,
            text="🔄 重置默認",
            command=self.reset_config,
            width=100,
            height=30,
            fg_color="orange",
            hover_color="darkorange"
        )
        reset_button.pack(side="left", padx=5, pady=5)
        
        # 應用按鈕
        apply_button = ctk.CTkButton(
            button_frame,
            text="✅ 應用更改",
            command=self.apply_changes,
            width=100,
            height=30,
            fg_color="blue",
            hover_color="darkblue"
        )
        apply_button.pack(side="left", padx=5, pady=5)
        
        # 說明標籤
        info_label = ctk.CTkLabel(
            header_frame,
            text="💡 保存的設定會存儲在外部配置文件中，下次啟動時自動載入",
            font=ctk.CTkFont(size=10),
            text_color="cyan"
        )
        info_label.pack(pady=(0, 5))
    
    def create_monster_category_section(self, category: str, category_configs: Dict[str, str], 
                                      types: Dict[str, str], choices: Dict[str, list]):
        """創建怪物檢測與攻擊配置區域（特殊處理）"""
        # 分類框架
        category_frame = ctk.CTkFrame(self.main_frame)
        category_frame.pack(fill="x", pady=10)
        
        # 分類標題
        category_label = ctk.CTkLabel(
            category_frame,
            text=category,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        category_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 配置項容器
        configs_frame = ctk.CTkFrame(category_frame)
        configs_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 處理 ENABLED_MONSTERS 特殊配置
        for config_key, description in category_configs.items():
            if config_key == 'ENABLED_MONSTERS':
                self.create_monster_selection_widget(configs_frame, config_key, description)
            else:
                self.create_config_widget(configs_frame, config_key, description, 
                                        types.get(config_key, 'str'), 
                                        choices.get(config_key, []))
    
    def create_monster_selection_widget(self, parent, config_key: str, description: str):
        """創建怪物選擇控件 - 整合下載功能的選項卡界面"""
        # 主框架
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", padx=10, pady=10)
        
        # 頂部：描述標籤
        label_frame = ctk.CTkFrame(item_frame)
        label_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        desc_label = ctk.CTkLabel(
            label_frame,
            text=description,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        desc_label.pack(side="left", padx=10, pady=5)
        
        key_label = ctk.CTkLabel(
            label_frame,
            text=f"({config_key})",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        key_label.pack(side="right", padx=10, pady=5)
        
        # 選項卡框架
        tab_frame = ctk.CTkFrame(item_frame)
        tab_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # 創建選項卡視圖
        self.monster_tabview = ctk.CTkTabview(tab_frame)
        self.monster_tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 已下載選項卡
        self.downloaded_tab = self.monster_tabview.add("📦 已下載")
        self.create_downloaded_monsters_section(self.downloaded_tab)
        
        # 下載器選項卡
        self.downloader_tab = self.monster_tabview.add("⬇️ 下載器")
        self.create_monster_downloader_section(self.downloader_tab)
        
        # 將選項卡控件存儲為怪物選擇控件
        self.widgets[config_key] = {
            'tabview': self.monster_tabview,
            'downloaded_checkboxes': {},  # 稍後填充
            'type': 'monster_selection'
        }
    
    def create_downloaded_monsters_section(self, parent):
        """創建已下載怪物選擇區域"""
        # 搜尋框
        search_frame = ctk.CTkFrame(parent)
        search_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(search_frame, text="🔍 搜尋:", width=60).pack(side="left", padx=(5, 2), pady=5)
        
        self.downloaded_search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="搜尋已下載的怪物...",
            width=200
        )
        self.downloaded_search_entry.pack(side="left", fill="x", expand=True, padx=2, pady=5)
        self.downloaded_search_entry.bind('<KeyRelease>', self.filter_downloaded_monsters)
        
        # 清除搜尋按鈕
        clear_downloaded_button = ctk.CTkButton(
            search_frame,
            text="清除",
            command=self.clear_downloaded_search,
            width=50,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        clear_downloaded_button.pack(side="right", padx=(2, 5), pady=5)
        
        # 控制按鈕
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill="x", padx=5, pady=2)
        
        # 統計標籤
        self.downloaded_count_label = ctk.CTkLabel(
            control_frame,
            text="已下載: 0 個怪物",
            font=ctk.CTkFont(size=11)
        )
        self.downloaded_count_label.pack(side="left", padx=5, pady=2)
        
        # 刷新按鈕
        refresh_button = ctk.CTkButton(
            control_frame,
            text="🔄 刷新",
            command=self.refresh_downloaded_monsters,
            width=60,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        refresh_button.pack(side="right", padx=2, pady=2)
        
        # 全選/全不選按鈕
        select_all_downloaded_button = ctk.CTkButton(
            control_frame,
            text="全選",
            command=self.select_all_downloaded,
            width=50,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        select_all_downloaded_button.pack(side="right", padx=2, pady=2)
        
        select_none_downloaded_button = ctk.CTkButton(
            control_frame,
            text="全不選",
            command=self.select_none_downloaded,
            width=50,
            height=25,
            font=ctk.CTkFont(size=10)
        )
        select_none_downloaded_button.pack(side="right", padx=2, pady=2)
        
        # 已下載怪物列表
        self.downloaded_monsters_frame = ctk.CTkScrollableFrame(
            parent,
            height=200,
            label_text="選擇要啟用的已下載怪物："
        )
        self.downloaded_monsters_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 存儲已下載怪物的複選框
        self.downloaded_monster_checkboxes = {}
        self.downloaded_monster_frames = {}
    
    def create_monster_downloader_section(self, parent):
        """創建怪物下載器區域"""
        try:
            from .integrated_monster_downloader import IntegratedMonsterDownloader
            
            # 創建整合式怪物下載器
            self.monster_downloader = IntegratedMonsterDownloader(
                parent, 
                self.config_manager,
                on_download_complete=self.on_download_complete,
                on_data_loaded=self.on_downloader_data_loaded
            )
            
        except Exception as e:
            error_label = ctk.CTkLabel(
                parent,
                text=f"怪物下載器載入失敗:\n{str(e)}",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.pack(expand=True)
    
    def on_downloader_data_loaded(self):
        """下載器數據載入完成回調"""
        # 重新掃描已下載怪物，這時候可以獲取正確的中文名稱
        self.scan_downloaded_monsters()
    
    def on_download_complete(self):
        """下載完成回調"""
        # 刷新已下載怪物列表
        self.refresh_downloaded_monsters()
        
        # 如果怪物下載器可用，更新已下載怪物的中文名稱
        if hasattr(self, 'monster_downloader') and self.monster_downloader:
            for folder_name, monster_data in self.downloaded_monsters.items():
                # 嘗試獲取更準確的中文名稱
                chinese_name = self.get_monster_display_name_from_downloader(folder_name)
                if chinese_name:
                    monster_data['display_name'] = chinese_name
            
            # 重新顯示
            self.refresh_downloaded_monsters_display()
    
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
    
    def scan_downloaded_monsters(self):
        """掃描已下載的怪物"""
        try:
            monsters_path = Path(self.get_save_path())
            if not monsters_path.exists():
                return
            
            self.downloaded_monsters = {}
            
            # 掃描怪物資料夾
            for monster_dir in monsters_path.iterdir():
                if monster_dir.is_dir():
                    # 檢查是否有圖片文件
                    image_files = list(monster_dir.glob("*.png")) + list(monster_dir.glob("*.jpg"))
                    if image_files:
                        # 資料夾名稱就是英文安全檔名
                        folder_name = monster_dir.name
                        
                        # 嘗試從怪物下載器中獲取對應的中文名稱
                        display_name = self.get_monster_display_name_from_downloader(folder_name)
                        if not display_name:
                            # 如果找不到，使用美化的英文名稱作為備選
                            display_name = folder_name.replace('_', ' ').title()
                        
                        self.downloaded_monsters[folder_name] = {
                            'display_name': display_name,
                            'folder_name': folder_name,
                            'image_count': len(image_files),
                            'path': monster_dir
                        }
            
            # 更新已下載怪物顯示
            self.refresh_downloaded_monsters_display()
            
        except Exception as e:
            print(f"掃描已下載怪物失敗: {str(e)}")
    
    def get_monster_display_name_from_downloader(self, folder_name: str) -> str:
        """從怪物下載器中獲取對應的中文顯示名稱"""
        try:
            if hasattr(self, 'monster_downloader') and self.monster_downloader:
                # 搜尋下載器中對應的怪物數據
                for mob in self.monster_downloader.all_mobs:
                    # 獲取這個怪物的英文安全檔名
                    english_data = self.monster_downloader.english_names.get(mob['id'])
                    if english_data and english_data['safe_name'] == folder_name:
                        # 找到對應的怪物，返回 TMS 中文名稱
                        return mob['name']
            
            return None
        except Exception as e:
            print(f"從下載器獲取顯示名稱失敗: {str(e)}")
            return None
    
    def get_monster_display_name(self, folder_name: str) -> str:
        """根據資料夾名稱獲取顯示名稱 - 備用方法"""
        # 這個方法現在只是備用，主要使用 get_monster_display_name_from_downloader
        # 將下劃線替換為空格，首字母大寫
        display_name = folder_name.replace('_', ' ').title()
        
        # 如果包含 mob_ 前綴，移除它
        if display_name.startswith('Mob '):
            display_name = display_name[4:]
        
        return display_name
    
    def refresh_downloaded_monsters(self):
        """刷新已下載怪物（重新掃描）"""
        self.scan_downloaded_monsters()
    
    def refresh_downloaded_monsters_display(self):
        """刷新已下載怪物顯示"""
        # 清除舊的複選框
        for widget in self.downloaded_monsters_frame.winfo_children():
            widget.destroy()
        self.downloaded_monster_checkboxes.clear()
        self.downloaded_monster_frames.clear()
        
        # 更新統計
        self.downloaded_count_label.configure(text=f"已下載: {len(self.downloaded_monsters)} 個怪物")
        
        # 創建新的複選框
        for folder_name, monster_data in self.downloaded_monsters.items():
            self.create_downloaded_monster_checkbox(folder_name, monster_data)
        
        # 過濾顯示（如果有搜尋條件）
        self.filter_downloaded_monsters()
    
    def create_downloaded_monster_checkbox(self, folder_name: str, monster_data: dict):
        """為已下載怪物創建複選框"""
        monster_frame = ctk.CTkFrame(self.downloaded_monsters_frame)
        monster_frame.pack(fill="x", padx=2, pady=1)
        
        # 複選框
        var = ctk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            monster_frame,
            text="",
            variable=var,
            width=20
        )
        checkbox.pack(side="left", padx=(5, 2), pady=2)
        
        # 怪物信息標籤
        info_text = f"{monster_data['display_name']} ({folder_name}) - {monster_data['image_count']} 張圖片"
        
        info_label = ctk.CTkLabel(
            monster_frame,
            text=info_text,
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        info_label.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        
        # 存儲複選框引用
        self.downloaded_monster_checkboxes[folder_name] = {
            'checkbox': checkbox,
            'var': var,
            'monster_data': monster_data,
            'frame': monster_frame
        }
        self.downloaded_monster_frames[folder_name] = monster_frame
    
    def filter_downloaded_monsters(self, event=None):
        """根據搜尋內容過濾已下載怪物"""
        search_text = self.downloaded_search_entry.get().lower()
        
        for folder_name, monster_frame in self.downloaded_monster_frames.items():
            monster_data = self.downloaded_monsters[folder_name]
            display_name = monster_data['display_name'].lower()
            folder_name_lower = folder_name.lower()
            
            # 檢查搜尋文字是否在顯示名稱或資料夾名稱中
            if search_text in display_name or search_text in folder_name_lower:
                monster_frame.pack(fill="x", padx=2, pady=1)
            else:
                monster_frame.pack_forget()
    
    def clear_downloaded_search(self):
        """清除已下載怪物搜尋"""
        self.downloaded_search_entry.delete(0, tk.END)
        
        # 顯示所有怪物
        for monster_frame in self.downloaded_monster_frames.values():
            monster_frame.pack(fill="x", padx=2, pady=1)
    
    def select_all_downloaded(self):
        """全選已下載怪物 - 只對當前顯示的怪物生效"""
        for folder_name, checkbox_data in self.downloaded_monster_checkboxes.items():
            # 只對當前顯示的怪物進行操作
            if self.downloaded_monster_frames[folder_name].winfo_viewable():
                checkbox_data['var'].set(True)
    
    def select_none_downloaded(self):
        """全不選已下載怪物 - 只對當前顯示的怪物生效"""
        for folder_name, checkbox_data in self.downloaded_monster_checkboxes.items():
            # 只對當前顯示的怪物進行操作
            if self.downloaded_monster_frames[folder_name].winfo_viewable():
                checkbox_data['var'].set(False)
    
    def create_category_section(self, category: str, category_configs: Dict[str, str], 
                              types: Dict[str, str], choices: Dict[str, list]):
        """創建普通分類設定區域"""
        # 分類框架
        category_frame = ctk.CTkFrame(self.main_frame)
        category_frame.pack(fill="x", pady=10)
        
        # 分類標題
        category_label = ctk.CTkLabel(
            category_frame,
            text=category,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        category_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 配置項容器
        configs_frame = ctk.CTkFrame(category_frame)
        configs_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 為每個配置項創建控件
        for config_key, description in category_configs.items():
            self.create_config_widget(configs_frame, config_key, description, 
                                    types.get(config_key, 'str'), 
                                    choices.get(config_key, []))
    
    def create_passive_skills_section(self, category: str, category_configs: Dict[str, str], 
                                    types: Dict[str, str], choices: Dict[str, list]):
        """創建被動技能專用的緊湊布局"""
        # 分類框架
        category_frame = ctk.CTkFrame(self.main_frame)
        category_frame.pack(fill="x", pady=10)
        
        # 分類標題
        category_label = ctk.CTkLabel(
            category_frame,
            text=category,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        category_label.pack(anchor="w", padx=15, pady=(15, 10))
        
        # 配置項容器
        configs_frame = ctk.CTkFrame(category_frame)
        configs_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # 總開關
        if 'ENABLE_PASSIVE_SKILLS' in category_configs:
            self.create_config_widget(configs_frame, 'ENABLE_PASSIVE_SKILLS', 
                                    category_configs['ENABLE_PASSIVE_SKILLS'],
                                    types.get('ENABLE_PASSIVE_SKILLS', 'bool'), [])
        
        # 為每個被動技能創建一行布局
        for skill_num in range(1, 5):
            skill_frame = ctk.CTkFrame(configs_frame)
            skill_frame.pack(fill="x", padx=10, pady=5)
            
            # 技能標題
            skill_label = ctk.CTkLabel(
                skill_frame,
                text=f"被動技能 {skill_num}",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=100
            )
            skill_label.pack(side="left", padx=(10, 5), pady=10)
            
            # 按鍵設定
            key_frame = ctk.CTkFrame(skill_frame)
            key_frame.pack(side="left", padx=5, pady=5)
            
            ctk.CTkLabel(key_frame, text="按鍵:", width=40).pack(side="left", padx=(5, 2), pady=5)
            key_entry = ctk.CTkEntry(key_frame, width=40)
            key_entry.pack(side="left", padx=(2, 5), pady=5)
            self.widgets[f'PASSIVE_SKILL_{skill_num}_KEY'] = key_entry
            
            # 冷卻時間設定
            cooldown_frame = ctk.CTkFrame(skill_frame)
            cooldown_frame.pack(side="left", padx=5, pady=5)
            
            ctk.CTkLabel(cooldown_frame, text="冷卻:", width=40).pack(side="left", padx=(5, 2), pady=5)
            cooldown_entry = ctk.CTkEntry(cooldown_frame, width=60)
            cooldown_entry.pack(side="left", padx=(2, 2), pady=5)
            ctk.CTkLabel(cooldown_frame, text="秒", width=20).pack(side="left", padx=(2, 5), pady=5)
            self.widgets[f'PASSIVE_SKILL_{skill_num}_COOLDOWN'] = cooldown_entry
            
            # 啟用開關
            enable_switch = ctk.CTkSwitch(skill_frame, text="啟用", width=60)
            enable_switch.pack(side="left", padx=10, pady=5)
            self.widgets[f'ENABLE_PASSIVE_SKILL_{skill_num}'] = enable_switch
        
        # 全局設定 - 只保留隨機延遲
        global_frame = ctk.CTkFrame(configs_frame)
        global_frame.pack(fill="x", padx=10, pady=10)
        
        global_label = ctk.CTkLabel(
            global_frame,
            text="全局設定",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        global_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # 隨機延遲設定
        delay_frame = ctk.CTkFrame(global_frame)
        delay_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(delay_frame, text="隨機延遲範圍:", width=120).pack(side="left", padx=(10, 5), pady=5)
        
        min_delay_entry = ctk.CTkEntry(delay_frame, width=60, placeholder_text="最小")
        min_delay_entry.pack(side="left", padx=5, pady=5)
        self.widgets['PASSIVE_SKILL_RANDOM_DELAY_MIN'] = min_delay_entry
        
        ctk.CTkLabel(delay_frame, text="~", width=20).pack(side="left", padx=2, pady=5)
        
        max_delay_entry = ctk.CTkEntry(delay_frame, width=60, placeholder_text="最大")
        max_delay_entry.pack(side="left", padx=5, pady=5)
        self.widgets['PASSIVE_SKILL_RANDOM_DELAY_MAX'] = max_delay_entry
        
        ctk.CTkLabel(delay_frame, text="秒", width=30).pack(side="left", padx=5, pady=5)
    
    def create_config_widget(self, parent, config_key: str, description: str, 
                           config_type: str, config_choices: list):
        """為單個配置項創建控件"""
        # 配置項框架
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", padx=10, pady=5)
        
        # 左側：描述標籤
        label_frame = ctk.CTkFrame(item_frame)
        label_frame.pack(side="left", fill="y", padx=(10, 5), pady=10)
        
        desc_label = ctk.CTkLabel(
            label_frame,
            text=description,
            width=250,
            anchor="w"
        )
        desc_label.pack(padx=10, pady=5)
        
        key_label = ctk.CTkLabel(
            label_frame,
            text=f"({config_key})",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w"
        )
        key_label.pack(padx=10, pady=(0, 5))
        
        # 右側：控件區域
        widget_frame = ctk.CTkFrame(item_frame)
        widget_frame.pack(side="right", fill="x", expand=True, padx=(5, 10), pady=10)
        
        # 根據類型創建相應控件
        if config_type == 'bool':
            widget = self.create_bool_widget(widget_frame, config_key)
        elif config_type == 'choice':
            widget = self.create_choice_widget(widget_frame, config_key, config_choices)
        elif config_type == 'int':
            widget = self.create_int_widget(widget_frame, config_key)
        elif config_type == 'float':
            widget = self.create_float_widget(widget_frame, config_key)
        elif config_type == 'str':
            widget = self.create_str_widget(widget_frame, config_key)
        elif config_type == 'list':
            widget = self.create_list_widget(widget_frame, config_key)
        else:
            widget = self.create_str_widget(widget_frame, config_key)
        
        # 存儲控件引用
        self.widgets[config_key] = widget
    
    def create_bool_widget(self, parent, config_key: str):
        """創建布爾值控件"""
        switch = ctk.CTkSwitch(parent, text="")
        switch.pack(anchor="w", padx=10, pady=10)
        return switch
    
    def create_choice_widget(self, parent, config_key: str, choices: list):
        """創建選擇控件"""
        option_menu = ctk.CTkOptionMenu(parent, values=choices if choices else ["選項1", "選項2"])
        option_menu.pack(anchor="w", padx=10, pady=10)
        return option_menu
    
    def create_int_widget(self, parent, config_key: str):
        """創建整數控件"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=10)
        
        entry = ctk.CTkEntry(frame, width=150)
        entry.pack(side="left", padx=(10, 5), pady=5)
        
        # 添加驗證標籤
        validate_label = ctk.CTkLabel(frame, text="", width=100)
        validate_label.pack(side="left", padx=(5, 10), pady=5)
        
        # 綁定驗證事件
        def validate_int(*args):
            try:
                value = entry.get()
                if value == "":
                    validate_label.configure(text="", text_color="gray")
                    return
                
                int_value = int(value)
                is_valid, message = self.config_manager.validate_config(config_key, int_value)
                if is_valid:
                    validate_label.configure(text="✓", text_color="green")
                else:
                    validate_label.configure(text="✗", text_color="red")
            except ValueError:
                validate_label.configure(text="✗", text_color="red")
        
        entry.bind('<KeyRelease>', validate_int)
        
        return {'entry': entry, 'validate_label': validate_label}
    
    def create_float_widget(self, parent, config_key: str):
        """創建浮點數控件"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=10)
        
        entry = ctk.CTkEntry(frame, width=150)
        entry.pack(side="left", padx=(10, 5), pady=5)
        
        # 添加驗證標籤
        validate_label = ctk.CTkLabel(frame, text="", width=100)
        validate_label.pack(side="left", padx=(5, 10), pady=5)
        
        # 綁定驗證事件
        def validate_float(*args):
            try:
                value = entry.get()
                if value == "":
                    validate_label.configure(text="", text_color="gray")
                    return
                
                float_value = float(value)
                is_valid, message = self.config_manager.validate_config(config_key, float_value)
                if is_valid:
                    validate_label.configure(text="✓", text_color="green")
                else:
                    validate_label.configure(text="✗", text_color="red")
            except ValueError:
                validate_label.configure(text="✗", text_color="red")
        
        entry.bind('<KeyRelease>', validate_float)
        
        return {'entry': entry, 'validate_label': validate_label}
    
    def create_str_widget(self, parent, config_key: str):
        """創建字符串控件"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=10)
        
        entry = ctk.CTkEntry(frame, width=150)
        entry.pack(side="left", padx=(10, 5), pady=5)
        
        # 添加驗證標籤
        validate_label = ctk.CTkLabel(frame, text="", width=100)
        validate_label.pack(side="left", padx=(5, 10), pady=5)
        
        # 綁定驗證事件
        def validate_str(*args):
            value = entry.get()
            if value == "":
                validate_label.configure(text="", text_color="gray")
                return
            
            is_valid, message = self.config_manager.validate_config(config_key, value)
            if is_valid:
                validate_label.configure(text="✓", text_color="green")
            else:
                validate_label.configure(text="✗", text_color="red")
        
        entry.bind('<KeyRelease>', validate_str)
        
        return {'entry': entry, 'validate_label': validate_label}
    
    def create_list_widget(self, parent, config_key: str):
        """創建列表控件（用於其他列表類型）"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=10)
        
        # 其他列表類型使用文本框
        entry = ctk.CTkEntry(frame, width=400)
        entry.pack(padx=10, pady=5)
        
        help_label = ctk.CTkLabel(frame, text="用逗號分隔多個值", font=ctk.CTkFont(size=10), text_color="gray")
        help_label.pack(padx=10, pady=(0, 5))
        
        return entry
    
    def load_current_config(self):
        """載入當前配置值到控件"""
        configs = self.config_manager.get_gui_relevant_configs()
        
        for config_key, value in configs.items():
            if config_key in self.widgets:
                widget = self.widgets[config_key]
                self.set_widget_value(config_key, widget, value)
        
        # 存儲當前值
        self.current_values = configs.copy()
    
    def set_widget_value(self, config_key: str, widget, value):
        """設置控件值"""
        config_types = self.config_manager.get_config_types()
        config_type = config_types.get(config_key, 'str')
        
        try:
            if config_key == 'ENABLED_MONSTERS':
                # 特殊處理怪物選擇
                self.set_monster_selection_value(value)
            elif config_type == 'bool':
                if value:
                    widget.select()
                else:
                    widget.deselect()
            elif config_type == 'choice':
                widget.set(str(value))
            elif config_type in ['int', 'float', 'str']:
                if isinstance(widget, dict):  # 複合控件
                    widget['entry'].delete(0, tk.END)
                    widget['entry'].insert(0, str(value))
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, str(value))
            elif config_type == 'list':
                if isinstance(value, list):
                    widget.delete(0, tk.END)
                    widget.insert(0, ', '.join(map(str, value)))
        
        except Exception as e:
            print(f"設置控件值失敗 {config_key}: {e}")
    
    def set_monster_selection_value(self, value):
        """設置怪物選擇值"""
        if not isinstance(value, list):
            return
        
        # 設置已下載怪物的選中狀態
        for folder_name, checkbox_data in self.downloaded_monster_checkboxes.items():
            if folder_name in value:
                checkbox_data['var'].set(True)
            else:
                checkbox_data['var'].set(False)
    
    def get_widget_value(self, config_key: str, widget):
        """獲取控件值"""
        config_types = self.config_manager.get_config_types()
        config_type = config_types.get(config_key, 'str')
        
        try:
            if config_key == 'ENABLED_MONSTERS':
                # 特殊處理怪物選擇
                return self.get_monster_selection_value()
            elif config_type == 'bool':
                return widget.get()
            elif config_type == 'choice':
                return widget.get()
            elif config_type == 'int':
                if isinstance(widget, dict):
                    return int(widget['entry'].get())
                else:
                    return int(widget.get())
            elif config_type == 'float':
                if isinstance(widget, dict):
                    return float(widget['entry'].get())
                else:
                    return float(widget.get())
            elif config_type == 'str':
                if isinstance(widget, dict):
                    return widget['entry'].get()
                else:
                    return widget.get()
            elif config_type == 'list':
                text = widget.get().strip()
                if text:
                    return [item.strip() for item in text.split(',')]
                else:
                    return []
            
            return None
        
        except Exception as e:
            print(f"獲取控件值失敗 {config_key}: {e}")
            return None
    
    def get_monster_selection_value(self):
        """獲取怪物選擇值"""
        selected = []
        
        # 從已下載怪物中獲取選中的
        for folder_name, checkbox_data in self.downloaded_monster_checkboxes.items():
            if checkbox_data['var'].get():
                selected.append(folder_name)
        
        return selected
    
    def collect_current_values(self) -> Dict[str, Any]:
        """收集當前所有控件的值"""
        values = {}
        
        for config_key, widget in self.widgets.items():
            try:
                value = self.get_widget_value(config_key, widget)
                if value is not None:
                    values[config_key] = value
            except Exception as e:
                print(f"收集配置值失敗 {config_key}: {e}")
        
        return values
    
    def validate_all_values(self) -> Tuple[bool, list]:
        """驗證所有配置值"""
        values = self.collect_current_values()
        invalid_configs = []
        
        for config_key, value in values.items():
            is_valid, message = self.config_manager.validate_config(config_key, value)
            if not is_valid:
                invalid_configs.append(f"{config_key}: {message}")
        
        return len(invalid_configs) == 0, invalid_configs
    
    def apply_changes(self):
        """應用配置更改"""
        # 驗證所有值
        is_valid, invalid_configs = self.validate_all_values()
        
        if not is_valid:
            error_message = "以下配置值無效:\n\n" + "\n".join(invalid_configs)
            messagebox.showerror("配置錯誤", error_message)
            return
        
        # 收集值
        values = self.collect_current_values()
        
        # 檢查是否有更改
        changed_configs = {}
        for key, value in values.items():
            if key in self.current_values:
                if self.current_values[key] != value:
                    changed_configs[key] = value
            else:
                changed_configs[key] = value
        
        if not changed_configs:
            messagebox.showinfo("提示", "沒有配置更改需要應用")
            return
        
        # 應用更改
        success = self.config_manager.update_configs(changed_configs)
        
        if success:
            # 更新當前值緩存
            self.current_values.update(changed_configs)
            
            # 回調通知父窗口
            if self.on_config_changed:
                self.on_config_changed(changed_configs)
            
            # 顯示更改的配置
            change_list = "\n".join([f"• {key} = {value}" for key, value in changed_configs.items()])
            messagebox.showinfo("配置已應用", f"以下配置已成功更新:\n\n{change_list}")
        else:
            messagebox.showerror("錯誤", "應用配置更改失敗")
    
    def quick_save_config(self):
        """快速保存配置（保存到外部配置文件）"""
        # 驗證所有值
        is_valid, invalid_configs = self.validate_all_values()
        
        if not is_valid:
            error_message = "以下配置值無效，無法保存:\n\n" + "\n".join(invalid_configs)
            messagebox.showerror("配置錯誤", error_message)
            return
        
        # 收集值
        values = self.collect_current_values()
        
        # 檢查是否有更改
        changed_configs = {}
        for key, value in values.items():
            if key in self.current_values:
                if self.current_values[key] != value:
                    changed_configs[key] = value
            else:
                changed_configs[key] = value
        
        if not changed_configs:
            messagebox.showinfo("提示", "沒有配置更改需要保存")
            return
        
        # 確認保存
        change_list = "\n".join([f"• {key} = {value}" for key, value in changed_configs.items()])
        result = messagebox.askyesno(
            "確認快速保存", 
            f"將以下配置保存到外部配置文件:\n\n{change_list}\n\n配置將在下次啟動時自動載入。確定要繼續嗎？"
        )
        
        if not result:
            return
        
        # 應用並保存配置
        success = self.config_manager.update_configs(changed_configs)
        
        if success:
            # 更新當前值緩存
            self.current_values.update(changed_configs)
            
            # 保存到外部配置文件
            self.save_to_external_config(changed_configs)
            
            # 回調通知父窗口
            if self.on_config_changed:
                self.on_config_changed(changed_configs)
            
            messagebox.showinfo("保存成功", f"配置已保存到外部文件\n\n更新了 {len(changed_configs)} 項配置\n\n下次啟動時會自動載入這些設定")
        else:
            messagebox.showerror("錯誤", "快速保存配置失敗")
    
    def save_to_external_config(self, changed_configs):
        """保存配置到外部配置文件"""
        try:
            # 獲取當前所有配置
            all_configs = self.config_manager.get_gui_relevant_configs()
            
            # 更新已更改的配置
            all_configs.update(changed_configs)
            
            # 使用config模組的保存功能
            import config
            success = config.save_external_config(all_configs)
            
            if success:
                print(f"✅ 配置已保存到外部文件")
            else:
                print(f"❌ 保存到外部文件失敗")
                messagebox.showerror("錯誤", "保存到外部配置文件失敗")
            
        except Exception as e:
            print(f"❌ 保存到外部文件時發生錯誤: {e}")
            messagebox.showerror("錯誤", f"保存配置時發生錯誤:\n{str(e)}")
    
    def reset_config(self):
        """重置為默認配置"""
        result = messagebox.askyesno(
            "確認重置", 
            "確定要重置所有配置為默認值嗎？\n\n這將清除所有自定義設定。"
        )
        
        if result:
            success = self.config_manager.reset_to_defaults()
            if success:
                # 重新載入界面值
                self.load_current_config()
                messagebox.showinfo("成功", "配置已重置為默認值")
                
                # 通知父窗口配置已更改
                if self.on_config_changed:
                    self.on_config_changed(self.current_values)
            else:
                messagebox.showerror("錯誤", "重置配置失敗")
    
    def refresh_display(self):
        """刷新顯示（重新載入配置值）"""
        self.load_current_config()
    
    def get_unsaved_changes(self) -> Dict[str, Any]:
        """獲取未保存的更改"""
        current_values = self.collect_current_values()
        changes = {}
        
        for key, value in current_values.items():
            if key in self.current_values:
                if self.current_values[key] != value:
                    changes[key] = {
                        'old': self.current_values[key],
                        'new': value
                    }
            else:
                changes[key] = {
                    'old': None,
                    'new': value
                }
        
        return changes
    
    def has_unsaved_changes(self) -> bool:
        """檢查是否有未保存的更改"""
        return len(self.get_unsaved_changes()) > 0