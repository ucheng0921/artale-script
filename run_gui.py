"""
Artale Script GUI 啟動器 - 重構版本
"""
import os
import sys
from pathlib import Path

# 確保專案根目錄在 Python 路徑中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    """主要入口點"""
    try:
        # 檢查環境
        if not check_environment():
            return
        
        # 檢查更新 (可選)
        check_updates = input("是否檢查更新? (Y/n): ").strip().lower()
        if check_updates in ('', 'y', 'yes'):
            try:
                from core.updater import AutoUpdater
                updater = AutoUpdater("ucheng0921/artale-script")
                has_update, update_info = updater.check_for_updates()
                
                if has_update:
                    print(f"🆕 發現新版本: {update_info['version']}")
                    update_now = input("是否立即更新? (y/N): ").strip().lower()
                    if update_now == 'y':
                        if updater.auto_update():
                            print("🎉 更新完成！請重新啟動程式")
                            return
            except Exception as e:
                print(f"更新檢查失敗: {e}")
        
        # 啟動 GUI
        from gui import run_gui
        run_gui()
        
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

def check_environment():
    """檢查執行環境"""
    # 檢查 .env 檔案
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠️ 找不到 .env 檔案")
        print("請執行: python scripts/setup_project.py")
        return False
    
    # 檢查資產目錄
    assets_dir = project_root / "assets" / "game_resources"
    if not assets_dir.exists():
        print("⚠️ 找不到遊戲資源目錄")
        print("請執行: python scripts/setup_project.py")
        return False
    
    return True

if __name__ == "__main__":
    main()