"""账号管理 — 每账号一个加密.dat文件"""

import os
import re
import time
import logging
from script.config.Setting import APP_DATA
from script.account.Crypto import encrypt, decrypt

ACCOUNTS_DIR = os.path.join(APP_DATA, "Config", "Accounts")


def _safe_name(name: str) -> str:
    """账号名 → 安全文件名"""
    return re.sub(r"[^a-zA-Z0-9_\-一-鿿]", "_", name)


def _ensure_dir():
    os.makedirs(ACCOUNTS_DIR, exist_ok=True)


class AccountManager:
    @staticmethod
    def list_accounts():
        """返回账号名列表（不含敏感信息）"""
        _ensure_dir()
        names = []
        for f in os.listdir(ACCOUNTS_DIR):
            if f.endswith(".dat"):
                try:
                    raw = open(os.path.join(ACCOUNTS_DIR, f), "rb").read()
                    data = decrypt(raw)
                    names.append({
                        "name": data["name"],
                        "createdAt": data.get("createdAt", 0),
                    })
                except Exception:
                    # 文件损坏或密钥不匹配，跳过
                    continue
        return names

    @staticmethod
    def list_account_names():
        return [a["name"] for a in AccountManager.list_accounts()]

    @staticmethod
    def _path(name: str) -> str:
        return os.path.join(ACCOUNTS_DIR, f"{_safe_name(name)}.dat")

    @staticmethod
    def get_account(name: str):
        """仅在需要时解密读取账号完整信息"""
        path = AccountManager._path(name)
        if not os.path.isfile(path):
            return None
        try:
            raw = open(path, "rb").read()
            return decrypt(raw)
        except Exception as e:
            logging.error(f"[AccountManager] 解密失败: {e}")
            return None

    @staticmethod
    def save_account(data: dict):
        name = data["name"]
        _ensure_dir()
        path = AccountManager._path(name)
        existing = None
        if os.path.isfile(path):
            try:
                existing = decrypt(open(path, "rb").read())
            except Exception:
                pass
        if existing:
            merged = {**existing, **data, "updatedAt": int(time.time() * 1000)}
        else:
            merged = {**data, "createdAt": int(time.time() * 1000)}
        open(path, "wb").write(encrypt(merged))
        logging.info(f"[AccountManager] 保存账号: {name}")

    @staticmethod
    def delete_account(name: str):
        path = AccountManager._path(name)
        if os.path.isfile(path):
            os.remove(path)
            logging.info(f"[AccountManager] 删除账号: {name}")
        return True

    @staticmethod
    def rename_account(name: str, new_name: str):
        old_path = AccountManager._path(name)
        if not os.path.isfile(old_path):
            return False
        try:
            data = decrypt(open(old_path, "rb").read())
        except Exception:
            return False
        data["name"] = new_name
        data["updatedAt"] = int(time.time() * 1000)
        new_path = AccountManager._path(new_name)
        open(new_path, "wb").write(encrypt(data))
        os.remove(old_path)
        logging.info(f"[AccountManager] 重命名: {name} -> {new_name}")
        return True
