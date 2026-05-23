"""更新执行器 — 下载更新 + 替换文件 + 重启"""
import logging
import os
import shutil
import subprocess
import sys

import webview

from script.config.Setting import APP_DATA, STORAGE_PATH
from script.core.UpdateEngine import UpdateEngine, APP_DIR

_log = logging.getLogger("Elves.UpdateWorker")

STAGING_DIR = os.path.join(APP_DATA, "_update_staging")
BAT_PATH = os.path.join(APP_DATA, "_restart.bat")
WEBVIEW_CACHE_DIRS = [
    os.path.join(STORAGE_PATH, "EBWebView", "Cache"),
    os.path.join(STORAGE_PATH, "EBWebView", "Code Cache"),
    os.path.join(STORAGE_PATH, "EBWebView", "GPUCache"),
]


def _push_js(code: str):
    """执行 JS 代码推送进度到前端 store"""
    try:
        w = webview.active_window()
        if w:
            w.evaluate_js(code)
            _log.debug(f"_push_js ok: {code[:80]}")
        else:
            _log.warning("_push_js: no active window")
    except Exception as e:
        _log.error(f"_push_js failed: {e}")


class UpdateWorker:
    @staticmethod
    def download_updates(current_version: str) -> dict:
        """下载更新文件，通过 JS bridge 实时推送进度到前端。返回 {"ok": True} 或 {"error": "..."}。"""
        _log.info(f"download_updates: start current_version={current_version}")
        local = UpdateEngine.compute_manifest()
        _log.info(f"download_updates: manifest has {len(local)} entries")
        diff = UpdateEngine.diff_manifest(current_version, local)

        if "error" in diff:
            _log.error(f"download_updates: diff error: {diff['error']}")
            _push_js("window.useUpdateStore.getState().finishDownload()")
            return {"error": diff["error"]}

        if not diff.get("changed"):
            _log.info("download_updates: no changed files, up to date")
            return {"up_to_date": True}

        changed = diff["changed"]
        total = len(changed)
        _log.info(f"download_updates: {total} files to download")

        # 推送初始化
        _push_js(f"window.useUpdateStore.getState().startDownload({total})")

        # 清空暂存区
        if os.path.exists(STAGING_DIR):
            shutil.rmtree(STAGING_DIR)
        os.makedirs(STAGING_DIR)

        for i, item in enumerate(changed):
            save_path = os.path.join(STAGING_DIR, item["path"])
            _log.info(f"download_updates: [{i+1}/{total}] {item['path']} (id={item['fingerprint_id']}, size={item['size']})")
            try:
                UpdateEngine.download_blob(item["fingerprint_id"], save_path)
                path = item["path"].replace("\\", "\\\\").replace("'", "\\'")
                _push_js(f"window.useUpdateStore.getState().updateProgress('{path}',{i+1})")
            except Exception as e:
                _log.error(f"download_updates: failed {item['path']}: {e}")
                _push_js("window.useUpdateStore.getState().finishDownload()")
                return {"error": f"download {item['path']}: {e}"}

        # 不在这里保存 manifest —— 文件还在暂存区，未应用到 APP_DIR。
        # 重启后 compute_manifest() 会基于实际文件重新计算。

        _push_js("window.useUpdateStore.getState().finishDownload()")
        _log.info(f"download_updates: done, {total} files downloaded")
        return {"ok": True, "file_count": total}

    @staticmethod
    def apply_and_restart():
        """写入重启脚本并退出应用。"""
        pid = os.getpid()
        _log.info(f"apply_and_restart: pid={pid} staging={STAGING_DIR} app_dir={APP_DIR}")

        if getattr(sys, 'frozen', False):
            launch = f'start "" "{sys.executable}"'
        else:
            entry = os.path.join(APP_DIR, "Elves.py")
            launch = f'start "" "{sys.executable}" "{entry}"'

        webview_clear_lines = ""
        for d in WEBVIEW_CACHE_DIRS:
            webview_clear_lines += f'if exist "{d}" rmdir /s /q "{d}"\n'

        # 等待旧进程退出（PID 轮询），而非盲等 2 秒
        script = f'''@echo off
echo [Elves] waiting for PID {pid} to exit...
:waitloop
tasklist /fi "PID eq {pid}" 2>nul | find /i "{pid}" >nul
if not errorlevel 1 (
    timeout /t 1 /nobreak > nul
    goto waitloop
)
echo [Elves] copying files...
xcopy /y /s /e "{STAGING_DIR}\\*" "{APP_DIR}\\"
if errorlevel 1 (
    echo [Elves] ERROR: xcopy failed, some files may be in use
    pause
    exit /b 1
)
echo [Elves] cleaning staging...
rmdir /s /q "{STAGING_DIR}"
echo [Elves] clearing WebView2 cache...
{webview_clear_lines}
echo [Elves] launching...
{launch}
del "%~f0"
'''
        os.makedirs(os.path.dirname(BAT_PATH), exist_ok=True)
        with open(BAT_PATH, "w", encoding="utf-8") as f:
            f.write(script)

        _log.info("apply_and_restart: launching batch and exiting")
        subprocess.Popen(
            f'cmd /c "{BAT_PATH}"',
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        os._exit(0)
