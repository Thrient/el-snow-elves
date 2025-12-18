import argparse
import logging
from multiprocessing import freeze_support

import webview

from script.config.Settings import settings
from script.config.logs import setup_logging
from script.core.Elves import Elves

webview.settings['WEBVIEW2_RUNTIME_PATH'] = "WebView2"

if __name__ == '__main__':
    freeze_support()
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default=settings.DEFAULT_URL)
    parser.add_argument('--debug', type=bool, default=False)
    parser.add_argument(
        '--no-file-log',
        action='store_true',
        default=False,
        help="禁用文件日志，仅输出到控制台"
    )

    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="设置日志级别"
    )

    setup_logging(
        log_level=getattr(logging, parser.parse_args().log_level),
        enable_file_logging=not parser.parse_args().no_file_log
    )

    Elves = Elves(url=parser.parse_args().url)
    Elves.run(debug=parser.parse_args().debug)
