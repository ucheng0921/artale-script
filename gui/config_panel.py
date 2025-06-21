"""
配置設定面板 - 提供完整的配置設定界面（支援外部配置文件）
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Any, Callable, Tuple
import datetime

class ConfigPanel:
    """配置設定面板類"""
    
    def __init__(self, parent_frame, config_manager, on_config_changed: Callable = None):
        self.parent = parent_frame
        self.config_manager = config_manager
        self.on_config_changed = on_config_changed
        
        # 存儲各種控件的引用
        self.widgets = {}
        self.current_values = {}
        
        # 創建界面
        self.create_widgets()
        
        # 載入當前配置值
        self.load_current_config()
    
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
    
    def create_category_section(self, category: str, category_configs: Dict[str, str], 
                              types: Dict[str, str], choices: Dict[str, list]):
        """創建分類設定區域"""
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
        
        # 特殊處理被動技能布局
        if category == "被動技能系統配置":
            self.create_passive_skills_section(configs_frame, category_configs, types, choices)
        else:
            # 為每個配置項創建控件
            for config_key, description in category_configs.items():
                self.create_config_widget(configs_frame, config_key, description, 
                                        types.get(config_key, 'str'), 
                                        choices.get(config_key, []))
    
    def create_passive_skills_section(self, parent, category_configs: Dict[str, str], 
                                    types: Dict[str, str], choices: Dict[str, list]):
        """創建被動技能專用的緊湊布局"""
        
        # 總開關
        if 'ENABLE_PASSIVE_SKILLS' in category_configs:
            self.create_config_widget(parent, 'ENABLE_PASSIVE_SKILLS', 
                                    category_configs['ENABLE_PASSIVE_SKILLS'],
                                    types.get('ENABLE_PASSIVE_SKILLS', 'bool'), [])
        
        # 為每個被動技能創建一行布局
        for skill_num in range(1, 5):
            skill_frame = ctk.CTkFrame(parent)
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
        global_frame = ctk.CTkFrame(parent)
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
        # 特殊處理ENABLED_MONSTERS - 使用上下布局
        if config_key == 'ENABLED_MONSTERS':
            self.create_monster_config_widget(parent, config_key, description, config_type)
            return
        
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
    
    def create_monster_config_widget(self, parent, config_key: str, description: str, config_type: str):
        """為怪物選擇創建特殊的上下布局控件"""
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
        
        # 底部：怪物選擇區域
        widget_frame = ctk.CTkFrame(item_frame)
        widget_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        widget = self.create_monster_selection_widget(widget_frame)
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
        """創建列表控件（用於怪物選擇等）"""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=10, pady=10)
        
        # 如果是ENABLED_MONSTERS，創建特殊的多選界面
        if config_key == 'ENABLED_MONSTERS':
            return self.create_monster_selection_widget(frame)
        else:
            # 其他列表類型使用文本框
            entry = ctk.CTkEntry(frame, width=400)
            entry.pack(padx=10, pady=5)
            
            help_label = ctk.CTkLabel(frame, text="用逗號分隔多個值", font=ctk.CTkFont(size=10), text_color="gray")
            help_label.pack(padx=10, pady=(0, 5))
            
            return entry
    
    def create_monster_selection_widget(self, parent):
        """創建怪物選擇控件 - 可搜尋的滾動式界面"""
        # 怪物類型映射 - 可以自定義顯示名稱
        monster_display_names = {
            'monster1': '木妖',
            'monster2': '姑姑寶貝', 
            'monster3': '藍寶、紅寶',
            'monster4': '肥肥',
            'monster5': '鋼之黑肥肥',
            'monster6': '石巨人系列',
            'monster7': '月妙',
            'monster8': '青龍',
            'grupin': '獨角獅',
        }
        
        # 創建容器框架
        container_frame = ctk.CTkFrame(parent)
        container_frame.pack(fill="x", padx=10, pady=10)
        
        # 頂部控制區域
        control_frame = ctk.CTkFrame(container_frame)
        control_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        # 搜尋框
        search_frame = ctk.CTkFrame(control_frame)
        search_frame.pack(side="left", padx=(10, 5), pady=5)
        
        ctk.CTkLabel(search_frame, text="🔍 搜尋:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(5, 2), pady=5)
        
        self.search_entry = ctk.CTkEntry(
            search_frame, 
            width=200, 
            placeholder_text="輸入怪物名稱..."
        )
        self.search_entry.pack(side="left", padx=(2, 5), pady=5)
        self.search_entry.bind('<KeyRelease>', self.filter_monsters)
        
        # 全選/全不選按鈕
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.pack(side="right", padx=(5, 10), pady=5)
        
        select_all_btn = ctk.CTkButton(
            button_frame,
            text="全選",
            width=60,
            height=25,
            font=ctk.CTkFont(size=10),
            command=lambda: self.toggle_all_monsters(True)
        )
        select_all_btn.pack(side="left", padx=2)
        
        select_none_btn = ctk.CTkButton(
            button_frame,
            text="全不選", 
            width=60,
            height=25,
            font=ctk.CTkFont(size=10),
            command=lambda: self.toggle_all_monsters(False)
        )
        select_none_btn.pack(side="left", padx=2)
        
        clear_search_btn = ctk.CTkButton(
            button_frame,
            text="清除搜尋",
            width=80,
            height=25,
            font=ctk.CTkFont(size=10),
            command=self.clear_search
        )
        clear_search_btn.pack(side="left", padx=2)
        
        # 滾動式怪物選擇區域
        scroll_frame = ctk.CTkScrollableFrame(
            container_frame, 
            height=300,  # 設置固定高度以啟用滾動
            label_text="選擇要啟用的怪物類型："
        )
        scroll_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        # 存儲複選框和框架
        self.monster_checkboxes = {}
        self.monster_frames = {}
        self.all_monsters = monster_display_names
        
        # 創建所有怪物複選框
        for monster_key, display_name in monster_display_names.items():
            # 為每個怪物創建一個框架
            monster_frame = ctk.CTkFrame(scroll_frame)
            monster_frame.pack(fill="x", padx=5, pady=2)
            
            checkbox = ctk.CTkCheckBox(
                monster_frame,
                text=display_name,
                font=ctk.CTkFont(size=11),
                width=300
            )
            checkbox.pack(side="left", padx=10, pady=5)
            
            self.monster_checkboxes[monster_key] = checkbox
            self.monster_frames[monster_key] = monster_frame
        
        return self.monster_checkboxes
    
    def filter_monsters(self, event=None):
        """根據搜尋內容過濾顯示怪物"""
        search_text = self.search_entry.get().lower()
        
        for monster_key, monster_frame in self.monster_frames.items():
            display_name = self.all_monsters[monster_key].lower()
            
            # 檢查搜尋文字是否在怪物名稱中
            if search_text in display_name or search_text in monster_key.lower():
                monster_frame.pack(fill="x", padx=5, pady=2)
            else:
                monster_frame.pack_forget()
    
    def clear_search(self):
        """清除搜尋並顯示所有怪物"""
        self.search_entry.delete(0, tk.END)
        
        # 顯示所有怪物
        for monster_frame in self.monster_frames.values():
            monster_frame.pack(fill="x", padx=5, pady=2)
    
    def toggle_all_monsters(self, select_all: bool):
        """全選或全不選怪物 - 只對當前顯示的怪物生效"""
        for monster_key, checkbox in self.monster_checkboxes.items():
            # 只對當前顯示的怪物進行操作
            if self.monster_frames[monster_key].winfo_viewable():
                if select_all:
                    checkbox.select()
                else:
                    checkbox.deselect()
    
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
            if config_type == 'bool':
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
                if config_key == 'ENABLED_MONSTERS' and isinstance(widget, dict):
                    # 怪物選擇控件
                    for monster, checkbox in widget.items():
                        if monster in value:
                            checkbox.select()
                        else:
                            checkbox.deselect()
                else:
                    # 其他列表類型
                    if isinstance(value, list):
                        widget.delete(0, tk.END)
                        widget.insert(0, ', '.join(map(str, value)))
        
        except Exception as e:
            print(f"設置控件值失敗 {config_key}: {e}")
    
    def get_widget_value(self, config_key: str, widget):
        """獲取控件值"""
        config_types = self.config_manager.get_config_types()
        config_type = config_types.get(config_key, 'str')
        
        try:
            if config_type == 'bool':
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
                if config_key == 'ENABLED_MONSTERS' and isinstance(widget, dict):
                    # 怪物選擇控件
                    selected = []
                    for monster, checkbox in widget.items():
                        if checkbox.get():
                            selected.append(monster)
                    return selected
                else:
                    # 其他列表類型
                    text = widget.get().strip()
                    if text:
                        return [item.strip() for item in text.split(',')]
                    else:
                        return []
            
            return None
        
        except Exception as e:
            print(f"獲取控件值失敗 {config_key}: {e}")
            return None
    
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