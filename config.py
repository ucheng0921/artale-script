"""
配置模組 - 修復版，解決 PyInstaller 路徑問題
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def get_application_path():
    """獲取應用程式的實際路徑（修復 PyInstaller 路徑問題）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包環境 - 返回 exe 所在目錄
        return Path(sys.executable).parent
    else:
        # 開發環境
        return Path(__file__).parent

def get_resource_path(relative_path):
    """獲取資源文件路徑（PyInstaller 兼容）"""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller 打包環境 - 資源在臨時目錄中
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # 開發環境 - 使用相對路徑
        base_path = Path(__file__).parent
        return os.path.join(base_path, relative_path)

# 基礎路徑配置 - 修復版
APPLICATION_DIR = get_application_path()  # exe 所在目錄
BASE_DIR = APPLICATION_DIR

# 工作目錄設定
WORKING_DIR = os.getenv('WORKING_DIR')
if not WORKING_DIR:
    WORKING_DIR = str(APPLICATION_DIR)

# 資源目錄設定 - 關鍵修復
ASSETS_DIR = os.getenv('ASSETS_DIR')
if not ASSETS_DIR:
    # 優先嘗試 exe 同目錄的 assets
    exe_dir_assets = APPLICATION_DIR / 'assets' / 'game_resources'
    if exe_dir_assets.exists():
        ASSETS_DIR = str(exe_dir_assets)
    else:
        # 使用打包內的資源
        ASSETS_DIR = get_resource_path('assets/game_resources')

# 確保關鍵路徑存在
def ensure_directories():
    """確保必要的目錄存在"""
    asset_path = Path(ASSETS_DIR)
    asset_path.mkdir(parents=True, exist_ok=True)
    
    # 建立子目錄
    required_dirs = [
        'monsters', 'change', 'rope', 'Detection', 'screenshots'
    ]
    
    for dir_name in required_dirs:
        (asset_path / dir_name).mkdir(exist_ok=True)
    
    print(f"✅ 資產目錄已確保存在: {ASSETS_DIR}")

# 基本設定
PYAUTOGUI_FAILSAFE = True
WINDOW_NAME = os.getenv('WINDOW_NAME', "MapleStory Worlds-Artale (繁體中文版)")

# 圖片路徑配置 - 使用相對路徑
MEDAL_PATH = os.path.join(ASSETS_DIR, 'medal.png')
SIGN_PATH = os.path.join(ASSETS_DIR, 'sign_text.png')
RUNE_PATH = os.path.join(ASSETS_DIR, 'rune_text.png')
ROPE_PATH = os.path.join(ASSETS_DIR, 'rope')
RED_DOT_PATH = os.path.join(ASSETS_DIR, 'red.png')

# 換頻道圖片路徑
CHANGE0_PATH = os.path.join(ASSETS_DIR, 'change', 'change0.png')
CHANGE0_1_PATH = os.path.join(ASSETS_DIR, 'change', 'change0_1.png')
CHANGE1_PATH = os.path.join(ASSETS_DIR, 'change', 'change1.png')
CHANGE2_PATH = os.path.join(ASSETS_DIR, 'change', 'change2.png')
CHANGE3_PATH = os.path.join(ASSETS_DIR, 'change', 'change3.png')
CHANGE4_PATH = os.path.join(ASSETS_DIR, 'change', 'change4.png')
CHANGE5_PATH = os.path.join(ASSETS_DIR, 'change', 'change5.png')

# 怪物檢測路徑
MONSTER_BASE_PATH = os.path.join(ASSETS_DIR, 'monsters')

# 截圖儲存路徑
SCREENSHOT_SAVE_PATH = os.getenv('SCREENSHOTS_DIR', os.path.join(ASSETS_DIR, 'screenshots'))

# 檢測參數 - 可透過環境變數調整
Y_OFFSET = int(os.getenv('Y_OFFSET', 50))
MATCH_THRESHOLD = float(os.getenv('MATCH_THRESHOLD', 0.6))
DETECTION_INTERVAL = float(os.getenv('DETECTION_INTERVAL', 0.01))
SIGN_CHECK_FREQUENCY = 3

# =============================================================================
# 遊戲功能配置 (保持原有設定)
# =============================================================================

