"""更新引擎 — 版本检查 + manifest diff + 文件下载"""
import hashlib
import json
import os
import requests

HUB_URL = "https://nas.elarion.cn:5173/api/v1"
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(APP_DIR, "manifest.json")

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
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_manifest(manifest: dict[str, str]):
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    @staticmethod
    def check_version() -> dict | None:
        """返回最新版本信息 {'version','changelog','is_mandatory','is_latest'} 或 None"""
        try:
            resp = requests.get(f"{HUB_URL}/versions", timeout=10)
            data = resp.json()
            versions = data.get("data", [])
            for v in versions:
                if v.get("is_latest"):
                    return v
            return None
        except Exception:
            return None

    @staticmethod
    def diff_manifest(current_version: str, local_manifest: dict[str, str]) -> dict:
        """POST /versions/diff，返回 {latest_version, changelog, is_mandatory, changed, removed}"""
        try:
            resp = requests.post(
                f"{HUB_URL}/versions/diff",
                json={"current_version": current_version, "manifest": local_manifest},
                timeout=30,
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def download_blob(fingerprint_id: int, save_path: str):
        """下载单个 blob 到指定路径"""
        resp = requests.get(f"{HUB_URL}/blobs/{fingerprint_id}", stream=True, timeout=60)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
