import time
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

from script.core.TaskConfigScheduler import taskConfigScheduler
from script.utils.Api import api


class Scheduler:
    def __init__(self, queueListener):
        self.sched = BackgroundScheduler(daemon=True, timezone=ZoneInfo('Asia/Shanghai'))
        self.queueListener = queueListener
        self.addScheduledTasks()

    def restart(self):
        if not taskConfigScheduler.common.restart:
            return
        self.queueListener.emit(
            {
                "event": "JS:EMIT",
                "args": (
                    "API:LOGS:ADD",
                    {
                        "time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                        "data": "五点重启任务"
                    }
                )
            }
        )
        api.emit("API:SCRIPT:END")
        api.emit("API:SCRIPT:LAUNCH", "默认配置", taskConfigScheduler.common.__dict__)

    def addScheduledTasks(self):
        self.sched.add_job(
            self.restart,
            "cron",
            hour=5,
            minute=10,
            timezone="Asia/Shanghai"
        )
