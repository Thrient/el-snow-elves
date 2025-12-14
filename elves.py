import argparse
import io
import logging
import sys
from logging.handlers import RotatingFileHandler
from multiprocessing import freeze_support
from pathlib import Path

import webview

from script.config.Config import Config
from script.core.Elves import Elves

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

Path(Config.LOGS_PATH).mkdir(parents=True, exist_ok=True)

file_handler = RotatingFileHandler(
    f'{Config.LOGS_PATH}/app.log',  # 日志文件名
    maxBytes=1024 * 1024 * 5,  # 5MB
    backupCount=5,  # 保留5个备份文件
    encoding='utf-8'  # 避免中文乱码
)

file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

webview.settings['WEBVIEW2_RUNTIME_PATH'] = "WebView2"

if __name__ == '__main__':
    freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default="https://nas.elarion.cn:5277")
    parser.add_argument('--debug', type=bool, default=False)

    Elves = Elves(url=parser.parse_args().url)
    Elves.run(debug=parser.parse_args().debug)
