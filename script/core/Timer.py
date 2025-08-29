import time


class Timer:

    def __init__(self):
        self.__elapsedTime = 0
        self.__startTime = 0
        self.__paused = False

    def start(self):
        """
        开始计时器

        该函数记录开始时间并重置已用时间
        """
        self.__startTime = time.time()
        self.__elapsedTime = 0

    def stop(self):
        """
        停止计时器

        该函数重置已用时间和开始时间
        """
        self.__elapsedTime = 0
        self.__startTime = 0

    def paused(self):
        """
        暂停计时器

        该函数计算当前已用时间并累加到总已用时间中
        """
        self.__elapsedTime += time.time() - self.__startTime
        self.__paused = True

    def resume(self):
        """
        恢复计时器

        该函数重新设置开始时间为当前时间
        """
        self.__startTime = time.time()
        self.__paused = False

    def getElapsedTime(self):
        """
        获取已用时间

        返回值:
            float: 从开始到现在的总已用时间（秒）
        """
        if self.__paused:
            return self.__elapsedTime
        return self.__elapsedTime + time.time() - self.__startTime
