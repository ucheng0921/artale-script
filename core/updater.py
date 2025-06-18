"""
自動更新系統 - 帶完整調試功能
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
        
        # 添加調試信息
        print(f"🔧 更新器初始化:")
        print(f"   倉庫: {self.github_repo}")
        print(f"   API 基礎URL: {self.api_base}")
        
    def get_current_version(self) -> Dict:
        """獲取當前版本資訊"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"version": "1.0.0"}
    
    def check_for_updates(self) -> Tuple[bool, Optional[Dict]]:
        """檢查是否有更新 - 支援 Tags 備用方案"""
        try:
            print(f"🔍 正在檢查更新...")
            print(f"   倉庫: {self.github_repo}")
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Artale-Script-Updater/1.0'
            }
            
            # 首先嘗試 releases/latest
            latest_url = f"{self.api_base}/releases/latest"
            print(f"   嘗試 releases API: {latest_url}")
            
            response = requests.get(latest_url, headers=headers, timeout=10)
            print(f"   Releases API 狀態: {response.status_code}")
            
            if response.status_code == 404:
                print("   ⚠️ 沒有 releases，嘗試使用 tags...")
                
                # 備用方案：使用 tags
                tags_url = f"{self.api_base}/tags"
                print(f"   嘗試 tags API: {tags_url}")
                
                tags_response = requests.get(tags_url, headers=headers, timeout=10)
                print(f"   Tags API 狀態: {tags_response.status_code}")
                
                if tags_response.status_code == 200:
                    tags_data = tags_response.json()
                    
                    if not tags_data:
                        print("   ❌ 沒有找到任何 tags")
                        return False, None
                    
                    # 取得最新的 tag
                    latest_tag = tags_data[0]
                    print(f"   ✅ 找到最新 tag: {latest_tag['name']}")
                    
                    # 構建類似 release 的數據結構
                    latest_release = {
                        "tag_name": latest_tag['name'],
                        "zipball_url": f"https://github.com/{self.github_repo}/archive/{latest_tag['name']}.zip",
                        "body": f"Release {latest_tag['name']}",
                        "published_at": "unknown"
                    }
                else:
                    print(f"   ❌ Tags API 也失敗: {tags_response.status_code}")
                    return False, None
                    
            elif response.status_code != 200:
                print(f"   ❌ API 請求失敗: {response.status_code}")
                return False, None
            else:
                latest_release = response.json()
                print(f"   ✅ 找到 release: {latest_release['tag_name']}")
            
            # 處理版本比較（其餘邏輯保持不變）
            latest_version_raw = latest_release["tag_name"]
            latest_version = latest_version_raw.lstrip("v")
            current_version = self.get_current_version()["version"]
            
            print(f"📊 版本比較:")
            print(f"   GitHub 版本: {latest_version}")
            print(f"   本地版本: {current_version}")
            
            comparison = self._compare_versions(latest_version, current_version)
            
            if comparison > 0:
                print("✨ 發現新版本!")
                return True, {
                    "version": latest_version,
                    "download_url": latest_release["zipball_url"],
                    "release_notes": latest_release["body"],
                    "published_at": latest_release["published_at"]
                }
            else:
                print("✅ 已是最新版本")
                return False, None
                
        except Exception as e:
            print(f"❌ 檢查更新失敗: {e}")
            return False, None
    
    def check_github_status(self):
        """檢查GitHub倉庫狀態的獨立方法"""
        print(f"🔍 檢查GitHub倉庫狀態: {self.github_repo}")
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Artale-Script-Updater/1.0'
        }
        
        # 1. 檢查倉庫
        try:
            repo_url = f"{self.api_base}"
            print(f"1. 檢查倉庫: {repo_url}")
            repo_response = requests.get(repo_url, headers=headers, timeout=10)
            print(f"   狀態碼: {repo_response.status_code}")
            
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                print(f"   ✅ 倉庫存在")
                print(f"   名稱: {repo_data['full_name']}")
                print(f"   私有: {repo_data['private']}")
                print(f"   描述: {repo_data['description'] or '無描述'}")
            else:
                print(f"   ❌ 倉庫不可訪問: {repo_response.status_code}")
                return
        except Exception as e:
            print(f"   ❌ 倉庫檢查失敗: {e}")
            return
        
        # 2. 檢查releases
        try:
            releases_url = f"{self.api_base}/releases"
            print(f"2. 檢查releases: {releases_url}")
            releases_response = requests.get(releases_url, headers=headers, timeout=10)
            print(f"   狀態碼: {releases_response.status_code}")
            
            if releases_response.status_code == 200:
                releases_data = releases_response.json()
                print(f"   ✅ 找到 {len(releases_data)} 個releases")
                
                for i, release in enumerate(releases_data[:3]):
                    print(f"   Release {i+1}: {release['tag_name']} ({release['published_at'][:10]})")
            else:
                print(f"   ❌ Releases檢查失敗: {releases_response.status_code}")
        except Exception as e:
            print(f"   ❌ Releases檢查失敗: {e}")
        
        # 3. 檢查tags (作為備選)
        try:
            tags_url = f"{self.api_base}/tags"
            print(f"3. 檢查tags: {tags_url}")
            tags_response = requests.get(tags_url, headers=headers, timeout=10)
            print(f"   狀態碼: {tags_response.status_code}")
            
            if tags_response.status_code == 200:
                tags_data = tags_response.json()
                print(f"   ✅ 找到 {len(tags_data)} 個tags")
                
                for i, tag in enumerate(tags_data[:3]):
                    print(f"   Tag {i+1}: {tag['name']}")
            else:
                print(f"   ❌ Tags檢查失敗: {tags_response.status_code}")
        except Exception as e:
            print(f"   ❌ Tags檢查失敗: {e}")
    
    def _compare_versions(self, v1: str, v2: str) -> int:
        """比較版本號"""
        def normalize(v):
            """標準化版本號"""
            v = str(v).strip().lstrip('v')
            
            try:
                parts = []
                for part in v.split("."):
                    import re
                    number_part = re.match(r'(\d+)', part)
                    if number_part:
                        parts.append(int(number_part.group(1)))
                    else:
                        parts.append(0)
                return parts
            except Exception as e:
                print(f"⚠️ 版本號解析失敗: {v} - {e}")
                return [0, 0, 0]
        
        try:
            norm_v1 = normalize(v1)
            norm_v2 = normalize(v2)
            
            print(f"   標準化版本: {v1} -> {norm_v1}")
            print(f"   標準化版本: {v2} -> {norm_v2}")
            
            max_len = max(len(norm_v1), len(norm_v2))
            norm_v1.extend([0] * (max_len - len(norm_v1)))
            norm_v2.extend([0] * (max_len - len(norm_v2)))
            
            for i in range(max_len):
                if norm_v1[i] > norm_v2[i]:
                    print(f"   結果: {v1} > {v2}")
                    return 1
                elif norm_v1[i] < norm_v2[i]:
                    print(f"   結果: {v1} < {v2}")
                    return -1
            
            print(f"   結果: {v1} == {v2}")
            return 0
            
        except Exception as e:
            print(f"❌ 版本比較錯誤: {e}")
            return 0
    
    def download_update(self, download_url: str) -> Optional[Path]:
        """下載更新檔案"""
        try:
            print("📥 正在下載更新...")
            
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            temp_file = Path(tempfile.gettempdir()) / "artale_update.zip"
            
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("✅ 下載完成")
            return temp_file
            
        except Exception as e:
            print(f"❌ 下載失敗: {e}")
            return None
    
    def apply_update(self, update_file: Path) -> bool:
        """套用更新"""
        try:
            print("🔄 正在套用更新...")
            
            backup_dir = self.base_dir.parent / f"backup_{self.get_current_version()['version']}"
            backup_dir.mkdir(exist_ok=True)
            
            important_files = [".env", "config.py"]
            for file_name in important_files:
                file_path = self.base_dir / file_name
                if file_path.exists():
                    import shutil
                    shutil.copy2(file_path, backup_dir / file_name)
            
            with zipfile.ZipFile(update_file, 'r') as zip_ref:
                extract_dir = Path(tempfile.gettempdir()) / "artale_update_extracted"
                if extract_dir.exists():
                    import shutil
                    shutil.rmtree(extract_dir)
                
                zip_ref.extractall(extract_dir)
                
                code_dirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                if not code_dirs:
                    raise Exception("無法找到程式碼資料夾")
                
                source_dir = code_dirs[0]
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
            
            for file_name in important_files:
                backup_file = backup_dir / file_name
                if backup_file.exists():
                    import shutil
                    shutil.copy2(backup_file, self.base_dir / file_name)
            
            print("✅ 更新套用完成")
            return True
            
        except Exception as e:
            print(f"❌ 套用更新失敗: {e}")
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
        
        update_file = self.download_update(update_info['download_url'])
        if not update_file:
            return False
        
        success = self.apply_update(update_file)
        
        try:
            update_file.unlink()
        except:
            pass
        
        if success:
            print("🎉 更新完成！請重新啟動程式")
        
        return success