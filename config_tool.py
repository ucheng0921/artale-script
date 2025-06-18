"""
配置文件管理工具 - 用於管理外部配置文件
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import shutil

def get_config_path():
    """獲取配置文件路徑"""
    # 如果是exe環境
    if hasattr(sys, '_MEIPASS'):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
    
    return app_dir / "user_config.json"

def get_template_path():
    """獲取模板路徑"""
    if hasattr(sys, '_MEIPASS'):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
    
    return app_dir / "config_template.json"

def check_config_status():
    """檢查配置文件狀態"""
    config_path = get_config_path()
    
    print("📋 配置文件狀態檢查")
    print("=" * 50)
    print(f"配置文件路徑: {config_path}")
    
    if config_path.exists():
        size = config_path.stat().st_size
        modified = datetime.fromtimestamp(config_path.stat().st_mtime)
        
        print(f"✅ 配置文件存在")
        print(f"📏 文件大小: {size} 字節")
        print(f"⏰ 修改時間: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 嘗試讀取內容
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            configs = config_data.get('configs', {})
            print(f"⚙️ 配置項數量: {len(configs)}")
            print(f"📝 版本: {config_data.get('_version', 'unknown')}")
            
        except Exception as e:
            print(f"❌ 讀取配置文件失敗: {e}")
    else:
        print("❌ 配置文件不存在")
        print("💡 首次啟動程式並修改設定後會自動創建")

def backup_config():
    """備份配置文件"""
    config_path = get_config_path()
    
    if not config_path.exists():
        print("❌ 配置文件不存在，無法備份")
        return False
    
    # 創建備份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = config_path.parent / f"user_config_backup_{timestamp}.json"
    
    try:
        shutil.copy2(config_path, backup_path)
        print(f"✅ 配置已備份到: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return False

def restore_config():
    """恢復配置文件"""
    config_dir = get_config_path().parent
    backup_files = list(config_dir.glob("user_config_backup_*.json"))
    
    if not backup_files:
        print("❌ 找不到備份文件")
        return False
    
    print("\n📋 可用的備份文件:")
    for i, backup_file in enumerate(backup_files, 1):
        modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"  {i}. {backup_file.name} ({modified.strftime('%Y-%m-%d %H:%M:%S')})")
    
    try:
        choice = int(input("\n請選擇要恢復的備份文件 (輸入編號): "))
        if 1 <= choice <= len(backup_files):
            selected_backup = backup_files[choice - 1]
            
            # 備份當前配置
            current_config = get_config_path()
            if current_config.exists():
                backup_config()
            
            # 恢復選定的備份
            shutil.copy2(selected_backup, current_config)
            print(f"✅ 配置已從備份恢復: {selected_backup.name}")
            return True
        else:
            print("❌ 無效的選擇")
            return False
    except ValueError:
        print("❌ 請輸入有效的數字")
        return False
    except Exception as e:
        print(f"❌ 恢復失敗: {e}")
        return False

def reset_config():
    """重置配置文件"""
    config_path = get_config_path()
    
    if not config_path.exists():
        print("❌ 配置文件不存在，無需重置")
        return False
    
    print("⚠️ 這將刪除所有自定義配置，恢復為默認設定")
    confirm = input("請輸入 'RESET' 確認重置: ")
    
    if confirm != 'RESET':
        print("❌ 操作已取消")
        return False
    
    # 先備份
    if backup_config():
        try:
            config_path.unlink()
            print("✅ 配置文件已重置")
            print("💡 下次啟動程式時將使用默認設定")
            return True
        except Exception as e:
            print(f"❌ 重置失敗: {e}")
            return False
    else:
        print("❌ 備份失敗，取消重置操作")
        return False

def export_template():
    """導出配置模板"""
    try:
        # 嘗試從程式中獲取模板
        sys.path.insert(0, str(Path(__file__).parent))
        
        from gui.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        template_path = get_template_path()
        
        success = config_manager.export_config_template(str(template_path))
        
        if success:
            print(f"✅ 配置模板已導出: {template_path}")
        else:
            print("❌ 導出模板失敗")
            
    except Exception as e:
        print(f"❌ 導出模板失敗: {e}")
        print("💡 請確保在程式目錄中執行此工具")

def view_config():
    """查看配置內容"""
    config_path = get_config_path()
    
    if not config_path.exists():
        print("❌ 配置文件不存在")
        return
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        print("\n📋 當前配置內容:")
        print("=" * 60)
        
        configs = config_data.get('configs', {})
        
        # 按類別分組顯示
        categories = {
            "怪物檢測與攻擊": ['ENABLED_MONSTERS', 'JUMP_KEY', 'ATTACK_KEY', 'SECONDARY_ATTACK_KEY', 
                           'ENABLE_SECONDARY_ATTACK', 'PRIMARY_ATTACK_CHANCE', 'SECONDARY_ATTACK_CHANCE',
                           'ATTACK_RANGE_X', 'JUMP_ATTACK_MODE'],
            "被動技能": ['ENABLE_PASSIVE_SKILLS', 'PASSIVE_SKILL_1_KEY', 'PASSIVE_SKILL_2_KEY',
                      'PASSIVE_SKILL_3_KEY', 'PASSIVE_SKILL_4_KEY'],
            "移動系統": ['ENABLE_ENHANCED_MOVEMENT', 'ENABLE_JUMP_MOVEMENT', 'ENABLE_DASH_MOVEMENT',
                      'DASH_SKILL_KEY', 'DASH_MOVEMENT_CHANCE'],
            "其他設定": []  # 用於未分類的配置
        }
        
        # 顯示分類配置
        for category, keys in categories.items():
            if category == "其他設定":
                # 找出未分類的配置
                categorized_keys = set()
                for cat_keys in categories.values():
                    categorized_keys.update(cat_keys)
                keys = [k for k in configs.keys() if k not in categorized_keys]
            
            if keys:
                print(f"\n📁 {category}:")
                for key in keys:
                    if key in configs:
                        value = configs[key]
                        print(f"   {key} = {value}")
        
        print("\n" + "=" * 60)
        print(f"📊 總計 {len(configs)} 項配置")
        
    except Exception as e:
        print(f"❌ 讀取配置失敗: {e}")

def clean_backups():
    """清理舊備份文件"""
    config_dir = get_config_path().parent
    backup_files = list(config_dir.glob("user_config_backup_*.json"))
    
    if not backup_files:
        print("❌ 沒有找到備份文件")
        return
    
    print(f"\n📋 找到 {len(backup_files)} 個備份文件")
    
    if len(backup_files) <= 5:
        print("💡 備份文件數量較少，建議保留")
        return
    
    # 按修改時間排序，保留最新的5個
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    files_to_delete = backup_files[5:]  # 保留前5個最新的
    
    print(f"🗑️ 將刪除 {len(files_to_delete)} 個舊備份文件:")
    for backup_file in files_to_delete:
        modified = datetime.fromtimestamp(backup_file.stat().st_mtime)
        print(f"   - {backup_file.name} ({modified.strftime('%Y-%m-%d %H:%M:%S')})")
    
    confirm = input("\n確認刪除? (y/N): ")
    if confirm.lower() == 'y':
        deleted_count = 0
        for backup_file in files_to_delete:
            try:
                backup_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"❌ 刪除 {backup_file.name} 失敗: {e}")
        
        print(f"✅ 已刪除 {deleted_count} 個備份文件")
    else:
        print("❌ 操作已取消")

def main():
    """主函數"""
    while True:
        print("\n" + "=" * 60)
        print("⚙️ ArtaleScript 配置文件管理工具")
        print("=" * 60)
        print("1. 檢查配置狀態")
        print("2. 查看配置內容") 
        print("3. 備份配置文件")
        print("4. 恢復配置文件")
        print("5. 重置配置文件")
        print("6. 導出配置模板")
        print("7. 清理舊備份")
        print("0. 退出")
        print("-" * 60)
        
        try:
            choice = input("請選擇操作 (0-7): ").strip()
            
            if choice == '0':
                print("👋 再見！")
                break
            elif choice == '1':
                check_config_status()
            elif choice == '2':
                view_config()
            elif choice == '3':
                backup_config()
            elif choice == '4':
                restore_config()
            elif choice == '5':
                reset_config()
            elif choice == '6':
                export_template()
            elif choice == '7':
                clean_backups()
            else:
                print("❌ 無效的選擇，請重新輸入")
            
            if choice != '0':
                input("\n按 Enter 鍵繼續...")
                
        except KeyboardInterrupt:
            print("\n\n👋 程式被中斷，再見！")
            break
        except Exception as e:
            print(f"\n❌ 發生錯誤: {e}")
            input("按 Enter 鍵繼續...")

if __name__ == "__main__":
    main()