"""更新执行器 — 下载更新 + 替换文件 + 重启"""
import os
import shutil
import subprocess
import sys
import json

from script.core.UpdateEngine import UpdateEngine, APP_DIR, MANIFEST_PATH

STAGING_DIR = os.path.join(APP_DIR, "_update_staging")
BAT_PATH = os.path.join(APP_DIR, "_restart.bat")


class UpdateWorker:
    @staticmethod
    def download_updates(current_version: str) -> list[dict]:
        """返回进度事件列表，最后一个为 done/error。用于 IPC 返回给前端。"""
        local = UpdateEngine.load_local_manifest()
        diff = UpdateEngine.diff_manifest(current_version, local)

        if "error" in diff:
            return [{"error": diff["error"]}]

        if not diff.get("changed"):
            return [{"up_to_date": True}]

        changed = diff["changed"]
        total = len(changed)
        events = []

        # 清空暂存区
        if os.path.exists(STAGING_DIR):
            shutil.rmtree(STAGING_DIR)
        os.makedirs(STAGING_DIR)

        for i, item in enumerate(changed):
            save_path = os.path.join(STAGING_DIR, item["path"])
            try:
                UpdateEngine.download_blob(item["fingerprint_id"], save_path)
                events.append({
                    "progress": (i + 1) / total,
                    "current": item["path"],
                    "total": total,
                    "index": i + 1,
                })
            except Exception as e:
                events.append({"error": f"download {item['path']}: {e}"})
                return events

        # 下载完成 — 把最新版本号写入 staged manifest
        staged_manifest = {item["path"]: item["sha256"] for item in changed}
        manifest_path = os.path.join(STAGING_DIR, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(staged_manifest, f, indent=2)

        events.append({
            "done": True,
            "version": diff["latest_version"],
            "file_count": total,
        })
        return events

    @staticmethod
    def apply_and_restart():
        """写入重启脚本并退出应用。"""
        # 找出可执行文件路径
        if getattr(sys, 'frozen', False):
            me = sys.executable
        else:
            me = sys.executable

        script = f'''@echo off
timeout /t 2 /nobreak > nul
xcopy /y /s /e "{STAGING_DIR}\\*" "{APP_DIR}\\"
rmdir /s /q "{STAGING_DIR}"
start "" "{me}"
del "%~f0"
'''
        with open(BAT_PATH, "w", encoding="utf-8") as f:
            f.write(script)

        subprocess.Popen(
            f'cmd /c "{BAT_PATH}"',
            shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE | 0x00000008,  # DETACHED_PROCESS
        )
        return True
