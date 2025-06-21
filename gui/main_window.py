"""
整合版主視窗類 - 包含 Firebase 認證功能、單一會話限制和怪物下載器 (簡化界面版)
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time
from typing import Optional

# 設置 CustomTkinter 主題
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow:
    """整合版主視窗類"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.setup_window()
        self.create_variables()
        
        # 腳本執行相關
        self.script_wrapper = None
        self.script_running = False
        self.config_manager = None
        
        # Firebase 認證相關
        self.auth_manager = None
        self.login_in_progress = False
        self.session_check_thread = None
        self.last_session_check = 0
        
        # 先創建界面組件
        self.create_widgets()
        
        # 然後初始化管理器（此時日誌控件已經存在）
        self.initialize_firebase_auth()
        self.initialize_script_wrapper()
        self.initialize_config_manager()
        
        # 啟動會話檢查
        self.start_session_monitoring()
        
    def setup_window(self):
        """設置主視窗屬性"""
        self.root.title("Artale Script GUI v1.1")
        self.root.geometry("1200x800")  # 增加寬度以容納新功能
        self.root.minsize(1000, 700)
        
        # 設置關閉事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_variables(self):
        """創建控制變數"""
        # 登入狀態
        self.logged_in = tk.BooleanVar(value=False)
        
        # 腳本狀態
        self.script_status = tk.StringVar(value="未運行")
        
        # 連接狀態
        self.connection_status = tk.StringVar(value="未連接")
        
        # 當前用戶
        self.current_user = tk.StringVar(value="未登入")
    
    def initialize_firebase_auth(self):
        """初始化 Firebase 認證"""
        try:
            from .firebase_auth import get_auth_manager
            self.auth_manager = get_auth_manager()
            
            if self.auth_manager.is_initialized:
                self.log("✅ 認證系統初始化完成")
            else:
                self.log("❌ 認證系統初始化失敗")
                self.log("請檢查網路連接和配置文件")
                
        except Exception as e:
            self.log(f"❌ 認證系統初始化錯誤: {str(e)}")
            self.auth_manager = None
    
    def initialize_script_wrapper(self):
        """初始化腳本包裝器"""
        try:
            from .script_wrapper import ScriptWrapper
            self.script_wrapper = ScriptWrapper(self)
            self.log("✅ 腳本包裝器初始化完成")
        except Exception as e:
            self.log(f"❌ 腳本包裝器初始化失敗: {str(e)}")
            self.script_wrapper = None
    
    def initialize_config_manager(self):
        """初始化配置管理器"""
        try:
            from .config_manager import ConfigManager
            self.config_manager = ConfigManager()
            self.log("✅ 配置管理器初始化完成")
            
            # 初始化完成後，重新創建配置面板
            self.refresh_config_panel()
            
        except Exception as e:
            self.log(f"❌ 配置管理器初始化失敗: {str(e)}")
            self.config_manager = None
    
    def start_session_monitoring(self):
        """啟動會話監控"""
        if not self.session_check_thread or not self.session_check_thread.is_alive():
            self.session_check_thread = threading.Thread(target=self._session_monitor_loop, daemon=True)
            self.session_check_thread.start()
    
    def _session_monitor_loop(self):
        """會話監控循環"""
        while True:
            try:
                time.sleep(120)  # 每2分鐘檢查一次，減少頻率
                current_time = time.time()
                
                # 避免頻繁檢查 - 至少間隔100秒
                if current_time - self.last_session_check < 100:
                    continue
                
                self.last_session_check = current_time
                
                if self.auth_manager and self.logged_in.get():
                    print(f"🔍 開始會話檢查: {time.strftime('%H:%M:%S')}")
                    
                    # 驗證會話是否仍然有效
                    if not self.auth_manager.validate_session():
                        # 會話失效，強制登出
                        print(f"❌ 會話驗證失敗，準備登出")
                        self.root.after(0, self._force_logout_due_to_session_invalid)
                    else:
                        print(f"✅ 會話檢查通過")
                        
            except Exception as e:
                print(f"會話監控錯誤: {str(e)}")
                time.sleep(5)
    
    def _force_logout_due_to_session_invalid(self):
        """由於會話失效強制登出"""
        self.handle_logout()
        self.log("⚠️ 會話已失效，已自動登出")
        self.log("💡 可能原因：帳號在其他地方登入、會話過期或帳號被停用")
        messagebox.showwarning(
            "會話失效", 
            "您的登入會話已失效，可能的原因：\n"
            "• 帳號在其他地方登入\n"
            "• 會話超時\n"
            "• 帳號被管理員停用\n\n"
            "請重新登入。"
        )
    
    def refresh_config_panel(self):
        """刷新配置面板"""
        try:
            if hasattr(self, 'settings_tab') and hasattr(self, 'tabview'):
                try:
                    self.tabview.delete("⚙️ 進階設定")
                except:
                    pass
                
                self.settings_tab = self.tabview.add("⚙️ 進階設定")
                self.create_settings_section(self.settings_tab)
                
                self.log("🔄 配置面板已刷新")
        except Exception as e:
            self.log(f"❌ 刷新配置面板失敗: {str(e)}")
        
    def create_widgets(self):
        """創建主要組件"""
        # 創建主框架
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 創建頂部標題欄
        self.create_header()
        
        # 創建主要內容區域
        self.create_content_area()
        
        # 創建底部狀態欄
        self.create_status_bar()
        
    def create_header(self):
        """創建頂部標題欄"""
        self.header_frame = ctk.CTkFrame(self.main_frame)
        self.header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # 標題
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🎮 Artale Script 控制台",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(side="left", padx=20, pady=15)
        
    def create_content_area(self):
        """創建主要內容區域"""
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 左側面板 (控制面板)
        self.left_panel = ctk.CTkFrame(self.content_frame, width=350)
        self.left_panel.pack(side="left", fill="y", padx=(5, 2.5), pady=5)
        self.left_panel.pack_propagate(False)
        
        # 右側面板 (日誌和設定)
        self.right_panel = ctk.CTkFrame(self.content_frame)
        self.right_panel.pack(side="right", fill="both", expand=True, padx=(2.5, 5), pady=5)
        
        # 創建左側面板內容
        self.create_left_panel()
        
        # 創建右側面板內容
        self.create_right_panel()
        
    def create_left_panel(self):
        """創建左側控制面板"""
        # 登入區域
        self.create_login_section()
        
        # 分隔線
        self.separator1 = ctk.CTkFrame(self.left_panel, height=2)
        self.separator1.pack(fill="x", padx=10, pady=10)
        
        # 腳本控制區域
        self.create_script_control_section()
    
    def create_login_section(self):
        """創建登入區域"""
        # 登入標題
        login_title = ctk.CTkLabel(
            self.left_panel,
            text="🔐 使用者認證",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        login_title.pack(pady=(15, 15))
        
        # 登入框架
        self.login_frame = ctk.CTkFrame(self.left_panel)
        self.login_frame.pack(fill="x", padx=15, pady=5)
        
        # UUID 輸入
        ctk.CTkLabel(self.login_frame, text="UUID:").pack(anchor="w", padx=15, pady=(15, 5))
        self.uuid_entry = ctk.CTkEntry(
            self.login_frame,
            placeholder_text="請輸入您的授權 UUID",
            width=300,
            show="*"  # 隱藏輸入
        )
        self.uuid_entry.pack(padx=15, pady=(0, 15))
        
        # 綁定 Enter 鍵
        self.uuid_entry.bind('<Return>', lambda event: self.handle_login())
        
        # 登入按鈕
        self.login_button = ctk.CTkButton(
            self.login_frame,
            text="🔑 登入",
            command=self.handle_login,
            height=35,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.login_button.pack(pady=(0, 15))
        
        # 登入狀態顯示
        self.login_status_label = ctk.CTkLabel(
            self.login_frame,
            text="狀態: 未登入",
            text_color="gray"
        )
        self.login_status_label.pack(pady=(0, 10))
        
        # 用戶信息顯示區域
        self.user_info_frame = ctk.CTkFrame(self.login_frame)
        self.user_info_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        self.user_info_label = ctk.CTkLabel(
            self.user_info_frame,
            text="",
            font=ctk.CTkFont(size=10),
            wraplength=250
        )
        self.user_info_label.pack(pady=5)
        
        # 會話信息顯示
        self.session_info_label = ctk.CTkLabel(
            self.user_info_frame,
            text="",
            font=ctk.CTkFont(size=9),
            text_color="cyan"
        )
        self.session_info_label.pack(pady=2)
        
    def create_script_control_section(self):
        """創建腳本控制區域"""
        # 腳本控制標題
        script_title = ctk.CTkLabel(
            self.left_panel,
            text="🎮 腳本控制",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        script_title.pack(pady=(15, 10))
        
        # 腳本控制框架
        self.script_frame = ctk.CTkFrame(self.left_panel)
        self.script_frame.pack(fill="x", padx=15, pady=5)
        
        # 腳本狀態顯示
        self.script_status_label = ctk.CTkLabel(
            self.script_frame,
            text="腳本狀態: 未運行",
            font=ctk.CTkFont(size=14)
        )
        self.script_status_label.pack(pady=(15, 10))
        
        # 控制按鈕框架
        button_frame = ctk.CTkFrame(self.script_frame)
        button_frame.pack(fill="x", padx=15, pady=10)
        
        # 開始按鈕
        self.start_button = ctk.CTkButton(
            button_frame,
            text="▶️ 開始腳本",
            command=self.start_script,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            state="disabled"
        )
        self.start_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        # 停止按鈕
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="⏸️ 停止腳本",
            command=self.stop_script,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.pack(side="right", expand=True, fill="x", padx=(5, 0))
        
        # 腳本信息顯示
        info_frame = ctk.CTkFrame(self.script_frame)
        info_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.runtime_label = ctk.CTkLabel(info_frame, text="運行時間: 00:00:00")
        self.runtime_label.pack(pady=5)
        
    def create_right_panel(self):
        """創建右側面板"""
        # 創建選項卡
        self.tabview = ctk.CTkTabview(self.right_panel)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 日誌選項卡
        self.log_tab = self.tabview.add("📋 即時日誌")
        self.create_log_section(self.log_tab)
        
        # 設定選項卡
        self.settings_tab = self.tabview.add("⚙️ 進階設定")
        self.create_settings_section(self.settings_tab)
        
        # 怪物下載器選項卡
        self.monster_tab = self.tabview.add("🎨 怪物下載器")
        self.create_monster_downloader_section(self.monster_tab)
        
        # 會話管理選項卡（僅登入後顯示）
        if self.logged_in.get():
            self.session_tab = self.tabview.add("🔗 會話管理")
            self.create_session_section(self.session_tab)
        
    def create_log_section(self, parent):
        """創建日誌區域"""
        # 日誌文本框
        self.log_text = ctk.CTkTextbox(
            parent,
            wrap="word",
            font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 日誌控制按鈕
        log_control_frame = ctk.CTkFrame(parent)
        log_control_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.clear_log_button = ctk.CTkButton(
            log_control_frame,
            text="🗑️ 清空日誌",
            command=self.clear_log,
            width=100,
            height=30
        )
        self.clear_log_button.pack(side="left", padx=10, pady=10)
        
        # 自動滾動開關
        self.auto_scroll_switch = ctk.CTkSwitch(
            log_control_frame,
            text="自動滾動",
            command=self.toggle_auto_scroll
        )
        self.auto_scroll_switch.pack(side="right", padx=10, pady=10)
        self.auto_scroll_switch.select()  # 默認開啟
        
    def create_settings_section(self, parent):
        """創建設定區域"""
        # 檢查登入狀態和權限
        if not self.logged_in.get():
            # 未登入時顯示提示
            info_label = ctk.CTkLabel(
                parent, 
                text="🔒 請先登入以使用配置設定功能",
                font=ctk.CTkFont(size=14),
                text_color="orange"
            )
            info_label.pack(expand=True)
            return
        
        # 檢查配置權限
        if self.auth_manager and not self.auth_manager.check_permission('config_modify'):
            # 無權限時顯示提示
            no_permission_label = ctk.CTkLabel(
                parent, 
                text="🚫 您沒有修改配置的權限",
                font=ctk.CTkFont(size=14),
                text_color="red"
            )
            no_permission_label.pack(expand=True)
            return
        
        # 添加檢查：確保配置管理器已初始化
        if not hasattr(self, 'config_manager') or self.config_manager is None:
            info_label = ctk.CTkLabel(
                parent, 
                text="配置管理器正在初始化中...\n請稍後刷新此頁面",
                font=ctk.CTkFont(size=12)
            )
            info_label.pack(expand=True)
            return
        
        if self.config_manager:
            try:
                from .config_panel import ConfigPanel
                self.config_panel = ConfigPanel(
                    parent, 
                    self.config_manager, 
                    on_config_changed=self.on_config_changed
                )
                self.log("✅ 配置面板創建完成")
            except Exception as e:
                self.log(f"❌ 配置面板創建失敗: {str(e)}")
                error_label = ctk.CTkLabel(
                    parent, 
                    text=f"配置面板載入失敗:\n{str(e)}\n\n請檢查配置管理器是否正常",
                    font=ctk.CTkFont(size=12)
                )
                error_label.pack(expand=True)
        else:
            info_label = ctk.CTkLabel(
                parent, 
                text="配置管理器未初始化\n無法顯示配置面板",
                font=ctk.CTkFont(size=12)
            )
            info_label.pack(expand=True)
    
    def create_monster_downloader_section(self, parent):
        """創建怪物下載器區域"""
        try:
            # 導入怪物下載器面板
            from .monster_downloader import MonsterDownloaderPanel
            
            # 創建怪物下載器面板
            self.monster_downloader_panel = MonsterDownloaderPanel(parent, self.config_manager)
            self.log("✅ 怪物下載器面板創建完成")
            
        except Exception as e:
            self.log(f"❌ 怪物下載器面板創建失敗: {str(e)}")
            error_label = ctk.CTkLabel(
                parent, 
                text=f"怪物下載器載入失敗:\n{str(e)}\n\n請檢查網路連接和相關依賴",
                font=ctk.CTkFont(size=12),
                text_color="red"
            )
            error_label.pack(expand=True)
    
    def create_session_section(self, parent):
        """創建會話管理區域"""
        # 會話信息框架
        session_info_frame = ctk.CTkFrame(parent)
        session_info_frame.pack(fill="x", padx=10, pady=10)
        
        # 當前會話信息
        current_session_label = ctk.CTkLabel(
            session_info_frame,
            text="📱 當前會話信息",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        current_session_label.pack(pady=(10, 5))
        
        self.current_session_info = ctk.CTkLabel(
            session_info_frame,
            text="載入中...",
            font=ctk.CTkFont(size=12),
            wraplength=400
        )
        self.current_session_info.pack(pady=(5, 15))
        
        # 按鈕框架
        button_frame = ctk.CTkFrame(session_info_frame)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # 刷新會話信息按鈕
        refresh_session_button = ctk.CTkButton(
            button_frame,
            text="🔄 刷新會話信息",
            command=self.refresh_session_info,
            width=150,
            height=30
        )
        refresh_session_button.pack(side="left", padx=5, pady=5)
        
        # 查看所有活躍會話按鈕
        view_sessions_button = ctk.CTkButton(
            button_frame,
            text="👥 查看所有會話",
            command=self.show_all_sessions,
            width=150,
            height=30
        )
        view_sessions_button.pack(side="right", padx=5, pady=5)
        
        # 初始載入會話信息
        self.refresh_session_info()
    
    def refresh_session_info(self):
        """刷新會話信息"""
        if not self.auth_manager or not self.logged_in.get():
            return
        
        try:
            current_user = self.auth_manager.get_current_user()
            if current_user and self.auth_manager.current_session_id:
                session_id = self.auth_manager.current_session_id
                user_data = current_user['data']
                
                info_text = f"會話ID: {session_id[:16]}...\n"
                info_text += f"用戶: {user_data.get('display_name', 'Unknown')}\n"
                info_text += f"登入時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                info_text += f"心跳狀態: {'運行中' if self.auth_manager.heartbeat_running else '已停止'}"
                
                self.current_session_info.configure(text=info_text)
            else:
                self.current_session_info.configure(text="無會話信息")
                
        except Exception as e:
            self.current_session_info.configure(text=f"載入失敗: {str(e)}")
    
    def show_all_sessions(self):
        """顯示所有活躍會話"""
        if not self.auth_manager:
            messagebox.showerror("錯誤", "認證管理器未初始化")
            return
        
        try:
            sessions = self.auth_manager.get_active_sessions()
            
            if not sessions:
                messagebox.showinfo("會話信息", "目前沒有活躍會話")
                return
            
            # 創建會話信息窗口
            session_window = ctk.CTkToplevel(self.root)
            session_window.title("活躍會話列表")
            session_window.geometry("600x400")
            
            # 會話列表框架
            list_frame = ctk.CTkScrollableFrame(session_window)
            list_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # 標題
            title_label = ctk.CTkLabel(
                list_frame,
                text="🔗 目前所有活躍會話",
                font=ctk.CTkFont(size=16, weight="bold")
            )
            title_label.pack(pady=10)
            
            # 顯示每個會話
            for i, session in enumerate(sessions, 1):
                session_frame = ctk.CTkFrame(list_frame)
                session_frame.pack(fill="x", padx=5, pady=5)
                
                session_text = f"{i}. {session['user_display_name']}\n"
                session_text += f"   會話ID: {session['session_id'][:16]}...\n"
                session_text += f"   登入時間: {session['created_at']}\n"
                session_text += f"   最後活動: {session['last_heartbeat']}"
                
                session_label = ctk.CTkLabel(
                    session_frame,
                    text=session_text,
                    font=ctk.CTkFont(size=11),
                    anchor="w"
                )
                session_label.pack(padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("錯誤", f"載入會話列表失敗:\n{str(e)}")
    
    def on_config_changed(self, changed_configs: dict):
        """配置更改回調"""
        self.log(f"⚙️ 配置已更新: {len(changed_configs)} 項")
        
        # 通知腳本包裝器配置已更改
        if self.script_wrapper:
            for key, value in changed_configs.items():
                self.script_wrapper.send_command('update_config', config={key: value})
        
        # 記錄更改的配置
        for key, value in changed_configs.items():
            self.log(f"   {key} = {value}")
        
    def create_status_bar(self):
        """創建底部狀態欄"""
        self.status_frame = ctk.CTkFrame(self.main_frame, height=40)
        self.status_frame.pack(fill="x", padx=5, pady=(5, 5))
        self.status_frame.pack_propagate(False)
        
        # 左側狀態信息
        self.status_left = ctk.CTkLabel(
            self.status_frame,
            text="就緒",
            anchor="w"
        )
        self.status_left.pack(side="left", padx=15, pady=10)
        
        # 中間用戶信息
        self.user_status_label = ctk.CTkLabel(
            self.status_frame,
            text="未登入",
            anchor="center"
        )
        self.user_status_label.pack(pady=10)
        
        # 右側狀態信息
        self.status_right = ctk.CTkLabel(
            self.status_frame,
            text="Artale Script v1.1",
            anchor="e"
        )
        self.status_right.pack(side="right", padx=15, pady=10)
        
    # ================ 登入登出事件處理函數 ================
        
    def handle_login(self):
        """處理登入 - 自動強制踢掉其他會話"""
        if self.login_in_progress:
            return
            
        if self.logged_in.get():
            # 如果已經登入，則執行登出
            self.handle_logout()
            return
        
        # 檢查認證系統
        if not self.auth_manager or not self.auth_manager.is_initialized:
            messagebox.showerror("錯誤", "認證系統未初始化\n請檢查網路連接和配置文件")
            return
        
        uuid = self.uuid_entry.get().strip()
        if not uuid:
            messagebox.showerror("錯誤", "請輸入 UUID")
            return
        
        # 開始登入程序 - 默認使用強制登入
        self.login_in_progress = True
        self.login_button.configure(state="disabled", text="🔄 認證中...")
        self.login_status_label.configure(text="狀態: 認證中...", text_color="orange")
        
        # 在後台線程中執行認證 - 直接使用強制登入
        threading.Thread(target=self._authenticate_background, args=(uuid, True), daemon=True).start()
        
    def _authenticate_background(self, uuid: str, force_login: bool):
        """在後台執行認證"""
        try:
            # 執行認證
            success, message, user_data = self.auth_manager.authenticate_user(uuid, force_login)
            
            # 在主線程中更新 UI
            self.root.after(0, self._handle_auth_result, success, message, user_data, force_login)
            
        except Exception as e:
            self.root.after(0, self._handle_auth_result, False, f"認證過程發生錯誤: {str(e)}", None, force_login)
    
    def _handle_auth_result(self, success: bool, message: str, user_data: dict, was_force_login: bool):
        """處理認證結果"""
        self.login_in_progress = False
        
        if success:
            self._login_success(user_data, was_force_login)
        else:
            self._login_failed(message, was_force_login)
        
        # 恢復登入按鈕狀態
        self.login_button.configure(state="normal")
    
    def _login_success(self, user_data: dict, was_force_login: bool):
        """登入成功處理"""
        self.logged_in.set(True)
        
        # 獲取用戶顯示信息
        user_display = user_data.get('display_name', 'Unknown User')
        self.current_user.set(f"用戶: {user_display}")
        self.login_status_label.configure(text="狀態: 已登入", text_color="green")
        self.login_button.configure(text="🔓 登出")
        
        # 顯示用戶信息
        self._update_user_info_display(user_data)
        
        # 顯示會話信息
        if self.auth_manager.current_session_id:
            session_display = f"會話: {self.auth_manager.current_session_id[:8]}..."
            self.session_info_label.configure(text=session_display)
        
        # 更新狀態欄
        self.user_status_label.configure(text=f"已登入: {user_display}")
        
        # 啟用腳本控制按鈕（如果有腳本權限）
        if self.auth_manager.check_permission('script_access'):
            self.start_button.configure(state="normal")
            if was_force_login:
                self.log(f"✅ 登入成功: {user_display}")
            else:
                self.log(f"✅ 登入成功: {user_display}")
        else:
            self.log(f"⚠️ 登入成功但無腳本權限: {user_display}")
            messagebox.showwarning("權限不足", "您沒有執行腳本的權限")
        
        # 刷新界面以顯示會話管理選項卡
        self._add_session_tab()
        
        # 刷新配置面板以反映權限變化
        self.refresh_config_panel()
        
        self.update_status("已登入")
        
    def _add_session_tab(self):
        """添加會話管理選項卡"""
        try:
            # 檢查是否已存在會話選項卡
            try:
                self.tabview.tab("🔗 會話管理")
                return  # 已存在，無需重複添加
            except:
                pass  # 不存在，繼續添加
            
            # 添加會話管理選項卡
            session_tab = self.tabview.add("🔗 會話管理")
            self.create_session_section(session_tab)
        except Exception as e:
            self.log(f"⚠️ 添加會話選項卡失敗: {str(e)}")
    
    def _login_failed(self, message: str, was_force_login: bool):
        """登入失敗處理"""
        self.login_status_label.configure(text="狀態: 認證失敗", text_color="red")
        self.login_button.configure(text="🔑 登入")
        
        self.log(f"❌ 登入失敗: {message}")
        messagebox.showerror("登入失敗", f"認證失敗:\n{message}")
        
        # 清空 UUID 輸入框
        self.uuid_entry.delete(0, tk.END)
        
    def _update_user_info_display(self, user_data: dict):
        """更新用戶信息顯示"""
        info_lines = []
        
        # 顯示用戶名
        if 'display_name' in user_data:
            info_lines.append(f"用戶: {user_data['display_name']}")
        
        # 顯示權限
        permissions = user_data.get('permissions', {})
        perm_list = []
        if permissions.get('script_access', False):
            perm_list.append("腳本執行")
        if permissions.get('config_modify', False):
            perm_list.append("配置修改")
        
        if perm_list:
            info_lines.append(f"權限: {', '.join(perm_list)}")
        
        # 顯示到期時間
        if 'expires_at' in user_data:
            expires_str = str(user_data['expires_at'])
            if 'T' in expires_str:
                expires_str = expires_str.split('T')[0]  # 只顯示日期部分
            info_lines.append(f"到期: {expires_str}")
        
        # 顯示登入次數
        if 'login_count' in user_data:
            info_lines.append(f"登入次數: {user_data['login_count']}")
        
        self.user_info_label.configure(text="\n".join(info_lines))
        
    def handle_logout(self):
        """處理登出"""
        # 如果腳本正在運行，先停止
        if self.script_running:
            self.stop_script()
        
        # Firebase 登出
        if self.auth_manager:
            self.auth_manager.logout_user()
            
        self.logged_in.set(False)
        self.current_user.set("未登入")
        self.login_status_label.configure(text="狀態: 未登入", text_color="gray")
        self.login_button.configure(text="🔑 登入")
        
        # 清空用戶信息顯示
        self.user_info_label.configure(text="")
        self.session_info_label.configure(text="")
        
        # 更新狀態欄
        self.user_status_label.configure(text="未登入")
        
        # 禁用腳本控制按鈕
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        
        # 清空 UUID 輸入框
        self.uuid_entry.delete(0, tk.END)
        
        # 移除會話管理選項卡
        try:
            self.tabview.delete("🔗 會話管理")
        except:
            pass
        
        # 刷新配置面板
        self.refresh_config_panel()
        
        self.log("🔓 已登出")
        self.update_status("未登入")
        
    # ================ 腳本控制事件處理函數 ================
        
    def start_script(self):
        """開始腳本"""
        # 檢查登入狀態
        if not self.logged_in.get():
            messagebox.showerror("錯誤", "請先登入")
            return
        
        # 檢查腳本權限
        if not self.auth_manager.check_permission('script_access'):
            messagebox.showerror("權限不足", "您沒有執行腳本的權限")
            return
            
        if not self.script_wrapper:
            self.log("❌ 腳本包裝器未初始化")
            messagebox.showerror("錯誤", "腳本包裝器未初始化")
            return
            
        if self.script_running:
            self.log("⚠️ 腳本已在運行中")
            return
            
        try:
            # 驗證會話是否仍然有效
            if not self.auth_manager.validate_session():
                messagebox.showerror("會話失效", "登入會話已失效，請重新登入")
                self.handle_logout()
                return
            
            # 使用腳本包裝器啟動腳本
            success = self.script_wrapper.start_script()
            
            if success:
                self.script_running = True
                self.script_status.set("運行中")
                self.script_status_label.configure(text="腳本狀態: 運行中", text_color="green")
                
                # 更新按鈕狀態
                self.start_button.configure(state="disabled")
                self.stop_button.configure(state="normal")
                
                self.log("🚀 腳本已開始運行")
                self.update_status("腳本運行中")
            else:
                self.log("❌ 腳本啟動失敗")
                messagebox.showerror("錯誤", "腳本啟動失敗，請檢查日誌")
            
        except Exception as e:
            self.log(f"❌ 啟動腳本失敗: {str(e)}")
            messagebox.showerror("錯誤", f"啟動腳本失敗: {str(e)}")
            
    def stop_script(self):
        """停止腳本"""
        if not self.script_wrapper:
            self.log("⚠️ 腳本包裝器未初始化")
            return
            
        if not self.script_running:
            self.log("⚠️ 腳本未在運行")
            return
            
        try:
            # 使用腳本包裝器停止腳本
            success = self.script_wrapper.stop_script()
            
            if success:
                self.script_running = False
                self.script_status.set("已停止")
                self.script_status_label.configure(text="腳本狀態: 已停止", text_color="red")
                
                # 更新按鈕狀態
                self.start_button.configure(state="normal" if self.logged_in.get() else "disabled")
                self.stop_button.configure(state="disabled")
                
                self.log("⏸️ 腳本已停止")
                self.update_status("已停止")
            else:
                self.log("❌ 腳本停止失敗")
                
        except Exception as e:
            self.log(f"❌ 停止腳本失敗: {str(e)}")
            messagebox.showerror("錯誤", f"停止腳本失敗: {str(e)}")
        
    # ================ 其他事件處理函數 ================
        
    def clear_log(self):
        """清空日誌"""
        self.log_text.delete("1.0", tk.END)
        self.log("日誌已清空")
        
    def toggle_auto_scroll(self):
        """切換自動滾動"""
        enabled = self.auto_scroll_switch.get()
        status = "啟用" if enabled else "禁用"
        self.log(f"📜 自動滾動已{status}")
        
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
            self.root.after(0, self._update_log_text, formatted_message)
            
    def _update_log_text(self, message):
        """更新日誌文本（主線程中執行）"""
        self.log_text.insert(tk.END, message)
        
        # 自動滾動到底部
        if self.auto_scroll_switch.get():
            self.log_text.see(tk.END)
            
        # 限制日誌長度，避免內存過度使用
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:  # 保留最新的1000行
            lines_to_keep = '\n'.join(lines[-1000:])
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", lines_to_keep)
            
    def update_status(self, status):
        """更新狀態欄"""
        self.status_left.configure(text=status)
        
    def on_closing(self):
        """處理窗口關閉事件"""
        if self.script_running:
            # 如果腳本正在運行，詢問是否確認關閉
            result = messagebox.askyesno(
                "確認關閉",
                "腳本正在運行中，確定要關閉程式嗎？\n\n關閉程式將停止所有腳本執行並登出。"
            )
            if not result:
                return
                
            # 停止腳本
            self.stop_script()
            
            # 等待腳本停止
            if self.script_wrapper:
                import time
                for _ in range(10):  # 最多等待1秒
                    if not self.script_wrapper.is_script_running():
                        break
                    time.sleep(0.1)
        
        # 登出用戶
        if self.logged_in.get():
            self.handle_logout()
        
        # 清理腳本包裝器資源
        if self.script_wrapper:
            self.script_wrapper.cleanup()
        
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """運行主程式"""
        # 添加歡迎消息
        self.log("🎮 歡迎使用 Artale Script GUI")
        
        # 檢查認證系統狀態
        if self.auth_manager and self.auth_manager.is_initialized:
            self.log("✅ 認證系統已就緒")
            self.log("🔐 請輸入您的授權 UUID 以開始使用")
        else:
            self.log("❌ 認證系統初始化失敗")
            self.log("請檢查網路連接和配置文件")
        
        self.log("💡 提示: 只有授權用戶才能使用腳本功能")
        self.log("🎯 登入後確保遊戲視窗已開啟，然後點擊開始腳本")
        self.log("🎨 怪物下載器功能現已整合，可在對應選項卡中使用")
        
        # 如果配置管理器初始化失敗，提示用戶
        if not self.config_manager:
            self.log("⚠️ 配置管理器未正常初始化，配置面板可能無法使用")
        
        # 啟動主循環
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log("程式被用戶中斷")
        except Exception as e:
            self.log(f"程式運行錯誤: {str(e)}")
            messagebox.showerror("錯誤", f"程式運行錯誤:\n{str(e)}")
        finally:
            # 確保資源正確清理
            if self.script_wrapper:
                self.script_wrapper.cleanup()
            if self.auth_manager and self.logged_in.get():
                self.auth_manager.logout_user()
                
    # 在 MainWindow 類別中新增方法

    def check_for_updates(self):
        """檢查更新"""
        try:
            from core.updater import AutoUpdater
            updater = AutoUpdater("ucheng0921/artale-script")  # 替換成你的 repo
            
            has_update, update_info = updater.check_for_updates()
            
            if has_update:
                self.show_update_dialog(update_info, updater)
            else:
                messagebox.showinfo("更新檢查", "目前已是最新版本")
                
        except Exception as e:
            messagebox.showerror("更新檢查失敗", f"無法檢查更新: {str(e)}")

    def show_update_dialog(self, update_info, updater):
        """顯示更新對話框"""
        from tkinter import messagebox
        
        message = f"""發現新版本: {update_info['version']}

    更新說明:
    {update_info['release_notes']}

    是否立即更新？
    """
        
        result = messagebox.askyesno("發現更新", message)
        
        if result:
            # 在背景執行更新
            import threading
            
            def update_thread():
                if updater.auto_update():
                    self.root.after(0, lambda: messagebox.showinfo(
                        "更新完成", 
                        "更新已完成！\n請重新啟動程式以使用新版本。"
                    ))
            
            threading.Thread(target=update_thread, daemon=True).start()