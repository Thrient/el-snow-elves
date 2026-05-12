import argparse
import mimetypes
import webview
from script.config.Setting import APP_URL, PROJECT_ROOT
from script.core.App import App
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-5s] %(message)s')

mimetypes.add_type("application/javascript", ".js")
webview.settings['WEBVIEW2_RUNTIME_PATH'] = "WebView2"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default=APP_URL)
    parser.add_argument('--debug', type=bool, default=False)

    app = App(url=parser.parse_args().url)
    app.run(debug=parser.parse_args().debug)

