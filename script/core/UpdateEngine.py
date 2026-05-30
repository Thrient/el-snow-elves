"""更新引擎 — 版本检查 + manifest diff + 文件下载"""
import hashlib
import logging
import os
import sys
import time

import requests

_log = logging.getLogger("Elves.UpdateEngine")

HUB_URL = "https://elves.elarion.cn/api/v1"

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "temp", "build", "dist", "_update_staging"}
EXCLUDE_FILES = {"manifest.json", "_restart.bat", "Elves.spec"}


class UpdateEngine:
    _session: requests.Session | None = None

    @classmethod
    def _get_session(cls) -> requests.Session:
        if cls._session is None:
            cls._session = requests.Session()
            cls._session.headers["Connection"] = "keep-alive"
        return cls._session

    @staticmethod
    def compute_manifest() -> dict[str, str]:
        """扫描应用目录，返回 {relative_path: sha256}"""
        manifest = {}
        for root, dirs, files in os.walk(APP_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f in EXCLUDE_FILES:
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, APP_DIR).replace("\\", "/")
                try:
                    with open(full, "rb") as fh:
                        manifest[rel] = hashlib.sha256(fh.read()).hexdigest()
                except OSError:
                    pass
        return manifest

    @staticmethod
    def check_version() -> dict | None:
        """返回最新版本信息 {'version','changelog','is_mandatory','is_latest'} 或 None"""
        try:
            _log.info(f"check_version: GET {HUB_URL}/versions")
            resp = UpdateEngine._get_session().get(f"{HUB_URL}/versions", timeout=10)
            data = resp.json()
            versions = data.get("data", [])
            for v in versions:
                if v.get("is_latest"):
                    _log.info(f"check_version: latest={v.get('version')}")
                    return v
            _log.info("check_version: no latest found")
            return None
        except Exception as e:
            _log.error(f"check_version failed: {e}")
            return None

    @staticmethod
    def diff_manifest(current_version: str, local_manifest: dict[str, str]) -> dict:
        """POST /versions/diff，返回 {latest_version, changelog, is_mandatory, changed, removed}"""
        try:
            _log.info(f"diff_manifest: POST {HUB_URL}/versions/diff current={current_version} manifest_keys={len(local_manifest)}")
            resp = UpdateEngine._get_session().post(
                f"{HUB_URL}/versions/diff",
                json={"current_version": current_version, "manifest": local_manifest},
                timeout=30,
            )
            data = resp.json()
            changed = len(data.get("changed", []))
            removed = len(data.get("removed", []))
            _log.info(f"diff_manifest: ok latest={data.get('latest_version')} changed={changed} removed={removed}")
            return data
        except Exception as e:
            _log.error(f"diff_manifest failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def download_blob(fingerprint_id: int, save_path: str, on_progress=None):
        """下载单个 blob 到指定路径。on_progress(received, total) 最多每秒回调一次。"""
        t0 = time.time()
        resp = UpdateEngine._get_session().get(f"{HUB_URL}/versions/blobs/{fingerprint_id}", stream=True, timeout=120)
        resp.raise_for_status()
        total = int(resp.headers.get("Content-Length", 0))
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        received = 0
        last_push = 0.0
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                f.write(chunk)
                received += len(chunk)
                now = time.time()
                if on_progress and (now - last_push >= 1.0 or received >= total):
                    on_progress(received, total)
                    last_push = now
        elapsed = time.time() - t0
        if elapsed > 0 and total > 0:
            speed_mbps = (total * 8) / elapsed / 1_000_000
            _log.info(f"download_blob: id={fingerprint_id} {total/1024:.0f}KB in {elapsed:.1f}s = {speed_mbps:.1f}Mbps")
