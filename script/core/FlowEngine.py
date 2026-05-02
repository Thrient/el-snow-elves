import json
import os
import re
from threading import Thread, Event

from script.config.Setting import PROJECT_ROOT
from script.core.VariableProcessor import VariableProcessor
from script.task.BaseTask import BaseTask

_COMMON_CACHE = None


class FlowEngine(Thread):


    def __init__(self, **kwargs):
        super().__init__()
        self._hwnd = kwargs.get("hwnd")
        self._running = kwargs.get("running")
        self.work = kwargs.get("work")
        self.name = self.work.get("name")
        self.version = self.work.get("version")
        self._steps = self.work.get("steps", {})
        self._common = self._load_common()
        self._all_steps = {**self._common, **self._steps}
        self.step_name = kwargs.get("start") if "start" in kwargs else self.work.get("start")
        self.vp = kwargs.get("vp") if "vp" in kwargs else VariableProcessor(self.work.get("values"))

        monitors = self.work.get("monitors", {})
        self._monitor_loop = monitors.get("loop", [])
        self._monitor_interval = monitors.get("interval", 1)
        self._monitor_stop_event = Event()
        self._task = BaseTask()

    def _load_common(self):
        """
        加载 common 步骤定义：
        1. 从 resources/config/common.json 文件加载基础定义（首次读磁盘，后续复用缓存）。
        2. 若 work 中存在 "common" 字段，则用其内容覆盖/补充基础定义。
        返回合并后的字典。
        """
        global _COMMON_CACHE
        if _COMMON_CACHE is None:
            file_path = os.path.join(PROJECT_ROOT, "resources", "config", "common.json")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    _COMMON_CACHE = json.load(f)
            except FileNotFoundError:
                print(f"警告：公共步骤文件 '{file_path}' 不存在，使用空基础")
                _COMMON_CACHE = {}
            except json.JSONDecodeError as e:
                print(f"错误：文件 '{file_path}' JSON 解析失败: {e}，使用空基础")
                _COMMON_CACHE = {}

        base_common = dict(_COMMON_CACHE)

        # 用 work 中的 common 覆盖
        work_common = self.work.get("common", {})
        if work_common is not None:
            if not isinstance(work_common, dict):
                print("警告：work 中的 common 字段应为字典类型，将忽略")
            else:
                base_common.update(work_common)

        return base_common

    def process_step(self, name):
        try:
            return self._all_steps[name]
        except KeyError:
            raise KeyError(f"工作流 '{self.name}' 中步骤 '{name}' 未定义") from None

    def run_subflow(self, subflow_start_name):
        sub_engine = FlowEngine(
            start=subflow_start_name,
            hwnd=self._hwnd,
            running=self._running,
            work=self.work,
            vp=self.vp

        )
        sub_engine.run()

    def _resolve_params(self, params):
        if isinstance(params, str):
            return self.vp.process_value(params, result=None)
        elif isinstance(params, dict):
            return {k: self._resolve_params(v) for k, v in params.items()}
        elif isinstance(params, list):
            return [self._resolve_params(item) for item in params]
        return params

    def to_action(self, action_type, params, **extra_kwargs):
        args = params.get('args', ()) if isinstance(params, dict) else ()
        kwargs = {k: v for k, v in params.items() if k != 'args'} if isinstance(params, dict) else {}
        kwargs.update(extra_kwargs)

        method = getattr(self._task, action_type)
        class _ActionWrapper:
            @staticmethod
            def execute():
                return method(*args, **kwargs)

        return _ActionWrapper()

    def action(self, hwnd, step):
        action_str = step.get("action")
        if isinstance(action_str, str) and action_str.startswith('{') and action_str.endswith('}'):
            try:
                result = self.vp.process_value(action_str, result=None)
                return bool(result)
            except Exception as e:
                print(f"表达式错误: {action_str}, {e}")
                return False
        else:
            params = self._resolve_params(step.get("params", {}))
            wrapper = self.to_action(step.get("action"), params, hwnd=hwnd, name=self.name, version=self.version, predicate=lambda: not self._running.is_set())
            return wrapper.execute()

    @staticmethod
    def process_result(result, step):
        if not result and "failure" in step:
            return step["failure"]
        if result and "success" in step:
            return step["success"]
        if "next" in step:
            return step["next"]
        return "任务结束"

    @staticmethod
    def _expand_subflow_list(subflow_list):
        pattern = re.compile(r"(.+)\*(\d+)$")
        expanded = []
        for item in subflow_list:
            match = pattern.match(item) if isinstance(item, str) else None
            if match:
                name, count = match.groups()
                expanded.extend([name] * int(count))
            else:
                expanded.append(item)
        return expanded

    def _monitor_thread(self):
        """监控线程：循环执行 monitors.loop 中的步骤"""
        # 如果未配置 loop 或为空，则直接返回
        if not self._monitor_loop:
            return
        while not self._monitor_stop_event.is_set():
            for step_name in self._monitor_loop:
                if self._monitor_stop_event.is_set():
                    break
                self.run_subflow(step_name)
            # 等待间隔，期间可被停止事件打断
            self._monitor_stop_event.wait(timeout=self._monitor_interval)

    def loop(self):
        Thread(target=self._monitor_thread, daemon=True).start()

    def run(self):
        while not self._running.is_set() and self.step_name and self.step_name != "任务结束":
            step_def = self.process_step(self.step_name)

            # 执行前缀子流程
            for prefix_step in self._expand_subflow_list(step_def.get("prefix", [])):
                self.run_subflow(prefix_step)

            # 执行主操作
            result = self.action(self._hwnd, step_def)

            # 应用变量
            self.vp.apply_set(step_def, result)

            # 执行后缀子流程
            for postfix_step in self._expand_subflow_list(step_def.get("postfix", [])):
                self.run_subflow(postfix_step)

            # 执行失败附加子流程
            if not result:
                for failure_extra in self._expand_subflow_list(step_def.get("failure_extra", [])):
                    self.run_subflow(failure_extra)
            else:
                for success_extra in self._expand_subflow_list(step_def.get("success_extra", [])):
                    self.run_subflow(success_extra)
            self.step_name = self.process_result(result, step_def)
        self._monitor_stop_event.set()
