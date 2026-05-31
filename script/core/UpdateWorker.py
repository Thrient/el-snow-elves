"""更新执行器 — 下载更新 + 替换文件 + 重启"""
import logging
import os
import shutil
import subprocess
import sys
import time
import time

from script.api.JsApi import js
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


class UpdateWorker:
    @staticmethod
    def download_updates(current_version: str) -> dict:
        _log.info(f"download_updates: start current_version={current_version}")
        local = UpdateEngine.compute_manifest()
        _log.info(f"download_updates: manifest has {len(local)} entries")
        diff = UpdateEngine.diff_manifest(current_version, local)

        if "error" in diff:
            _log.error(f"download_updates: diff error: {diff['error']}")
            js.update_finish_download()
            return {"error": diff["error"]}

        if not diff.get("changed"):
            _log.info("download_updates: no changed files, up to date")
            return {"up_to_date": True}

        changed = diff["changed"]
        total_files = len(changed)
        total_bytes = sum(item["size"] for item in changed)
        _log.info(f"download_updates: {total_files} files, {total_bytes} bytes")

        js.update_start_download(total_files, total_bytes)

        if os.path.exists(STAGING_DIR):
            shutil.rmtree(STAGING_DIR)
        os.makedirs(STAGING_DIR)

        downloaded_bytes = 0
        for i, item in enumerate(changed):
            save_path = os.path.join(STAGING_DIR, item["path"])
            blob_id = item.get("record_id") or item["fingerprint_id"]
            _log.info(f"download_updates: [{i + 1}/{total_files}] {item['path']} (id={blob_id}, size={item['size']})")
            try:
                file_bytes_before = downloaded_bytes

                def on_chunk(received: int, _total: int):
                    js.update_progress_bytes(file_bytes_before + received)

                UpdateEngine.download_blob(blob_id, save_path, on_progress=on_chunk)
                downloaded_bytes += item["size"]
                _log.info(f"download_updates: {item['path']} done, {downloaded_bytes}/{total_bytes} bytes")
                js.update_progress(item["path"], i + 1, downloaded_bytes)
            except Exception as e:
                _log.error(f"download_updates: failed {item['path']}: {e}")
                js.update_finish_download()
                return {"error": f"download {item['path']}: {e}"}

        js.update_finish_download()
        _log.info(f"download_updates: done, {total_files} files, {total_bytes} bytes")
        return {"ok": True, "file_count": total_files}

    @staticmethod
    def _build_bat(pid: int, launch: str, cache_dirs: list[str]) -> str:
        lines = ["@echo off"]
        lines.append(f'echo [Elves] waiting for PID {pid} to exit...')
        lines.append(":waitloop")
        lines.append(f'tasklist /fi "PID eq {pid}" 2>nul | find /i "{pid}" >nul')
        lines.append("if not errorlevel 1 (")
        lines.append("    timeout /t 1 /nobreak > nul")
        lines.append("    goto waitloop")
        lines.append(")")
        lines.append("echo [Elves] copying files...")
        lines.append(f'xcopy /y /s /e "{STAGING_DIR}\\*" "{APP_DIR}\\"')
        lines.append("if errorlevel 1 (")
        lines.append("    echo [Elves] ERROR: xcopy failed, some files may be in use")
        lines.append("    pause")
        lines.append("    exit /b 1")
        lines.append(")")
        lines.append("echo [Elves] cleaning staging...")
        lines.append(f'rmdir /s /q "{STAGING_DIR}"')
        lines.append("echo [Elves] clearing WebView2 cache...")
        for d in cache_dirs:
            lines.append(f'if exist "{d}" rmdir /s /q "{d}"')
        lines.append("echo [Elves] launching...")
        lines.append(launch)
        lines.append('del "%~f0"')
        return "\n".join(lines)

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

        script = UpdateWorker._build_bat(pid, launch, WEBVIEW_CACHE_DIRS)

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
