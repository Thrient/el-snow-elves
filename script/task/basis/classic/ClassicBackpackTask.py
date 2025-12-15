from abc import ABC

from script.task.basis.classic.ClassicBasisTask import ClassicBasisTask


class ClassicBackpackTask(ClassicBasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def closeBackpack(self):
        """关闭背包"""
        if not self.exits("界面物品"):
            return
        self.logs("关闭背包")
        self.click_mouse(pos=(0, 0))
        self.closeCurrentUi()

    def openBackpack(self):
        """打开背包"""
        if self.exits("界面物品"):
            return
        self.logs("打开背包")
        self.click_key(key=self.taskConfig.keyList[20])

    def useBackpackArticles(self, model, articles, count):
        """使用背包道具"""
        self.openBackpack()
        self.touch(f"按钮物品{model}")
        self.touch("按钮搜索")
        self.touch("标志输入道具名称")
        self.input(text=articles)
        self.touch("按钮搜索")

        # 检查道具是否存在，如果不存在则返回False
        if not self.exits(f"标志物品{articles}"):
            self.logs(f"道具{articles}不存在")
            self.closeBackpack()
            return False

        # 循环使用指定次数的道具
        for _ in range(count):
            self.touch(f"标志物品{articles}")
            self.touch("按钮背包使用")
        self.closeBackpack()
        return True
