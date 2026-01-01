import time
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler

from script.core.TaskConfigScheduler import taskConfigScheduler
from script.utils.Api import api


class Scheduler:
    def __init__(self):
        self.sched = BackgroundScheduler(daemon=True, timezone=ZoneInfo('Asia/Shanghai'))
        self.addScheduledTasks()

    @staticmethod
    def restart():
        if not taskConfigScheduler.common.restart:
            return
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
