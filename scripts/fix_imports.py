"""
修復 import 語句的腳本
"""
import os
import re
from pathlib import Path

# import 對應表
IMPORT_MAPPING = {
    'from auth_manager import': 'from core.auth_manager import',
    'from monster_detector import': 'from core.monster_detector import',
    'from movement import': 'from core.movement import',
    'from enhanced_movement import': 'from core.enhanced_movement import',
    'from image_processor import': 'from core.image_processor import',
    'from cliff_detection import': 'from core.cliff_detection import',
    'from rope_climbing import': 'from core.rope_climbing import',
    'from rune_mode import': 'from core.rune_mode import',
    'from search import': 'from core.search import',
    'from red_dot_detector import': 'from core.red_dot_detector import',
    'from passive_skills_manager import': 'from core.passive_skills_manager import',
    'from random_down_jump import': 'from core.random_down_jump import',
    'from config_protection import': 'from core.config_protection import',
    'from utils import': 'from core.utils import',
    'import auth_manager': 'import core.auth_manager',
    'import monster_detector': 'import core.monster_detector',
    'import movement': 'import core.movement',
    'import enhanced_movement': 'import core.enhanced_movement',
    'import image_processor': 'import core.image_processor',
    'import cliff_detection': 'import core.cliff_detection',
    'import rope_climbing': 'import core.rope_climbing',
    'import rune_mode': 'import core.rune_mode',
    'import search': 'import core.search',
    'import red_dot_detector': 'import core.red_dot_detector',
    'import passive_skills_manager': 'import core.passive_skills_manager',
    'import random_down_jump': 'import core.random_down_jump',
    'import config_protection': 'import core.config_protection',
    'import utils': 'import core.utils',
}

def fix_imports_in_file(file_path):
    """修復單個檔案的 import"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 修復 import 語句
        for old_import, new_import in IMPORT_MAPPING.items():
            content = content.replace(old_import, new_import)
        
        # 如果有變更，寫回檔案
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已修復: {file_path}")
            return True
        else:
            print(f"⏭️  無需修復: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ 修復失敗 {file_path}: {e}")
        return False

def fix_all_imports():
    """修復所有 Python 檔案的 import"""
    base_dir = Path(__file__).parent.parent
    
    # 需要修復的檔案路徑
    python_files = []
    
    # 收集所有 .py 檔案
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.py') and file != 'fix_imports.py':
                python_files.append(os.path.join(root, file))
    
    print(f"找到 {len(python_files)} 個 Python 檔案")
    
    fixed_count = 0
    for file_path in python_files:
        if fix_imports_in_file(file_path):
            fixed_count += 1
    
    print(f"\n✅ 修復完成！共修復 {fixed_count} 個檔案")

if __name__ == "__main__":
    fix_all_imports()