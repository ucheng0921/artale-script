# 建立測試腳本 test_updater.py
from core.updater import AutoUpdater

# 測試更新檢查
updater = AutoUpdater("yourusername/artale-script")  # 這裡需要你的實際 repo
has_update, update_info = updater.check_for_updates()

print(f"有更新: {has_update}")
if update_info:
    print(f"更新資訊: {update_info}")