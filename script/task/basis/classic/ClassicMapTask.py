from abc import ABC

from script.task.basis.classic.ClassicBasisTask import ClassicBasisTask


class ClassicMapTask(ClassicBasisTask, ABC):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def closeMap(self):
        """关闭地图"""

        if not self.exits("标志地图当前坐标"):
            return
        self.logs("关闭地图")
        self.closeCurrentUi()

    def openMap(self):
        """打开地图"""

        # 检查队伍界面是否已存在，如果不存在则按下T键打开
        if self.exits("标志地图当前坐标"):
            return
        self.logs("打开地图")
        self.click_key(key=self.taskConfig.keyList[23])

    def coordGo(self, x, y):
        """坐标前往"""

        self.logs(f"坐标前往 {x}:{y}")

        self.openMap()

        # 停止自动寻路功能
        self.touch("按钮地图停止寻路")

        # 展开坐标输入面板
        self.touch("按钮地图坐标展开")

        # 输入横坐标值
        self.touch("按钮地图横坐标")
        self.input(text=x)

        # 输入纵坐标值
        self.touch("按钮地图纵坐标")
        self.input(text=y)

        self.touch("按钮地图前往区域")

        self.closeMap()
        self.arrive()

    def areaGo(self, area):
        """前往指定区域"""
        __coordinate = {
            "金陵": (571, 484),
            "江南": (1095, 1117),
            "风雷岛": (970, 542),
            "中原": (1080, 996),
            "塞北": (1277, 718),
            "华山": (344, 206),
            "少林": (239, 326),
        }

        self.logs(f"前往{area}区域")
        self.openMap()

        self.touch("按钮地图世界区域")
        self.touch(f"按钮地图{area}区域")
        self.coordGo(__coordinate[area][0], __coordinate[area][1])

    def arrive(self):
        """寻路检测"""
        if self._finished.is_set():
            return
        from script.core.TaskFactory import TaskFactory

        cls = TaskFactory.instance().create(self.taskConfig.model, "到达检测")
        with cls(hwnd=self.hwnd, winConsole=self.winConsole, queueListener=self.queueListener) as obj:
            obj.execute()
