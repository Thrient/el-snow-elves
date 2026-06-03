import json
import os
import winreg


def find_game_exe(config_path: str) -> str | None:
    # 读已保存的路径
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                saved = json.load(f).get("game_exe", "")
            if saved and os.path.isfile(saved):
                return saved
    except Exception:
        pass

    # 尝试注册表检测
    exe = None
    reg_roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    keywords = ["一梦江湖", "wyclx", "yimeng", "Yimeng"]

    for root, subkey in reg_roots:
        if exe:
            break
        try:
            with winreg.OpenKey(root, subkey) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        sub = winreg.EnumKey(key, i)
                        with winreg.OpenKey(root, f"{subkey}\\{sub}") as sk:
                            name, _ = winreg.QueryValueEx(sk, "DisplayName") if True else ("", "")
                    except Exception:
                        continue
                    try:
                        name = winreg.QueryValueEx(sk, "DisplayName")[0]
                        if any(kw in str(name) for kw in keywords):
                            try:
                                exe = winreg.QueryValueEx(sk, "DisplayIcon")[0]
                                if exe and os.path.isfile(exe):
                                    break
                            except Exception:
                                pass
                            try:
                                install = winreg.QueryValueEx(sk, "InstallLocation")[0]
                                if install:
                                    for root_dir, _, files in os.walk(install):
                                        for f in files:
                                            if f.endswith(".exe") and any(kw.lower() in f.lower() for kw in ["launcher", "game", "client", "ym", "yj"]):
                                                exe = os.path.join(root_dir, f)
                                                break
                                        if exe:
                                            break
                            except Exception:
                                pass
                    except Exception:
                        continue
        except Exception:
            continue

    if not exe:
        return None

    # 持久化保存
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        data = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["game_exe"] = exe
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass

    return exe
