import time
from threading import Thread, Event


class MonitorEngine(Thread):
    def __init__(self, engine, monitors):
        super().__init__(daemon=True)
        self.engine = engine
        self.interval = monitors.get("interval", 1)
        self.loop = monitors.get("loop", [])
        self._stop_event = Event()
        self.start()

    def stop(self):
        self._stop_event.set()

    def run(self):
        """执行监控主循环"""
        if not self.loop:
            return
        while not self._stop_event.is_set():
            for step in self.loop:
                if self._stop_event.is_set():
                    break
                self.engine.run_subflow(step)
                time.sleep(self.interval)
