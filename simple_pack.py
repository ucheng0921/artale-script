# simple_pack.py
# 簡化版打包腳本 - 只打包 GUI 版本

import os
import shutil
import subprocess
import sys

def clean_build():
    """清理舊的構建文件"""
    print("🧹 清理舊文件...")
    
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

def ensure_env_file():
    """確保 .env 文件存在"""
    if not os.path.exists('.env'):
        print("📝 創建 .env 文件...")
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
        print("✅ 已創建 .env")
    else:
        print("✅ .env 已存在")

def build_gui_version():
    """構建 GUI 版本"""
    print("🔨 開始打包 GUI 版本...")
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',  # 無控制台窗口
        '--name=ArtaleScript',
        '--clean',
        '--noconfirm',
        
        # 排除問題模組
        '--exclude-module=PyQt5',
        '--exclude-module=PyQt6',
        '--exclude-module=matplotlib',
        '--exclude-module=scipy',
        '--exclude-module=pandas',
        
        # 必要的隱藏導入
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
        '--hidden-import=firebase_admin',
        '--hidden-import=google.cloud.firestore',
        
        # 添加文件
        '--add-data=core;core',
        '--add-data=config.py;.',
        '--add-data=.env;.',
    ]
    
    # 添加 assets 目錄（如果存在）
    if os.path.exists('assets'):
        cmd.append('--add-data=assets;assets')
        print("   添加 assets/")
    
    # 主文件
    cmd.append('run_gui.py')
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ GUI 版本打包成功！")
            return True
        else:
            print("❌ 打包失敗:")
            print(result.stderr[-1000:])
            return False
            
    except Exception as e:
        print(f"❌ 打包過程出錯: {e}")
        return False

def create_release():
    """創建發布包"""
    print("📦 創建發布包...")
    
    release_dir = 'ArtaleScript_Release'
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    
    os.makedirs(release_dir)
    
    # 複製主程式
    if os.path.exists('dist/ArtaleScript.exe'):
        shutil.copy2('dist/ArtaleScript.exe', release_dir)
        print("✅ 已複製 ArtaleScript.exe")
    else:
        print("❌ 找不到 ArtaleScript.exe")
        return None
    
    # 創建使用說明
    readme_content = """# ArtaleScript

## 🚀 使用方法
1. 雙擊 ArtaleScript.exe 啟動
2. 輸入有效的 UUID 進行認證
3. 認證成功後即可使用

## ⚙️ 系統要求
- Windows 10/11
- 管理員權限
- 網路連接

## 🔒 安全
需要有效的 UUID 才能使用所有功能。

如有問題請聯繫開發者。
"""
    
    with open(os.path.join(release_dir, 'README.txt'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    # 顯示文件大小
    exe_path = os.path.join(release_dir, 'ArtaleScript.exe')
    size = os.path.getsize(exe_path)
    size_mb = size / (1024 * 1024)
    
    print(f"✅ 發布包已創建: {release_dir}/")
    print(f"📊 ArtaleScript.exe 大小: {size_mb:.1f} MB")
    
    return release_dir

def main():
    """主流程"""
    print("🚀 ArtaleScript 簡化打包工具")
    print("=" * 40)
    
    # 1. 確保 .env 文件存在
    ensure_env_file()
    
    # 2. 清理舊文件
    clean_build()
    
    # 3. 打包 GUI 版本
    if build_gui_version():
        # 4. 創建發布包
        release_dir = create_release()
        
        if release_dir:
            print("\n" + "=" * 40)
            print("🎉 打包完成！")
            print(f"📁 發布包: {release_dir}")
            print("💡 用戶只需雙擊 ArtaleScript.exe 即可使用")
            print("🔒 所有源碼已隱藏，需要 UUID 認證")
        else:
            print("❌ 創建發布包失敗")
    else:
        print("❌ 打包失敗")
    
    input("\n按 Enter 退出...")

if __name__ == "__main__":
    main()