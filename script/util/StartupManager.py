import os
import winreg

_AUTOSTART_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
_AUTOSTART_NAME = "Elves"


def get_autostart() -> bool:
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _AUTOSTART_NAME)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart(enabled: bool) -> bool:
    import sys
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _AUTOSTART_KEY, 0,
                             winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
    except Exception:
        return False

    if not enabled:
        try:
            winreg.DeleteValue(key, _AUTOSTART_NAME)
            return True
        except FileNotFoundError:
            return True
        except Exception:
            return False

    exe = sys.executable
    exe_name = os.path.basename(exe).lower()
    if "python" not in exe_name:
        target = exe
        work_dir = os.path.dirname(exe)
        cmd = f'cmd /c "cd /d {work_dir} && start "" "{target}" --tray"'
    else:
        from script.config.Setting import PROJECT_ROOT
        target = os.path.join(PROJECT_ROOT, "Elves.py")
        cmd = f'cmd /c "cd /d {PROJECT_ROOT} && start "" "{exe}" "{target}" --tray"'

    try:
        winreg.SetValueEx(key, _AUTOSTART_NAME, 0, winreg.REG_SZ, cmd)
        old_lnk = os.path.join(os.getenv("APPDATA", ""),
                               r"Microsoft\Windows\Start Menu\Programs\Startup\Elves.lnk")
        try:
            os.remove(old_lnk)
        except Exception:
            pass
        return True
    except Exception:
        return False
