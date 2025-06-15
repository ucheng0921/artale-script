"""
自動更新系統
"""
import json
import os
import requests
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

class AutoUpdater:
    def __init__(self, github_repo: str = "ucheng0921/artale-script"):
        self.github_repo = github_repo
        self.api_base = f"https://api.github.com/repos/{github_repo}"
        self.base_dir = Path(__file__).parent.parent
        self.version_file = self.base_dir / "version.json"
        
    def get_current_version(self) -> Dict:
        """獲取當前版本資訊"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"version": "1.0.0"}
    
    def check_for_updates(self) -> Tuple[bool, Optional[Dict]]:
        """檢查是否有更新"""
        try:
            # 獲取最新 release
            response = requests.get(f"{self.api_base}/releases/latest", timeout=10)
            if response.status_code != 200:
                return False, None
            
            latest_release = response.json()
            latest_version = latest_release["tag_name"].lstrip("v")
            current_version = self.get_current_version()["version"]
            
            # 比較版本號
            if self._compare_versions(latest_version, current_version) > 0:
                return True, {
                    "version": latest_version,
                    "download_url": latest_release["zipball_url"],
                    "release_notes": latest_release["body"],
                    "published_at": latest_release["published_at"]
                }
            
            return False, None
            
        except Exception as e:
            print(f"檢查更新失敗: {e}")
            return False, None
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比較版本號"""
        def normalize(v):
            return [int(x) for x in v.split(".")]
        
        norm_v1 = normalize(v1)
        norm_v2 = normalize(v2)
        
        # 補齊長度
        max_len = max(len(norm_v1), len(norm_v2))
        norm_v1.extend([0] * (max_len - len(norm_v1)))
        norm_v2.extend([0] * (max_len - len(norm_v2)))
        
        if norm_v1 > norm_v2:
            return 1
        elif norm_v1 < norm_v2:
            return -1
        else:
            return 0
    
    def download_update(self, download_url: str) -> Optional[Path]:
        """下載更新檔案"""
        try:
            print("📥 正在下載更新...")
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 建立暫存檔案
            temp_file = Path(tempfile.gettempdir()) / "artale_update.zip"
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("✅ 下載完成")
            return temp_file
            
        except Exception as e:
            print(f"下載失敗: {e}")
            return None
    
    def apply_update(self, update_file: Path) -> bool:
        """套用更新"""
        try:
            print("🔄 正在套用更新...")
            
            # 建立備份
            backup_dir = self.base_dir.parent / f"backup_{self.get_current_version()['version']}"
            backup_dir.mkdir(exist_ok=True)
            
            # 備份重要檔案
            important_files = [".env", "config.py"]
            for file_name in important_files:
                file_path = self.base_dir / file_name
                if file_path.exists():
                    import shutil
                    shutil.copy2(file_path, backup_dir / file_name)
            
            # 解壓更新檔案
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                # 取得解壓後的資料夾名稱
                extract_dir = Path(tempfile.gettempdir()) / "artale_update_extracted"
                if extract_dir.exists():
                    import shutil
                    shutil.rmtree(extract_dir)
                
                zip_ref.extractall(extract_dir)
                
                # 找到實際的程式碼資料夾
                code_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                if not code_dirs:
                    raise Exception("無法找到程式碼資料夾")
                
                source_dir = code_dirs[0]
                
                # 複製檔案 (排除某些檔案)
                exclude_files = {".env", "assets", "ArtaleScriptFiles"}
                
                import shutil
                for item in source_dir.iterdir():
                    if item.name not in exclude_files:
                        dest_path = self.base_dir / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                shutil.rmtree(dest_path)
                            shutil.copytree(item, dest_path)
                        else:
                            shutil.copy2(item, dest_path)
            
            # 恢復重要檔案
            for file_name in important_files:
                backup_file = backup_dir / file_name
                if backup_file.exists():
                    import shutil
                    shutil.copy2(backup_file, self.base_dir / file_name)
            
            print("✅ 更新套用完成")
            return True
            
        except Exception as e:
            print(f"套用更新失敗: {e}")
            return False
    
    def auto_update(self) -> bool:
        """執行自動更新流程"""
        print("🔍 檢查更新...")
        
        has_update, update_info = self.check_for_updates()
        
        if not has_update:
            print("✅ 已是最新版本")
            return True
        
        print(f"🆕 發現新版本: {update_info['version']}")
        print(f"發布說明: {update_info['release_notes']}")
        
        # 下載更新
        update_file = self.download_update(update_info['download_url'])
        if not update_file:
            return False
        
        # 套用更新
        success = self.apply_update(update_file)
        
        # 清理暫存檔案
        try:
            update_file.unlink()
        except:
            pass
        
        if success:
            print("🎉 更新完成！請重新啟動程式")
        
        return success