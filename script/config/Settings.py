"""应用设置配置"""
import os
from pathlib import Path


class Settings:
    """应用设置"""
    # 应用基础路径
    APP_NAME = "Elves"
    BASE_DIR = os.path.join(os.getenv("LOCALAPPDATA", ""), APP_NAME)
    # 日志配置
    LOGS_PATH = Path(BASE_DIR) / "logs"
    LOG_FILE = LOGS_PATH / "app.log"
    LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
    LOG_BACKUP_COUNT = 5
    LOG_ENCODING = "utf-8"

    # WebView 配置
    WEBVIEW2_RUNTIME_PATH = "WebView2"

    # 默认URL
    DEFAULT_URL = "https://elves.elarion.cn:5277"

    # 日志格式
    LOG_FORMAT = (
        '%(asctime)s - %(name)s - %(levelname)s - '
        '%(filename)s:%(lineno)d - %(message)s'
    )
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


settings = Settings()