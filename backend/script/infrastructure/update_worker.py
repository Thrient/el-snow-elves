"""更新执行器 — 下载更新 + 替换文件 + 重启"""
import logging
import os
import shutil
import subprocess
import sys
from script.api.JsApi import js
from script.config.Setting import APP_DATA, STORAGE_PATH
from script.infrastructure.update_engine import UpdateEngine, APP_DIR

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
            _log.info(f"download_updates: [{i + 1}/{total_files}] {item['path']} (id={item['fingerprint_id']}, size={item['size']})")
            try:
                file_bytes_before = downloaded_bytes

                def on_chunk(received: int, _total: int):
                    js.update_progress_bytes(file_bytes_before + received)

                UpdateEngine.download_blob(item["fingerprint_id"], save_path, on_progress=on_chunk)
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
        log = os.path.join(APP_DATA, "_update.log")
        tee = f'>> "{log}" 2>&1'

        lines = ["@echo off"]
        # 日志头
        lines.append(f'echo [Elves] ==== UPDATE START %date% %time% ==== {tee}')
        lines.append(f'echo [Elves] PID={pid} STAGING={STAGING_DIR} APP_DIR={APP_DIR} {tee}')

        # 等主进程退出
        lines.append(f'echo [Elves] waiting for PID {pid} to exit... {tee}')
        lines.append(":waitloop")
        lines.append(f'tasklist /fi "PID eq {pid}" 2>nul | find /i "{pid}" >nul')
        lines.append("if not errorlevel 1 (")
        lines.append("    timeout /t 1 /nobreak > nul")
        lines.append("    goto waitloop")
        lines.append(")")

        # 主进程已退出，额外等 3 秒让 Windows 释放子进程文件句柄
        lines.append(f'echo [Elves] PID {pid} exited, waiting for file handles... {tee}')
        lines.append("timeout /t 3 /nobreak > nul")

        # 复制文件
        lines.append(f'echo [Elves] copying files... {tee}')
        lines.append(f'xcopy /y /s /e "{STAGING_DIR}\\*" "{APP_DIR}\\\\" {tee}')
        lines.append("if errorlevel 1 (")
        lines.append(f'    echo [Elves] ERROR: xcopy failed, retrying with robocopy... {tee}')
        lines.append(f'    robocopy "{STAGING_DIR}" "{APP_DIR}" /e /is /it /r:3 /w:3 {tee}')
        lines.append("    if errorlevel 8 (")
        lines.append(f"        echo [Elves] FATAL: robocopy also failed {tee}")
        lines.append("    )")
        lines.append(")")

        # 清理
        lines.append(f'echo [Elves] cleaning staging... {tee}')
        lines.append(f'rmdir /s /q "{STAGING_DIR}" {tee} 2>nul')

        lines.append(f'echo [Elves] clearing WebView2 cache... {tee}')
        for d in cache_dirs:
            lines.append(f'if exist "{d}" rmdir /s /q "{d}" {tee} 2>nul')

        lines.append(f'echo [Elves] launching... {tee}')
        lines.append(launch)
        lines.append(f'echo [Elves] ==== UPDATE DONE %date% %time% ==== {tee}')
        lines.append('del "%~f0"')
        return "\n".join(lines)

    @staticmethod
    def apply_and_restart():
        """写入重启脚本并启动 batch（batch 会等本进程退出后替换文件并重启）"""
        pid = os.getpid()
        _log.info(f"apply_and_restart: pid={pid} staging={STAGING_DIR} app_dir={APP_DIR}")

        if getattr(sys, 'frozen', False):
            launch = f'start "" "{sys.executable}"'
        else:
            entry = os.path.join(APP_DIR, "Elves.py")
            launch = f'start "" "{sys.executable}" "{entry}"'

        script = UpdateWorker._build_bat(pid, launch, WEBVIEW_CACHE_DIRS)

        os.makedirs(os.path.dirname(BAT_PATH), exist_ok=True)
        with open(BAT_PATH, "w") as f:
            f.write(script)

        _log.info("apply_and_restart: launching batch (will wait for us to exit)")
        subprocess.Popen(
            f'cmd /c "{BAT_PATH}"',
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0,
        )
        # 不调 os._exit(0)，由调用方走正常退出流程 → window.destroy() → WebView2 干净退出
