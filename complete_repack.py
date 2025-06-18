# complete_repack.py
# 完整重新打包腳本 - 包含所有必要文件

import os
import shutil
import subprocess
import sys

def create_missing_files():
    """創建可能缺少的文件"""
    print("📝 創建必要的配置文件...")
    
    # 創建 .env 文件
    env_content = """# ArtaleScript 配置文件
WORKING_DIR=
ASSETS_DIR=
SCREENSHOTS_DIR=
WINDOW_NAME=MapleStory Worlds-Artale (繁體中文版)
Y_OFFSET=50
MATCH_THRESHOLD=0.6
DETECTION_INTERVAL=0.01
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ 已創建 .env")
    else:
        print("✅ .env 已存在")
    
    # 創建 scripts 目錄和 setup_project.py
    if not os.path.exists('scripts'):
        os.makedirs('scripts')
        print("✅ 已創建 scripts 目錄")
    
    setup_content = '''#!/usr/bin/env python3
"""項目設置腳本"""
import os

def setup_project():
    """設置項目環境"""
    print("🔧 設置 ArtaleScript 項目...")
    
    env_content = """# ArtaleScript 配置文件
WORKING_DIR=
ASSETS_DIR=
SCREENSHOTS_DIR=
WINDOW_NAME=MapleStory Worlds-Artale (繁體中文版)
Y_OFFSET=50
MATCH_THRESHOLD=0.6
DETECTION_INTERVAL=0.01
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env 文件已創建")
    print("🎉 項目設置完成！")

if __name__ == "__main__":
    setup_project()
