"""更新引擎 — 版本检查 + manifest diff + 文件下载"""
import hashlib
import json
import logging
import os
import sys
import requests

_log = logging.getLogger("Elves.UpdateEngine")

from script.config.Setting import APP_DATA

HUB_URL = "https://nas.elarion.cn:5173/api/v1"

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MANIFEST_PATH = os.path.join(APP_DATA, "manifest.json")

EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "temp", "build", "dist", "_update_staging"}
EXCLUDE_FILES = {"manifest.json", "_restart.bat", "Elves.spec"}


class UpdateEngine:
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
    def load_local_manifest() -> dict[str, str]:
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 安装路径变了 → 抛弃旧 manifest，重新计算
            if data.get("install_path") != APP_DIR:
                _log.info("load_local_manifest: install_path changed, discarding cached manifest")
                return {}
            return data.get("files", {})
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_manifest(manifest: dict[str, str]):
        os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
        data = {"install_path": APP_DIR, "files": manifest}
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def check_version() -> dict | None:
        """返回最新版本信息 {'version','changelog','is_mandatory','is_latest'} 或 None"""
        try:
            _log.info(f"check_version: GET {HUB_URL}/versions")
            resp = requests.get(f"{HUB_URL}/versions", timeout=10)
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
            resp = requests.post(
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
    def download_blob(fingerprint_id: int, save_path: str):
        """下载单个 blob 到指定路径"""
        _log.debug(f"download_blob: id={fingerprint_id} → {save_path}")
        resp = requests.get(f"{HUB_URL}/blobs/{fingerprint_id}", stream=True, timeout=60)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
