"""
專案初始化腳本
完整設定 Artale Script 專案環境
"""
import os
import shutil
import sys
from pathlib import Path
import subprocess

def setup_project():
    """設定專案環境"""
    print("🚀 開始設定 Artale Script 專案...")
    print("=" * 60)
    
    base_dir = Path(__file__).parent.parent
    print(f"📁 專案目錄: {base_dir}")
    
    # 1. 檢查 Python 版本
    print("\n🐍 檢查 Python 版本...")
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        print(f"   當前版本: {sys.version}")
        return False
    print(f"✅ Python 版本: {sys.version.split()[0]}")
    
    # 2. 建立環境檔案
    print("\n📄 設定環境檔案...")
    env_example = base_dir / ".env.example"
    env_file = base_dir / ".env"
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ 已從 .env.example 建立 .env 檔案")
    elif env_file.exists():
        print("✅ .env 檔案已存在")
    else:
        print("⚠️ 找不到 .env.example，建立基本 .env 檔案")
        create_basic_env_file(env_file)
    
    # 3. 建立並檢查目錄結構
    print("\n📂 檢查目錄結構...")
    create_directory_structure(base_dir)
    
    # 4. 檢查資產目錄
    print("\n🎮 設定遊戲資源目錄...")
    setup_assets_directory(base_dir)
    
    # 5. 檢查依賴
    print("\n📦 檢查依賴套件...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"❌ 缺少套件: {', '.join(missing_packages)}")
        print("\n🔧 嘗試自動安裝缺少的套件...")
        
        install_success = install_missing_packages(missing_packages)
        if not install_success:
            print("❌ 自動安裝失敗，請手動執行:")
            print("   pip install -r requirements.txt")
            return False
    
    print("✅ 所有依賴套件都已安裝")
    
    # 6. 修復 import 語句
    print("\n🔧 修復 import 語句...")
    fix_import_statements(base_dir)
    
    # 7. 建立啟動腳本
    print("\n🚀 建立啟動腳本...")
    create_launcher_scripts(base_dir)
    
    # 8. 驗證設定
    print("\n✅ 驗證專案設定...")
    verify_setup(base_dir)
    
    print("\n" + "=" * 60)
    print("🎉 專案設定完成！")
    print("\n📋 下一步操作:")
    print("1. 📁 將遊戲圖片檔案放入 assets/game_resources/ 目錄")
    print("2. ⚙️ 編輯 .env 檔案調整您的配置")
    print("3. 🎮 執行 GUI 版本: python run_gui.py")
    print("4. 💻 或執行命令列版本: python main.py")
    print("\n📚 更多說明請查看 docs/ 目錄中的文檔")
    
    return True

def create_basic_env_file(env_file):
    """建立基本的環境檔案"""
    basic_env_content = """# Artale Script 環境變數配置
# 基礎路徑配置
WORKING_DIR=./
ASSETS_DIR=./assets/game_resources
SCREENSHOTS_DIR=./assets/game_resources/screenshots

# 遊戲視窗設定
WINDOW_NAME=MapleStory Worlds-Artale (繁體中文版)

# Render 後端 API 設定
RENDER_SERVER_URL=https://artale-auth-service.onrender.com

# 檢測參數
DETECTION_INTERVAL=0.01
MATCH_THRESHOLD=0.6
Y_OFFSET=50

# 調試設定
DEBUG_MODE=false
LOG_LEVEL=INFO
"""
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(basic_env_content)
    print("✅ 已建立基本 .env 檔案")

def create_directory_structure(base_dir):
    """建立目錄結構"""
    directories = [
        "core",
        "gui/components", 
        "assets/game_resources",
        "assets/game_resources/monsters",
        "assets/game_resources/change",
        "assets/game_resources/rope", 
        "assets/game_resources/Detection",
        "assets/game_resources/screenshots",
        "docs",
        "scripts",
        "tests",
        "logs"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 建立目錄: {dir_path}")
        else:
            print(f"⏭️ 目錄已存在: {dir_path}")
    
    # 建立 __init__.py 檔案
    init_files = [
        "core/__init__.py",
        "gui/__init__.py", 
        "scripts/__init__.py",
        "tests/__init__.py"
    ]
    
    for init_file in init_files:
        init_path = base_dir / init_file
        if not init_path.exists():
            with open(init_path, 'w', encoding='utf-8') as f:
                module_name = init_file.split('/')[0]
                f.write(f'"""\n{module_name.title()} 模組\n"""\n')
            print(f"✅ 建立: {init_file}")

def setup_assets_directory(base_dir):
    """設定資產目錄"""
    assets_dir = base_dir / "assets" / "game_resources"
    
    # 建立說明檔案
    readme_path = assets_dir / "README.md"
    if not readme_path.exists():
        readme_content = """# 🎮 遊戲資源檔案

請將您的遊戲圖片檔案放置在此目錄中。

## 📁 必需檔案：
- `medal.png` - 角色圖示 (用於角色檢測)
- `sign_text.png` - 標誌文字 (用於特殊事件檢測)
- `rune_text.png` - 符文文字 (用於符文檢測)
- `red.png` - 紅點圖示 (用於玩家檢測)

## 📂 目錄結構：game_resources/
├── monsters/          # 怪物圖片資料夾
│   ├── monster1/      # 第一種怪物的所有圖片
│   ├── monster2/      # 第二種怪物的所有圖片
│   └── monster3/      # 第三種怪物的所有圖片
├── change/           # 換頻道相關圖片
│   ├── change0.png   # 換頻道界面圖片
│   ├── change1.png   # 頻道選項圖片
│   ├── change2.png
│   ├── change3.png
│   ├── change4.png
│   └── change5.png
├── rope/            # 繩索圖片 (各種繩索樣式)
├── Detection/       # 方向檢測圖片 (符文解謎用)
└── screenshots/     # 截圖儲存目錄 (自動建立)## ⚠️ 重要說明：
- 這些檔案因遊戲版權問題不包含在程式碼中
- 您需要自行從遊戲中截取相應的圖片
- 圖片格式支援：PNG, JPG, JPEG, BMP, WEBP
- 建議使用 PNG 格式以獲得最佳檢測效果

## 🔧 設定提示：
1. 使用截圖工具擷取遊戲中的相應元素
2. 確保圖片背景乾淨，減少干擾元素
3. 怪物圖片應包含多種狀態和角度
4. 測試時可先從少量圖片開始，逐步增加
"""
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print("✅ 已建立遊戲資源說明文檔")
    
    # 檢查是否有遊戲資源檔案
    resource_files = list(assets_dir.glob("*.png")) + list(assets_dir.glob("*.jpg"))
    if resource_files:
        print(f"✅ 找到 {len(resource_files)} 個遊戲資源檔案")
    else:
        print("⚠️ 未找到遊戲資源檔案，請參考 assets/game_resources/README.md")

def check_dependencies():
    """檢查依賴套件"""
    print("   檢查必要套件...")
    
    required_packages = {
        "customtkinter": "customtkinter", 
        "PIL": "pillow",
        "cv2": "opencv-python", 
        "numpy": "numpy",
        "pyautogui": "pyautogui", 
        "requests": "requests", 
        "dotenv": "python-dotenv", 
        "psutil": "psutil"
    }
    
    missing = []
    for import_name, package_name in required_packages.items():
        try:
            if import_name == "PIL":
                import PIL
                print(f"   ✅ {package_name}")
            elif import_name == "cv2":
                import cv2
                print(f"   ✅ {package_name}")
            elif import_name == "dotenv":
                from dotenv import load_dotenv
                print(f"   ✅ {package_name}")
            else:
                __import__(import_name)
                print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name}")
            missing.append(package_name)
    
    # Windows 特殊檢查
    if sys.platform == "win32":
        try:
            import win32gui
            print(f"   ✅ pywin32")
        except ImportError:
            print(f"   ❌ pywin32")
            missing.append("pywin32")
    
    return missing

def install_missing_packages(missing_packages):
    """嘗試自動安裝缺少的套件"""
    try:
        for package in missing_packages:
            print(f"   正在安裝 {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
                timeout=300  # 5分鐘超時
            )
            
            if result.returncode == 0:
                print(f"   ✅ {package} 安裝成功")
            else:
                print(f"   ❌ {package} 安裝失敗: {result.stderr}")
                return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("   ❌ 安裝超時")
        return False
    except Exception as e:
        print(f"   ❌ 安裝過程發生錯誤: {e}")
        return False

def fix_import_statements(base_dir):
    """修復 import 語句"""
    try:
        # 檢查是否存在修復腳本
        fix_script = base_dir / "scripts" / "fix_imports.py"
        if fix_script.exists():
            print("   執行 import 修復腳本...")
            
            # 動態執行修復腳本
            spec = importlib.util.spec_from_file_location("fix_imports", fix_script)
            fix_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fix_module)
            
            if hasattr(fix_module, 'fix_all_imports'):
                fix_module.fix_all_imports()
                print("   ✅ Import 語句修復完成")
            else:
                print("   ⚠️ 修復腳本中找不到 fix_all_imports 函數")
        else:
            print("   ⚠️ 找不到 fix_imports.py，請手動修復 import 語句")
            
    except Exception as e:
        print(f"   ⚠️ 修復 import 時發生錯誤: {e}")
        print("   請手動檢查 import 語句")