# 怪物檢測與攻擊配置
ENABLED_MONSTERS = ['monster5']
JUMP_KEY = 'alt'
ATTACK_KEY = 'z'
SECONDARY_ATTACK_KEY = 'v'
ENABLE_SECONDARY_ATTACK = 0
PRIMARY_ATTACK_CHANCE = 0.8
SECONDARY_ATTACK_CHANCE = 0.2
ATTACK_RANGE_X = 200
JUMP_ATTACK_MODE = 'original'

# 被動技能系統配置
ENABLE_PASSIVE_SKILLS = 0
PASSIVE_SKILL_1_KEY = 'r'
PASSIVE_SKILL_2_KEY = 't'
PASSIVE_SKILL_3_KEY = '3'
PASSIVE_SKILL_4_KEY = '4'
PASSIVE_SKILL_1_COOLDOWN = 30.0
PASSIVE_SKILL_2_COOLDOWN = 45.0
PASSIVE_SKILL_3_COOLDOWN = 60.0
PASSIVE_SKILL_4_COOLDOWN = 120.0
ENABLE_PASSIVE_SKILL_1 = True
ENABLE_PASSIVE_SKILL_2 = True
ENABLE_PASSIVE_SKILL_3 = False
ENABLE_PASSIVE_SKILL_4 = False
PASSIVE_SKILL_RANDOM_DELAY_MIN = 1
PASSIVE_SKILL_RANDOM_DELAY_MAX = 2

# 隨機下跳功能配置
ENABLE_RANDOM_DOWN_JUMP = True
RANDOM_DOWN_JUMP_MIN_INTERVAL = 50
RANDOM_DOWN_JUMP_MAX_INTERVAL = 100
DOWN_JUMP_HOLD_TIME = 0.1
DOWN_JUMP_CHANCE = 1
DOWN_JUMP_ONLY_WHEN_MOVING = True
DOWN_JUMP_AVOID_DURING_ATTACK = True
DOWN_JUMP_AVOID_DURING_CLIMBING = True
DOWN_JUMP_WITH_DIRECTION = True
DOWN_JUMP_RANDOM_DIRECTION = False

# 增強移動系統配置
ENABLE_ENHANCED_MOVEMENT = True
ENABLE_JUMP_MOVEMENT = False
JUMP_MOVEMENT_CHANCE = 0.05
ENABLE_DASH_MOVEMENT = True
DASH_MOVEMENT_CHANCE = 0.7
DASH_SKILL_KEY = 'x'
DASH_SKILL_COOLDOWN = 3.0
MOVEMENT_PRIORITY = ['jump', 'dash', 'normal']
ROPE_COOLDOWN_TIME = 60.0

# 紅點偵測與換頻道配置
ENABLE_RED_DOT_DETECTION = True
RED_DOT_MIN_TIME = 1.0
RED_DOT_MAX_TIME = 2.0
RED_DOT_DETECTION_THRESHOLD = 0.9
RED_DOT_RESET_THRESHOLD = 3

# 檢測參數配置
Y_LAYER_THRESHOLD = 300
RUNE_HEIGHT_THRESHOLD = 200
SMALL_MONSTER_Y_TOLERANCE = 30
MEDIUM_MONSTER_Y_TOLERANCE = 45
LARGE_MONSTER_Y_TOLERANCE = 70
MIN_DETECTION_SIZE = 200
MAX_DETECTION_SIZE = 1000

# 在模組載入時確保目錄存在
ensure_directories()

# 調試信息
print(f"🔧 [配置調試] 路徑信息:")
print(f"   APPLICATION_DIR: {APPLICATION_DIR}")
print(f"   ASSETS_DIR: {ASSETS_DIR}")
print(f"   是否為打包環境: {hasattr(sys, '_MEIPASS')}")
if hasattr(sys, '_MEIPASS'):
    print(f"   PyInstaller 臨時目錄: {sys._MEIPASS}")

# 驗證關鍵文件
key_files = ['medal.png', 'sign_text.png', 'rune_text.png', 'red.png']
print(f"🔍 [配置調試] 關鍵文件檢查:")
for filename in key_files:
    filepath = os.path.join(ASSETS_DIR, filename)
    exists = os.path.exists(filepath)
    print(f"   {'✅' if exists else '❌'} {filename}: {filepath}")