'''
    
    setup_path = os.path.join('scripts', 'setup_project.py')
    if not os.path.exists(setup_path):
        with open(setup_path, 'w', encoding='utf-8') as f:
            f.write(setup_content)
        print("✅ 已創建 scripts/setup_project.py")
    else:
        print("✅ setup_project.py 已存在")

def clean_build():
    """清理構建文件"""
    print("🧹 清理舊的構建文件...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   已刪除 {dir_name}/")
    
    # 清理 .spec 文件
    import glob
    for spec_file in glob.glob('*.spec'):
        os.remove(spec_file)
        print(f"   已刪除 {spec_file}")

def build_complete_version():
    """構建包含所有文件的完整版本"""
    print("🔨 構建完整版本...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',  # 不顯示控制台
        '--name=ArtaleScript_Complete',
        '--clean',
        '--noconfirm',
        
        # 排除問題模組
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        
        # 添加必要的隱藏導入
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=pyautogui',
        '--hidden-import=customtkinter',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=tkinter.filedialog',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageTk',
        '--hidden-import=requests',
        '--hidden-import=win32gui',
        '--hidden-import=keyboard',
        '--hidden-import=threading',
        '--hidden-import=queue',
        '--hidden-import=hashlib',
        '--hidden-import=uuid',
        '--hidden-import=json',
        '--hidden-import=time',
        '--hidden-import=random',
        '--hidden-import=pathlib',
        '--hidden-import=dotenv',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=glob',
        '--hidden-import=datetime',
        '--hidden-import=platform',
        '--hidden-import=subprocess',
        '--hidden-import=tempfile',
        '--hidden-import=zipfile',
        
        # 添加 Firebase 相關（如果有）
        '--hidden-import=firebase_admin',
        '--hidden-import=google.cloud.firestore',
        
        # 添加所有必要文件
        '--add-data=core;core',
        '--add-data=config.py;.',
        '--add-data=.env;.',  # 重要：包含 .env 文件
        '--add-data=scripts;scripts',  # 包含 scripts 目錄
    ]
    
    # 添加資源目錄
    resource_dirs = ['assets', 'ArtaleScriptFiles']
    for dir_name in resource_dirs:
        if os.path.exists(dir_name):
            cmd.append(f'--add-data={dir_name};{dir_name}')
            print(f"   添加 {dir_name}/")
    
    # 主文件
    cmd.append('run_gui.py')
    
    print("開始打包完整版本...")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ 完整版本打包成功！")
            return True
        else:
            print("❌ 打包失敗:")
            print(result.stderr[-1000:])
            return False
            
    except Exception as e:
        print(f"❌ 打包過程出錯: {e}")
        return False

def build_debug_version():
    """同時構建調試版本"""
    print("🔧 構建調試版本...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--console',  # 顯示控制台
        '--name=ArtaleScript_Debug',
        '--clean',
        '--noconfirm',
        
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        
        '--hidden-import=cv2',
        '--hidden-import=numpy',
        '--hidden-import=pyautogui',
        '--hidden-import=customtkinter',
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
        '--hidden-import=requests',
        '--hidden-import=win32gui',
        '--hidden-import=keyboard',
        '--hidden-import=dotenv',
        
        '--add-data=core;core',
        '--add-data=config.py;.',
        '--add-data=.env;.',  # 重要：包含 .env 文件
        '--add-data=scripts;scripts',
    ]
    
    # 添加資源目錄
    if os.path.exists('assets'):
        cmd.append('--add-data=assets;assets')
    
    cmd.append('run_gui.py')
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        return result.returncode == 0
    except:
        return False

def create_release_package():
    """創建最終發布包"""
    print("📦 創建發布包...")
    
    release_dir = 'ArtaleScript_Final_Release'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    
    os.makedirs(release_dir)
    
    # 複製主程式
    if os.path.exists('dist/ArtaleScript_Complete.exe'):
        shutil.copy2('dist/ArtaleScript_Complete.exe', release_dir)
        shutil.rename(
            os.path.join(release_dir, 'ArtaleScript_Complete.exe'),
            os.path.join(release_dir, 'ArtaleScript.exe')
        )
        print("✅ 已複製主程式")
    
    # 複製調試版本
    if os.path.exists('dist/ArtaleScript_Debug.exe'):
        shutil.copy2('dist/ArtaleScript_Debug.exe', release_dir)
        print("✅ 已複製調試版本")
    
    # 創建 .env 範例
    env_example_content = """# ArtaleScript 配置文件
# 如果程式無法啟動，請檢查這些設定

# 工作目錄（通常留空）
WORKING_DIR=

# 資源目錄（通常留空使用預設）
ASSETS_DIR=

# 截圖保存目錄
SCREENSHOTS_DIR=

# 遊戲視窗名稱（請根據你的遊戲版本調整）
WINDOW_NAME=MapleStory Worlds-Artale (繁體中文版)

# 檢測參數（進階用戶可調整）
Y_OFFSET=50
MATCH_THRESHOLD=0.6
DETECTION_INTERVAL=0.01
"""
    
    with open(os.path.join(release_dir, '.env.example'), 'w', encoding='utf-8') as f:
        f.write(env_example_content)
    
    # 創建使用說明
    readme_content = """# ArtaleScript 使用說明

## 🚀 快速開始
1. 雙擊 ArtaleScript.exe 啟動程式
2. 在 GUI 中輸入有效的 UUID 進行認證
3. 認證成功後即可使用所有功能

## 🔧 故障排除
如果程式無法啟動：
1. 先嘗試執行 ArtaleScript_Debug.exe 查看錯誤信息
2. 確認 .env 文件存在且配置正確
3. 檢查是否有防毒軟體阻擋
4. 嘗試以管理員身分執行

## ⚙️ 系統要求
- Windows 10/11
- 管理員權限（用於遊戲操作）
- 穩定的網路連接（認證需要）
- Visual C++ Redistributable（如果缺少會自動提示安裝）

## 📁 文件說明
- ArtaleScript.exe - 主程式（GUI 模式）
- ArtaleScript_Debug.exe - 調試版本（控制台模式）
- .env.example - 配置文件範例

## 🔒 安全特性
- Firebase 認證保護
- 會話令牌驗證
- 定期認證檢查
- 未授權自動退出

需要有效的 UUID 才能使用。如有問題請聯繫開發者。
"""
    
    with open(os.path.join(release_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 發布包已創建: {release_dir}/")
    
    # 顯示包內容和大小
    print("\n📋 發布包內容:")
    for root, dirs, files in os.walk(release_dir):
        for file in files:
            file_path = os.path.join(root, file)
            size = os.path.getsize(file_path)
            rel_path = os.path.relpath(file_path, release_dir)
            if size > 1024*1024:
                size_str = f"{size // (1024*1024)} MB"
            else:
                size_str = f"{size // 1024} KB"
            print(f"   📄 {rel_path} ({size_str})")
    
    return release_dir

def main():
    """主流程"""
    print("🚀 ArtaleScript 完整重新打包工具")
    print("=" * 60)
    
    # 1. 創建必要文件
    create_missing_files()
    
    # 2. 清理舊文件
    clean_build()
    
    # 3. 構建完整版本
    print(f"\n🔨 開始構建...")
    complete_success = build_complete_version()
    
    # 4. 構建調試版本
    debug_success = build_debug_version()
    
    if complete_success:
        print("✅ 完整版本構建成功")
    else:
        print("❌ 完整版本構建失敗")
    
    if debug_success:
        print("✅ 調試版本構建成功")
    else:
        print("❌ 調試版本構建失敗")
    
    # 5. 創建發布包
    if complete_success or debug_success:
        release_dir = create_release_package()
        
        print("\n" + "=" * 60)
        print("🎉 重新打包完成！")
        print(f"📁 發布包位置: {release_dir}")
        print("\n💡 測試順序:")
        print("1. 先測試 ArtaleScript.exe（主程式）")
        print("2. 如果有問題，測試 ArtaleScript_Debug.exe（查看錯誤）")
        print("3. 現在應該包含所有必要文件，不會再出現 .env 錯誤")
        print("\n🔒 用戶使用:")
        print("- 雙擊 ArtaleScript.exe 即可使用")
        print("- 需要有效的 UUID 進行認證")
        print("- 所有源碼都已隱藏在 exe 中")
        
    else:
        print("❌ 所有構建都失敗了")
        print("請檢查上面的錯誤信息")
    
    input("\n按 Enter 退出...")

if __name__ == "__main__":
    main()