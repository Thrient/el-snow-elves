import ctypes

import win32con
import win32gui
import win32ui

from script.utils.Utils import Utils
from PIL import Image


class WindowConsole:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.style = None

    def setWindowNoMenu(self):
        """
        设置窗口无菜单样式

        该函数通过修改窗口样式来移除窗口的标题栏、边框和系统菜单，
        实现无边框窗口效果，并设置窗口大小为1335x750

        参数:
            self: 类实例引用

        返回值:
            无
        """
        # 设置进程DPI感知级别
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # 确保窗口有效
        assert win32gui.IsWindow(self.hwnd), "无效窗口"
        # 获取当前窗口样式
        self.style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
        # 移除窗口标题栏、边框和系统菜单样式
        style = self.style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU)
        # 应用新的窗口样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)
        # 设置窗口位置和大小
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOP,
            0, 0,
            1335, 750,
            win32con.SWP_NOMOVE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
        )

    def setWinEnableClickThrough(self):
        """
        设置窗口为点击穿透模式

        该函数通过修改窗口扩展样式，使窗口具有分层和透明属性，
        从而实现鼠标点击可以穿透该窗口，不会拦截鼠标事件

        参数:
            self: 类实例引用

        返回值:
            无
        """
        # 确保窗口有效
        assert win32gui.IsWindow(self.hwnd), "无效窗口"

        # 获取窗口当前的扩展样式
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        # 添加分层和透明扩展样式标志
        ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        # 应用新的扩展样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        # 更新窗口位置和样式以使更改生效
        win32gui.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    def setWinUnEnableClickThrough(self):
        """
        设置窗口为非点击穿透状态

        该函数通过修改窗口的扩展样式来禁用点击穿透功能，使窗口能够正常接收鼠标事件。
        主要用于将之前设置为透明且可点击穿透的窗口恢复为普通窗口状态。

        参数:
            无

        返回值:
            无

        异常:
            AssertionError: 当窗口句柄无效时抛出
        """
        assert win32gui.IsWindow(self.hwnd), "无效窗口"

        # 获取当前窗口的扩展样式
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        # 移除WS_EX_LAYERED和WS_EX_TRANSPARENT样式，禁用点击穿透功能
        ex_style &= ~(win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)

        # 设置修改后的窗口扩展样式
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        # 更新窗口位置和样式，使更改生效
        win32gui.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED)

    def captureWindow(self):
        """
        捕获指定窗口的内容并返回PIL图像对象

        该函数通过GDI接口获取窗口句柄对应的窗口区域，执行位块传输操作来捕获窗口内容，
        然后将捕获的位图数据转换为PIL图像格式返回。

        Returns:
            Image: PIL图像对象，包含捕获的窗口内容

        Raises:
            ValueError: 当窗口尺寸无效时抛出
            RuntimeError: 当截图过程发生错误时抛出
        """
        try:
            rect = Utils.getWinRect(self.hwnd)

            if rect[2] - rect[0] <= 0 or rect[3] - rect[1] <= 0:
                raise ValueError(f"Invalid window dimensions: {rect}")

            left, top, right, bottom = rect
            width, height = right - left, bottom - top

            with WindowConsole.GdiContext(self.hwnd) as (hwnd_dc, mfc_dc, save_dc, bitmap):
                # 执行位块传输捕获内容
                save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)

                # 获取位图元数据
                bmp_info = bitmap.GetInfo()
                bits = bitmap.GetBitmapBits(True)

                # 计算对齐后的行跨距
                bits_pixel = bmp_info['bmBitsPixel']
                stride = ((width * bits_pixel + 31) // 32) * 4

                # 转换到PIL图像
                return Image.frombuffer(
                    'RGB',
                    (width, height),
                    bits,
                    'raw',
                    Utils.getOptimalBitmapMode(bits_pixel),
                    stride,
                    1
                )

        except Exception as e:
            raise RuntimeError(f"Screenshot failed: {str(e)}") from e

    class GdiContext:
        """安全管理GDI资源的上下文管理器"""

        def __init__(self, hwnd):
            self.hwnd = hwnd
            self.hwnd_dc = None
            self.mfc_dc = None
            self.save_dc = None
            self.bitmap = None

        def __enter__(self):
            """
            上下文管理器的进入方法，用于初始化窗口截图所需的设备上下文和位图资源。

            该方法会获取目标窗口的设备上下文，创建兼容的内存设备上下文和位图，
            为后续的窗口截图操作准备必要的资源。

            Returns:
                tuple: 包含(hwnd_dc, mfc_dc, save_dc, bitmap)的元组
                    - hwnd_dc: 窗口设备上下文句柄
                    - mfc_dc: 从窗口DC创建的MFC设备上下文对象
                    - save_dc: 兼容的内存设备上下文对象
                    - bitmap: 兼容位图对象

            Raises:
                RuntimeError: 当无法获取窗口设备上下文时抛出异常
            """
            # 获取窗口设备上下文
            self.hwnd_dc = win32gui.GetWindowDC(self.hwnd)
            if not self.hwnd_dc:
                raise RuntimeError("Cannot acquire window DC")

            # 创建兼容设备上下文
            self.mfc_dc = win32ui.CreateDCFromHandle(self.hwnd_dc)
            self.save_dc = self.mfc_dc.CreateCompatibleDC()

            # 创建兼容位图
            rect = Utils.getWinRect(self.hwnd)
            width, height = rect[2] - rect[0], rect[3] - rect[1]
            self.bitmap = win32ui.CreateBitmap()
            self.bitmap.CreateCompatibleBitmap(self.mfc_dc, width, height)
            self.save_dc.SelectObject(self.bitmap)

            return self.hwnd_dc, self.mfc_dc, self.save_dc, self.bitmap

        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            上下文管理器退出方法，用于清理和释放Windows图形设备上下文资源

            参数:
                exc_type: 异常类型，如果没有异常则为None
                exc_val: 异常值，如果没有异常则为None
                exc_tb: 异常追踪信息，如果没有异常则为None

            返回值:
                None
            """
            # 逆序清理资源
            if self.bitmap:
                win32gui.DeleteObject(self.bitmap.GetHandle())
            if self.save_dc:
                self.save_dc.DeleteDC()
            if self.mfc_dc:
                self.mfc_dc.DeleteDC()
            if self.hwnd_dc:
                win32gui.ReleaseDC(self.hwnd, self.hwnd_dc)
