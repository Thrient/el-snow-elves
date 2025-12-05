from abc import ABC

from script.config.Config import Config
from script.task.basis.classic.ClassicBasisTask import ClassicBasisTask


class ClassicInstanceTask(ClassicBasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def closeRewardUi(self, count=1):
        """关闭奖励界面"""
        # 指定奖励界面的坐标区域
        self.closeCurrentUi(count=count, box=(905, 201, 1118, 454))

    def closeCurrentUi(self, count=1, box=Config.BOX):
        """关闭当前界面"""
        # 循环执行关闭操作，直到达到指定次数或无法找到关闭按钮
        for i in range(count):
            if not self.touch(
                    "按钮关闭", "按钮关闭_V1", "按钮关闭_V2", "按钮关闭_V3",
                    box=box,
                    find_all=True,
                    click_mode="last"
            ):
                break

    def backToMain(self):
        """返回主界面"""
        if self._finished.is_set():
            return
        from script.core.TaskFactory import TaskFactory

        cls = TaskFactory.instance().create(self.taskConfig.model, "界面返回")
        with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
            obj.execute()

    def startInterconnected(self):
        """切换互联分线"""
        self.logs("开启互联")
        self.click_mouse(pos=(1230, 25))
        self.touch("标志互联分线", x=80)
        self.keepAlive()

    def switchBranchLine(self, index):
        """切换分线"""
        self.logs(f"切换分线{index}")
        digits = [int(d) for d in str(index)]
        args = [f"标志{i}" for i in digits]

        self.click_mouse(pos=(1230, 25))
        # 循环滑动屏幕查找目标分线按钮，每次向上滑动一定距离

        for _ in range(index // 7 + 5):
            results = self.exits("标志线", find_all=True)
            for result in results:
                if len(digits) == 1:
                    if self.exits(args[0], box=(result[0] - 35, result[1] - 20, result[0] - 15, result[1] + 20)):
                        self.click_mouse(pos=(result[0] - 30, result[1]))
                        return
                if len(digits) == 2:
                    if self.exits(args[0],
                                  box=(result[0] - 50, result[1] - 20, result[0] - 30, result[1] + 20)) and self.exits(
                        args[1], box=(result[0] - 35, result[1] - 20, result[0] - 15, result[1] + 20)):
                        self.click_mouse(pos=(result[0] - 50, result[1]))
                        return
            self.move_mouse(start=(1050, 555), end=(1050, 355))

        self.keepAlive()
