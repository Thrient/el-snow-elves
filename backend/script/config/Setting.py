# 应用配置
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
APP_URL = os.path.join(PROJECT_ROOT, 'dist', 'index.html')
APP_NAME = "Elves"
APP_TITLE = '时雪-创意工坊'
VERSION = '7.6.2'
APP_DATA = os.getenv("LOCALAPPDATA") + f"/{APP_NAME}"
USER_CONFIG_PATH = APP_DATA + r"\Config\User"
STORAGE_PATH = APP_DATA + r"\pywebview"
THRESHOLD = 0.85
BOX = (0, 0, 1335, 750)
DESIGN_WIDTH = 1335
DESIGN_HEIGHT = 750
PREPROCESS_KEYS = {"binarize", "binarize_threshold", "binarize_invert", "adaptive", "adaptive_block", "adaptive_c",
                   "canny", "canny_low", "canny_high", "dilate", "erode", "morph_size", "clahe", "clahe_clip"}
OVERTIME = 1800
DELAY = 1500
SYS_CONFIG_PATH = APP_DATA + r"\Config\sys"
