"""账号文件加密 — AES-256-GCM + 机器绑定密钥"""

import os
import hashlib
import json
import logging
import subprocess

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

SALT = b"elves-account-v1-salt\x00\x01\x02\x03"


def _machine_uid() -> bytes:
    """获取机器唯一标识"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-WmiObject Win32_ComputerSystemProduct).UUID"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip().encode()
    except Exception:
        pass

    try:
        r = subprocess.run(
            ["wmic", "csproduct", "get", "uuid"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000,
        )
        lines = r.stdout.strip().split("\n")
        if len(lines) > 1 and lines[1].strip():
            return lines[1].strip().encode()
    except Exception:
        pass

    # 兜底：机器名 + 用户名
    return f"{os.environ.get('COMPUTERNAME', '')}{os.environ.get('USERNAME', '')}".encode()


def _derive_key() -> bytes:
    """从机器UID派生AES256密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=600_000,
        backend=default_backend(),
    )
    return kdf.derive(_machine_uid())


_key = _derive_key()
_aesgcm = AESGCM(_key)


def encrypt(data: dict) -> bytes:
    """加密账号数据（每次随机nonce）"""
    nonce = os.urandom(12)
    plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
    ciphertext = _aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def decrypt(raw: bytes) -> dict:
    """解密账号数据"""
    nonce = raw[:12]
    ciphertext = raw[12:]
    plaintext = _aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))
