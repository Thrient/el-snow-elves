import threading
from typing import Dict, Tuple, Callable, List

import keyboard


class HotkeyManager:
    """基于 keyboard 库的全局快捷键管理器"""

    def __init__(self):
        # 存储快捷键映射: {快捷键字符串: (回调函数, 描述, 热键ID)}
        self._hotkeys: Dict[str, Tuple[Callable, str]] = {}
        self._lock = threading.Lock()

    def register(self, hotkey: str, callback: Callable, description: str = "") -> bool:
        """
        注册全局快捷键

        Args:
            hotkey: 快捷键字符串（如 'ctrl+s', 'alt+space', 'f5'）
            callback: 触发时执行的函数（无参数）
            description: 快捷键功能描述

        Returns:
            注册成功返回 True，失败返回 False
        """
        with self._lock:
            if hotkey in self._hotkeys:
                print(f"快捷键 {hotkey} 已存在")
                return False

            if not callable(callback):
                print("回调函数必须是可调用对象")
                return False

            try:
                # 使用 keyboard 库注册快捷键，返回热键ID
                keyboard.add_hotkey(hotkey, callback)
                self._hotkeys[hotkey] = (callback, description)
                print(f"已注册快捷键: {hotkey} ({description})")
                return True
            except ValueError as e:
                print(f"注册快捷键失败: {e}")
                return False

    def unregister(self, hotkey: str) -> bool:
        """
        解绑指定快捷键

        Args:
            hotkey: 要解绑的快捷键字符串

        Returns:
            解绑成功返回 True，不存在或失败返回 False
        """
        with self._lock:
            if hotkey not in self._hotkeys:
                print(f"快捷键 {hotkey} 未注册")
                return False
            try:
                # 通过ID移除快捷键
                keyboard.remove_hotkey(hotkey)
                del self._hotkeys[hotkey]
                print(f"已解绑快捷键: {hotkey}")
                return True
            except Exception as e:
                print(f"解绑快捷键失败: {e}")
                return False

    def unregister_all(self) -> None:
        """解绑所有已注册的快捷键"""
        with self._lock:
            for hotkey in list(self._hotkeys.keys()):
                self.unregister(hotkey)
        print("所有快捷键已解绑")

    def get_all_hotkeys(self) -> List[Tuple[str, str]]:
        """获取所有快捷键信息"""
        with self._lock:
            return [(hk, desc) for hk, (_, desc, _) in self._hotkeys.items()]

    def list_all(self) -> None:
        """列出所有已注册的快捷键"""
        hotkeys = self.get_all_hotkeys()
        if not hotkeys:
            print("没有已注册的快捷键")
            return

        print("\n===== 已注册快捷键列表 =====")
        for hk, desc in hotkeys:
            print(f"{hk} → {desc or '无描述'}")
        print("===========================\n")


    def stop(self) -> None:
        """停止所有快捷键监听并清理资源"""
        self.unregister_all()
        # 停止 keyboard 库的监听线程
        keyboard.unhook_all()
        print("快捷键管理器已停止")


# 创建管理器实例
hot_key_manager = HotkeyManager()