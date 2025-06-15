"""
Artale Script GUI 模組 - Render 服務器認證版
"""

__version__ = "1.2.0"
__author__ = "Artale Script Team"
__description__ = "Artale Script 圖形用戶界面 - 支援 Render 服務器認證"

print("🔥 正在載入 Render 服務器認證系統...")

try:
    # 測試認證系統連接
    from .firebase_auth import get_auth_manager
    
    # 創建認證管理器實例來測試
    auth_manager = get_auth_manager()
    
    if auth_manager.is_initialized:
        print("✅ Render 認證系統連接成功")
        
        # 載入主視窗
        from .main_window import MainWindow
        print("✅ 已載入 Render 認證版本主視窗")
        
        # 導入其他認證相關模組
        from .firebase_auth import initialize_auth
        __all__ = ['MainWindow', 'get_auth_manager', 'initialize_auth']
        
    else:
        print("❌ Render 認證系統連接失敗")
        print("📋 可能的原因:")
        print("   1. 網路連接問題")
        print("   2. Render 服務器未啟動")
        print("   3. 服務器 URL 配置錯誤")
        print("\n🔧 解決方案:")
        print("   1. 檢查網路連接")
        print("   2. 確認 Render 服務狀態")
        print("   3. 檢查 firebase_auth.py 中的 server_url")
        
        raise ImportError("Render 認證系統連接失敗，無法使用程式")

except ImportError as e:
    print(f"❌ 認證模組載入失敗: {e}")
    print("🔧 請確保以下文件存在:")
    print("   - gui/firebase_auth.py")
    print("   - gui/main_window_integrated_with_firebase.py")
    print("   - 已安裝 requests: pip install requests")
    
    raise ImportError(f"認證系統必需組件缺失: {e}")

except Exception as e:
    print(f"❌ 認證系統載入錯誤: {e}")
    raise

def run_gui():
    """運行 GUI 應用程式"""
    try:
        print("🚀 啟動 Render 認證版 GUI...")
        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"❌ GUI 運行失敗: {str(e)}")
        raise