from apscheduler.schedulers.background import BackgroundScheduler

from script.core.TaskConfigScheduler import taskConfigScheduler
from script.utils.Api import api


class Scheduler:
    def __init__(self):
        self.sched = BackgroundScheduler(daemon=True)

    def start(self):
        self.sched.start()

    @staticmethod
    def restart():
        if not taskConfigScheduler.config.reStart:
            return
        api.emit("SWITCH:CHARACTER:SCHEDULER:CLEAR")
        api.emit("TASK:SCHEDULER:INIT")

    def addScheduledTasks(self):
        self.sched.add_job(
            self.restart,
            "cron",
            hour=5,
            minute=10,
            timezone="Asia/Shanghai"
        )


scheduler = Scheduler()
