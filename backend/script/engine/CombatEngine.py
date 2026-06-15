"""战斗连招引擎 — 独立的后台连招循环，不依赖 FlowEngine"""
import logging
from threading import Thread, Event

from script.engine.InputSimulator import InputSimulator


class CombatEngine:
    """后台连招循环：从 vp 传入的 config 解析技能按键，循环执行"""

    def __init__(self):
        self._input = InputSimulator()
        self._stop_event = Event()
        self._stop_event.set()

    def start(self, *args, **kwargs) -> None:
        """kwargs: combo(连招步骤列表，s 已是按键值), hwnd, predicate"""
        combo = kwargs.get("combo", [])
        hwnd = kwargs.get("hwnd")
        predicate = kwargs.get("predicate")
        self.stop()
        self._stop_event.clear()
        Thread(target=self._loop, args=(combo, hwnd, predicate), daemon=True).start()
        logging.info(f"⚔ 自动战斗: {' → '.join(s.get('s', '?') for s in combo)}")

    def stop(self) -> None:
        self._stop_event.set()

    def _loop(self, combo: list, hwnd: int, predicate) -> None:
        _paused = (lambda: not predicate()) if predicate else (lambda: False)
        while not self._stop_event.is_set() and not _paused():
            for step in combo:
                if self._stop_event.is_set() or _paused():
                    break

                key = step.get("s", "")
                if not key:
                    continue

                mode = step.get("m", "click")
                press_s = float(step.get("p", 0.1) or 0)
                delay_ms = float(step.get("d", 800) or 0)

                if mode == "down":
                    self._input.key_down(key=key, hwnd=hwnd, predicate=predicate, post_delay=delay_ms)
                elif mode == "up":
                    self._input.key_up(key=key, hwnd=hwnd, predicate=predicate, post_delay=delay_ms)
                else:
                    self._input.key_click(key=key, press=press_s, hwnd=hwnd, predicate=predicate, post_delay=delay_ms)

        self._stop_event.set()
        logging.info("⚔ 自动战斗已停止")