def create_launcher_scripts(base_dir):
    """建立啟動腳本"""
    # Windows 批次檔
    batch_content = """@echo off
echo Starting Artale Script GUI...
python run_gui.py
pause
"""
    
    batch_path = base_dir / "start_gui.bat"
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_content)
    print("✅ 已建立 Windows 啟動腳本: start_gui.bat")
    
    # Shell 腳本 (Linux/Mac)
    shell_content = """#!/bin/bash
echo "Starting Artale Script GUI..."
python3 run_gui.py
"""
    
    shell_path = base_dir / "start_gui.sh"
    with open(shell_path, 'w', encoding='utf-8') as f:
        f.write(shell_content)
    
    # 設定執行權限
    try:
        os.chmod(shell_path, 0o755)
        print("✅ 已建立 Linux/Mac 啟動腳本: start_gui.sh")
    except OSError:
        print("⚠️ 無法設定 Shell 腳本執行權限")

def verify_setup(base_dir):
    """驗證專案設定"""
    checks = []
    
    # 檢查關鍵檔案
    critical_files = [
        "config.py",
        "main.py", 
        "run_gui.py",
        ".env",
        "requirements.txt"
    ]
    
    for file_name in critical_files:
        file_path = base_dir / file_name
        if file_path.exists():
            checks.append(f"✅ {file_name}")
        else:
            checks.append(f"❌ {file_name}")
    
    # 檢查核心模組
    core_modules = [
        "core/config.py",
        "core/utils.py",
        "core/monster_detector.py"
    ]
    
    for module in core_modules:
        module_path = base_dir / module
        if module_path.exists():
            checks.append(f"✅ {module}")
        else:
            checks.append(f"❌ {module}")
    
    # 檢查 GUI 模組
    gui_modules = [
        "gui/__init__.py",
        "gui/main_window.py"
    ]
    
    for module in gui_modules:
        module_path = base_dir / module
        if module_path.exists():
            checks.append(f"✅ {module}")
        else:
            checks.append(f"❌ {module}")
    
    print("   專案檔案檢查:")
    for check in checks:
        print(f"     {check}")
    
    # 統計結果
    success_count = len([c for c in checks if c.startswith("✅")])
    total_count = len(checks)
    
    if success_count == total_count:
        print(f"   🎉 專案檔案檢查通過 ({success_count}/{total_count})")
        return True
    else:
        print(f"   ⚠️ 部分檔案缺失 ({success_count}/{total_count})")
        return False

# 匯入 importlib 用於動態載入模組
import importlib.util

if __name__ == "__main__":
    try:
        success = setup_project()
        if success:
            print("\n🎊 設定完成！您可以開始使用 Artale Script 了！")
        else:
            print("\n❌ 設定過程中發生問題，請檢查上方的錯誤訊息")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 設定被用戶中斷")
    except Exception as e:
        print(f"\n❌ 設定過程發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()