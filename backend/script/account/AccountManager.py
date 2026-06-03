"""账号管理 — 每账号一个加密.dat文件 + 明文.meta元数据"""

import json
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

    # ── 元数据（明文，列表读取时不触发解密）──

    @staticmethod
    def _meta_path(name: str) -> str:
        return os.path.join(ACCOUNTS_DIR, f"{_safe_name(name)}.meta")

    @staticmethod
    def _read_meta(name: str) -> dict | None:
        p = AccountManager._meta_path(name)
        if os.path.isfile(p):
            try:
                return json.loads(open(p, "r", encoding="utf-8").read())
            except Exception:
                return None
        return None

    @staticmethod
    def _write_meta(name: str, meta: dict):
        with open(AccountManager._meta_path(name), "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)

    # ── 排序 ──

    @staticmethod
    def _order_path() -> str:
        return os.path.join(ACCOUNTS_DIR, "_order.json")

    @staticmethod
    def get_order() -> list[str]:
        p = AccountManager._order_path()
        if os.path.isfile(p):
            try:
                data = json.loads(open(p, "r", encoding="utf-8").read())
                return data.get("names", []) if isinstance(data, dict) else []
            except Exception:
                return []
        return []

    @staticmethod
    def save_order(names: list[str]):
        _ensure_dir()
        with open(AccountManager._order_path(), "w", encoding="utf-8") as f:
            json.dump({"names": names}, f, ensure_ascii=False)

    # ── 账号 CRUD ──

    @staticmethod
    def list_accounts():
        """返回账号列表（读.meta，不解密敏感数据），按 _order.json 排序"""
        _ensure_dir()
        accounts = []
        for f in os.listdir(ACCOUNTS_DIR):
            if f.endswith(".meta"):
                try:
                    meta = json.loads(open(os.path.join(ACCOUNTS_DIR, f), "r", encoding="utf-8").read())
                    accounts.append(meta)
                except Exception:
                    continue
        order = AccountManager.get_order()
        ordered = {name: i for i, name in enumerate(order)}
        accounts.sort(key=lambda x: (ordered.get(x["name"], len(order)), -x.get("createdAt", 0)))
        return accounts

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
        now = int(time.time() * 1000)
        if existing:
            merged = {**existing, **data, "updatedAt": now}
        else:
            merged = {**data, "createdAt": now}

        open(path, "wb").write(encrypt(merged))

        ca = data.get("channel_auth") or (existing or {}).get("channel_auth")
        acct_type = ca.get("channel_type", "官服") if ca else "官服"
        AccountManager._write_meta(name, {
            "name": name,
            "createdAt": existing.get("createdAt", now) if existing else now,
            "type": acct_type,
            "port": 443,
        })
        logging.info(f"[AccountManager] 保存账号: {name} ({acct_type})")

    @staticmethod
    def delete_account(name: str):
        path = AccountManager._path(name)
        meta = AccountManager._meta_path(name)
        if os.path.isfile(path):
            os.remove(path)
        if os.path.isfile(meta):
            os.remove(meta)
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

        old_meta = AccountManager._meta_path(name)
        if os.path.isfile(old_meta):
            meta = json.loads(open(old_meta, "r", encoding="utf-8").read())
        else:
            meta = {}
        meta["name"] = new_name
        AccountManager._write_meta(new_name, meta)
        if os.path.isfile(old_meta):
            os.remove(old_meta)
        logging.info(f"[AccountManager] 重命名: {name} -> {new_name}")
        return True
