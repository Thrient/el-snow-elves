"""Windows hosts文件管理 — 劫持/还原"""

import os
import logging

MARKER = "# ELVES_AUTO_HIJACK"
LOGIN_DOMAINS = ["service.mkey.163.com", "sdk-os.mpsdk.easebar.com"]


class HostsManager:
    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"

    @staticmethod
    def hijack(domains=None):
        """将登录域名劫持到127.0.0.1"""
        domains = domains or LOGIN_DOMAINS
        if not domains:
            return False

        try:
            with open(HostsManager.HOSTS_PATH, "r", encoding="utf-8") as f:
                content = f.read()

            if f"127.0.0.1 {domains[0]} {MARKER}" in content:
                logging.info("[HostsManager] 已经劫持，跳过")
                return True

            entries = [f"127.0.0.1 {d} {MARKER}" for d in domains]
            new_content = content.rstrip("\n") + "\n" + "\n".join(entries) + "\n"

            with open(HostsManager.HOSTS_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)

            logging.info(f"[HostsManager] 劫持 {len(domains)} 个域名: {domains}")
            return True
        except PermissionError:
            logging.error("[HostsManager] 权限不足，请以管理员身份运行")
            return False
        except Exception as e:
            logging.error(f"[HostsManager] 劫持失败: {e}")
            return False

    @staticmethod
    def restore():
        """移除劫持条目"""
        try:
            with open(HostsManager.HOSTS_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = [line for line in lines if MARKER not in line]

            if len(new_lines) == len(lines):
                logging.info("[HostsManager] 无劫持条目需要还原")
                return True

            with open(HostsManager.HOSTS_PATH, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            logging.info("[HostsManager] 已还原hosts")
            return True
        except PermissionError:
            logging.error("[HostsManager] 权限不足，请以管理员身份运行")
            return False
        except Exception as e:
            logging.error(f"[HostsManager] 还原失败: {e}")
            return False
