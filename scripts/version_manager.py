"""
版本管理工具
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class VersionManager:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.version_file = self.base_dir / "version.json"
        self.version_py = self.base_dir / "__version__.py"
    
    def get_current_version(self):
        """獲取當前版本"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"version": "1.0.0", "build": "20241201001"}
    
    def update_version(self, version_type="patch"):
        """更新版本號
        
        Args:
            version_type: "major", "minor", "patch"
        """
        current = self.get_current_version()
        version_parts = current["version"].split(".")
        
        major, minor, patch = map(int, version_parts)
        
        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif version_type == "minor":
            minor += 1
            patch = 0
        elif version_type == "patch":
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        new_build = datetime.now().strftime("%Y%m%d%H%M")
        
        # 更新版本資訊
        version_data = {
            "version": new_version,
            "build": new_build,
            "release_date": datetime.now().strftime("%Y-%m-%d"),
            "changelog": [],
            "min_python_version": "3.8",
            "required_files": [
                "config.py", "main.py", "run_gui.py", "requirements.txt"
            ]
        }
        
        # 保存到 version.json
        with open(self.version_file, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
        
        # 更新 __version__.py
        version_py_content = f'''"""
版本資訊
"""
__version__ = "{new_version}"
__build__ = "{new_build}"
__author__ = "Artale Script Team"
__description__ = "Artale 遊戲自動化腳本"
'''
        
        with open(self.version_py, 'w', encoding='utf-8') as f:
            f.write(version_py_content)
        
        print(f"✅ 版本已更新: {current['version']} -> {new_version}")
        print(f"📅 建置號: {new_build}")
        
        return new_version, new_build
    
    def commit_and_tag(self, version, message=""):
        """提交並建立標籤"""
        try:
            # Git 提交
            subprocess.run(["git", "add", "."], check=True)
            commit_message = f"Release v{version}"
            if message:
                commit_message += f": {message}"
            
            subprocess.run(["git", "commit", "-m", commit_message], check=True)
            
            # 建立標籤
            subprocess.run(["git", "tag", f"v{version}"], check=True)
            
            print(f"✅ Git 提交完成: v{version}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 操作失敗: {e}")
            return False
    
    def push_to_github(self):
        """推送到 GitHub"""
        try:
            subprocess.run(["git", "push"], check=True)
            subprocess.run(["git", "push", "--tags"], check=True)
            print("✅ 已推送到 GitHub")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 推送失敗: {e}")
            return False

def main():
    vm = VersionManager()
    
    if len(sys.argv) < 2:
        print("使用方法: python version_manager.py <major|minor|patch> [commit_message]")
        return
    
    version_type = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else ""
    
    # 更新版本
    new_version, build = vm.update_version(version_type)
    
    # 提交並推送
    if vm.commit_and_tag(new_version, message):
        push = input("是否推送到 GitHub? (y/N): ")
        if push.lower() == 'y':
            vm.push_to_github()

if __name__ == "__main__":
    main()