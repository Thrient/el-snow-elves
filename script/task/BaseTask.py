import random

from script.config.Setting import OVERTIME
from script.core.InputSimulator import InputSimulator
from script.core.TemplateMatcher import TemplateMatcher
from script.functools.Functools import during, wait_until


class BaseTask:
    def __init__(self):
        self._matcher = TemplateMatcher()
        self._input = InputSimulator()

    def batch_template_match(self, *args, **kwargs):
        return self._matcher.batch_match(*args, **kwargs)

    def key_click(self, *args, **kwargs):
        return self._input.key_click(*args, **kwargs)

    def mouse_click(self, *args, **kwargs):
        return self._input.mouse_click(*args, **kwargs)

    def exits(self, *args, **kwargs):
        return self.batch_template_match(*args, **kwargs)

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

            if mode == "first":
                self.click_first(results=results, **kwargs)
            elif mode == "last":
                self.click_last(results=results, **kwargs)
            elif mode == "random":
                self.click_random(results=results, **kwargs)
            elif mode == "all":
                self.click_all(results=results, **kwargs)
            elif mode == "all_reverse":
                self.click_all_reverse(results=results, **kwargs)
            else:
                self.click_random(results=results, **kwargs)

            return results

        return _inner(**kwargs)

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
