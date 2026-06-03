import logging
import os
import shutil


def clear_webview_cache_if_version_changed():
    from script.config.Setting import STORAGE_PATH, VERSION

    version_file = os.path.join(STORAGE_PATH, "Config", ".last_version")
    last_version = ""
    try:
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                last_version = f.read().strip()
    except Exception:
        pass

    if last_version != VERSION:
        logging.info(f"[Cache] 版本变更 {last_version!r} → {VERSION!r}，清除 WebView2 缓存")
        cache_dirs = [
            os.path.join(STORAGE_PATH, "EBWebView", "Cache"),
            os.path.join(STORAGE_PATH, "EBWebView", "Code Cache"),
            os.path.join(STORAGE_PATH, "EBWebView", "GPUCache"),
        ]
        for d in cache_dirs:
            try:
                if os.path.exists(d):
                    shutil.rmtree(d)
                    logging.info(f"[Cache] 已清除: {d}")
            except Exception as e:
                logging.warning(f"[Cache] 清除失败 {d}: {e}")

        try:
            os.makedirs(os.path.dirname(version_file), exist_ok=True)
            with open(version_file, "w") as f:
                f.write(VERSION)
        except Exception as e:
            logging.warning(f"[Cache] 写入版本文件失败: {e}")
