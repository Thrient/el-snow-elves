"""更新执行器 — 下载更新 + 替换文件 + 重启"""
import logging
import os
import shutil
import subprocess
import sys
import json

import webview

from script.core.UpdateEngine import UpdateEngine, APP_DIR, MANIFEST_PATH

_log = logging.getLogger("Elves.UpdateWorker")

STAGING_DIR = os.path.join(APP_DIR, "_update_staging")
BAT_PATH = os.path.join(APP_DIR, "_restart.bat")


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
        local = UpdateEngine.load_local_manifest()
        if not local:
            _log.info("download_updates: no saved manifest, computing from disk")
            local = UpdateEngine.compute_manifest()
            UpdateEngine.save_manifest(local)
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

        # 更新本地 manifest：合并已变更文件的 SHA256
        new_manifest = dict(local)
        for item in changed:
            new_manifest[item["path"]] = item["sha256"]
        UpdateEngine.save_manifest(new_manifest)

        _push_js("window.useUpdateStore.getState().finishDownload()")
        _log.info(f"download_updates: done, {total} files downloaded")
        return {"ok": True, "file_count": total}

    @staticmethod
    def apply_and_restart():
        """写入重启脚本并退出应用。"""
        if getattr(sys, 'frozen', False):
            # 打包后：直接启动 exe
            launch = f'start "" "{sys.executable}"'
        else:
            # 开发模式：python 执行入口脚本
            entry = os.path.join(APP_DIR, "Elves.py")
            launch = f'start "" "{sys.executable}" "{entry}"'

        script = f'''@echo off
timeout /t 2 /nobreak > nul
xcopy /y /s /e "{STAGING_DIR}\\*" "{APP_DIR}\\"
rmdir /s /q "{STAGING_DIR}"
{launch}
del "%~f0"
'''
        with open(BAT_PATH, "w", encoding="utf-8") as f:
            f.write(script)

        subprocess.Popen(
            f'cmd /c "{BAT_PATH}"',
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE | 0x00000008,
        )
        return True
