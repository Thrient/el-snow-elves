import base64
import random
import subprocess

import cv2

from script.api.JsApi import js
from script.config.Setting import OVERTIME
from script.core.ColorMatcher import ColorMatcher
from script.engine.InputSimulator import InputSimulator
from script.engine.ScreenCapture import ScreenCapture
from script.engine.TemplateMatcher import TemplateMatcher
from script.functools.Functools import during, wait_until
from script.account.AccountManager import AccountManager
from script.account.AccountProxy import INJECTION, get_proxy
from script.account.HostsManager import HostsManager
from script.engine.CombatEngine import CombatEngine


class BaseTask:
    def __init__(self):
        self._matcher = TemplateMatcher()
        self._input = InputSimulator()
        self._color = ColorMatcher()
        self._combat = CombatEngine()

    def cleanup(self):
        """主流程结束时清理后台资源"""
        self._combat.stop()

    @staticmethod
    def ai_vision(*args, **kwargs):
        """截图 → Hub AI Vision → 返回识别文本。kwargs: box(可选), prompt(必填)"""
        from script.infrastructure.AiClient import AiClient

        hwnd = kwargs.get("hwnd")
        box = kwargs.get("box")
        prompt = kwargs.get("prompt", "")

        # 保留彩色原图，不做灰度转换
        img, _ = ScreenCapture.capture_gray(hwnd)

        if box and isinstance(box, (list, tuple)) and len(box) == 4:
            x1, y1, x2, y2 = [int(v) for v in box]
            img = img[y1:y2, x1:x2]

        # PNG 无损编码，保留色彩和细节
        _, buf = cv2.imencode(".png", img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        b64 = base64.b64encode(buf).decode()
        data_uri = f"data:image/png;base64,{b64}"

        return AiClient.vision(data_uri, prompt)

    def batch_template_match(self, *args, **kwargs):
        return self._matcher.batch_match(*args, **kwargs)

    def key_click(self, *args, **kwargs):
        self._input.key_click(*args, **kwargs)
        return True

    def key_down(self, *args, **kwargs):
        self._input.key_down(*args, **kwargs)
        return True

    def key_up(self, *args, **kwargs):
        self._input.key_up(*args, **kwargs)
        return True

    def mouse_click(self, *args, **kwargs):
        self._input.mouse_click(*args, **kwargs)
        return True

    def mouse_drag(self, *args, **kwargs):
        self._input.mouse_drag(*args, **kwargs)
        return True

    def exits(self, *args, **kwargs):
        return self.batch_template_match(*args, **kwargs)

    def wait(self, *args, **kwargs):
        """等待屏幕出现"""

        @wait_until(k=1)
        def _inner(**inner_kwargs):
            return self.batch_template_match(*args, **inner_kwargs)

        return _inner(**kwargs)

    def wait_disappear(self, *args, **kwargs):
        @wait_until(k=1, is_valid=lambda x: not bool(x))
        def _inner(**inner_kwargs):
            return self.batch_template_match(*args, **inner_kwargs)

        return _inner(**kwargs)

    def touch(self, *args, **kwargs):
        @during(seconds=OVERTIME, is_valid=lambda x: bool(x))
        def _inner(**inner_kwargs):
            mode = kwargs.get("click_mode", "random")
            results = self.batch_template_match(*args, **inner_kwargs)

            getattr(self, self._dispatch_click(mode))(results=results, **kwargs)
            return results

        return _inner(**kwargs)

    @staticmethod
    def _dispatch_click(mode):
        return {
            "first": "click_first",
            "last": "click_last",
            "random": "click_random",
            "all": "click_all",
            "all_reverse": "click_all_reverse",
        }.get(mode, "click_random")

    def click_first(self, **kwargs):
        results = kwargs.pop("results")
        if not results:
            return
        self.mouse_click(pos=results[0], **kwargs)

    def click_last(self, **kwargs):
        results = kwargs.pop("results")
        if not results:
            return
        self.mouse_click(pos=results[-1], **kwargs)

    def click_random(self, **kwargs):
        results = kwargs.pop("results")
        if not results:
            return
        self.mouse_click(pos=random.choice(results), **kwargs)

    def click_all(self, **kwargs):
        results = kwargs.pop("results")
        if not results:
            return
        for pos in results:
            self.mouse_click(pos=pos, **kwargs)

    def click_all_reverse(self, **kwargs):
        results = kwargs.pop("results")
        if not results:
            return
        for pos in reversed(results):
            self.mouse_click(pos=pos, **kwargs)

    @staticmethod
    def set_character(*args, **kwargs):
        hwnd = kwargs.get("hwnd")
        assert hwnd is not None, "缺少窗口句柄"

        box = kwargs.get("box", [158, 186, 742, 892])
        img, _ = ScreenCapture.capture_gray(hwnd=hwnd)
        character = img[box[0]:box[1], box[2]:box[3]]

        # 将图像编码为PNG格式的二进制数据
        _, buffer = cv2.imencode('.png', character)

        js.update_character({
            "character": f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}",
            "hwnd": hwnd
        })
        return True

    @staticmethod
    def switch_account(*args, **kwargs):
        """启用代理注入，后续登录请求自动注入凭证"""
        account_name = kwargs.get("account_name")
        account = AccountManager.get_account(account_name)
        token_info = account.get("token_info") if account else None
        channel_auth = account.get("channel_auth") if account else None

        proxy = get_proxy()
        proxy.mode = INJECTION
        proxy.channel_fake = False
        if channel_auth:
            proxy.token_info = {"source": "channel", "channel_auth": channel_auth}
            proxy.channel_fake = True
        else:
            proxy.token_info = token_info
        proxy.completed = False
        HostsManager.hijack()
        subprocess.run(["ipconfig", "/flushdns"], capture_output=True, creationflags=0x08000000)
        return True

    # ── 颜色动作 ──

    def exits_color(self, *args, **kwargs):
        return self._color.exits_color(**kwargs)

    def touch_color(self, *args, **kwargs):
        @during(seconds=OVERTIME, is_valid=lambda x: bool(x))
        def _inner(**inner_kwargs):
            results = self._color.match_color(**inner_kwargs)
            mode = kwargs.get("click_mode", "random")
            getattr(self, self._dispatch_click(mode))(results=results, **kwargs)
            return results
        return _inner(**kwargs)

    def wait_color(self, *args, **kwargs):
        @wait_until(k=1)
        def _inner(**inner_kwargs):
            return self._color.exits_color(**inner_kwargs)
        return _inner(**kwargs)

    def wait_color_disappear(self, *args, **kwargs):
        @wait_until(k=1, is_valid=lambda x: not bool(x))
        def _inner(**inner_kwargs):
            return self._color.exits_color(**inner_kwargs)
        return _inner(**kwargs)

    def input(self, *args, **kwargs):
        self._input.input(*args, **kwargs)
        return True

    def monitor_start(self, *args, **kwargs):
        self._combat.start(*args, **kwargs)
        return True

    def monitor_stop(self, *args, **kwargs):
        self._combat.stop()
        return True

    @staticmethod
    def notify(*args, **kwargs):
        """发送通知到前端。params: title, description, type, duration"""
        title = kwargs.get("title", "")
        description = kwargs.get("description", "")
        type_ = kwargs.get("type", "info")
        duration = kwargs.get("duration", 5000)

        if not title and not description:
            return False

        js.push_notification(
            title=str(title),
            description=str(description),
            type=str(type_),
            duration=int(duration),
        )
        return True

