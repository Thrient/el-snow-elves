import json
import logging
import os
import re
import time
from threading import Thread, Event

from script.config.Setting import PROJECT_ROOT
from script.core.VariableProcessor import VariableProcessor
from script.task.BaseTask import BaseTask

_COMMON_CACHE = None


class FlowEngine(Thread):


    def __init__(self, **kwargs):
        super().__init__()
        self._hwnd = kwargs.get("hwnd")
        self._paused = kwargs.get("paused")
        self.work = kwargs.get("work")
        self.name = self.work.get("name")
        self.version = self.work.get("version")
        self._steps = self.work.get("steps", {})
        self._common = self._load_common()
        self._all_steps = {**self._common, **self._steps}
        self.step_name = kwargs.get("start") if "start" in kwargs else self.work.get("start")
        self._single_step = kwargs.get("single_step", False)
        self.vp = kwargs.get("vp") if "vp" in kwargs else VariableProcessor(self.work.get("values"))

        monitors = self.work.get("monitors", {})
        self._monitor_loop = monitors.get("loop", [])
        self._monitor_interval = monitors.get("interval", 1)
        self._monitor_stop_event = Event()
        self._task = BaseTask()
        self._validate()

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
                logging.warning(f"公共步骤文件不存在，使用空基础: {file_path}")
                _COMMON_CACHE = {}
            except json.JSONDecodeError as e:
                logging.error(f"公共步骤文件 JSON 解析失败，使用空基础: {file_path} | {e}")
                _COMMON_CACHE = {}

        base_common = dict(_COMMON_CACHE)

        # 用 work 中的 common 覆盖
        work_common = self.work.get("common", {})
        if work_common is not None:
            if not isinstance(work_common, dict):
                logging.warning("work 中 common 字段类型错误，预期字典，已忽略")
            else:
                base_common.update(work_common)

        return base_common

    def _validate(self):
        """校验工作流定义，发现错误时打印警告或抛出异常"""
        errors = []

        if not isinstance(self.work.get("steps", {}), dict):
            errors.append("'steps' 必须为字典")

        allowed_keys = {"action", "params", "prefix", "postfix", "success", "failure", "next",
                        "set", "retry", "extends", "failure_extra", "success_extra"}
        valid_names = {*self._all_steps, "任务结束"}

        for name, step in self._all_steps.items():
            if not isinstance(step, dict):
                errors.append(f"步骤 '{name}' 不是字典")
                continue
            if "action" not in step and "extends" not in step:
                errors.append(f"步骤 '{name}' 缺少 'action'")

            for key, expected in [("prefix", list), ("postfix", list),
                                  ("failure_extra", list), ("success_extra", list),
                                  ("params", dict), ("retry", dict)]:
                val = step.get(key)
                if val is not None and not isinstance(val, expected):
                    errors.append(f"步骤 '{name}' 的 '{key}' 应为 {expected.__name__}")

            for key in ("success", "failure", "next"):
                target = step.get(key)
                if target and target not in valid_names:
                    errors.append(f"步骤 '{name}' 的 '{key}' 指向未定义的 '{target}'")

            base = step.get("extends")
            if base and base not in self._all_steps:
                errors.append(f"步骤 '{name}' extends 的 '{base}' 未定义")

            if "retry" in step and not isinstance(step["retry"].get("times"), (int, type(None))):
                errors.append(f"步骤 '{name}' retry.times 应为整数")

            unknown = set(step) - allowed_keys
            if unknown:
                logging.warning(f"步骤含未知字段: {name} -> {unknown}")

        if errors:
            raise ValueError("工作流定义错误:\n  " + "\n  ".join(errors))

    def process_step(self, name):
        try:
            step = dict(self._all_steps[name])
        except KeyError:
            raise KeyError(f"工作流 '{self.name}' 中步骤 '{name}' 未定义") from None

        base_name = step.pop("extends", None)
        if base_name:
            try:
                base = self._all_steps[base_name]
            except KeyError:
                raise KeyError(f"继承的步骤 '{base_name}' 未定义") from None
            merged_params = {**base.get("params", {}), **step.get("params", {})}
            step = {**base, **step, "params": merged_params}
        return step

    def run_subflow(self, subflow_start_name, args={}):
        self.vp.bulk_update(args)
        sub_engine = FlowEngine(
            start=subflow_start_name,
            hwnd=self._hwnd,
            paused=self._paused,
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
                logging.error(f"表达式执行错误: {action_str} | {e}")
                return False
        else:
            params = self._resolve_params(step.get("params", {}))
            wrapper = self.to_action(step.get("action"), params, hwnd=hwnd, name=self.name, version=self.version, predicate=lambda: not self._paused.is_set())
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
            if isinstance(item, str):
                match = pattern.match(item)
                if match:
                    name, count = match.groups()
                    expanded.extend([(name, {}, None)] * int(count))
                else:
                    expanded.append((item, {}, None))
            elif isinstance(item, dict):
                name = item["step"]
                args = item.get("args", {})
                when = item.get("when")
                match = pattern.match(name)
                if match:
                    base_name, count = match.groups()
                    expanded.extend([(base_name, args, when)] * int(count))
                else:
                    expanded.append((name, args, when))
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
        logging.info(f"监控线程已启动: {self.name} | interval={self._monitor_interval}s")
        Thread(target=self._monitor_thread, daemon=True).start()

    def _run_extra(self, step_def, key):
        """执行附加子流程，支持 when 条件"""
        for name, args, when in self._expand_subflow_list(step_def.get(key, [])):
            if when:
                cond = self.vp.process_value(when, result=None)
                if not cond:
                    logging.info(f"子流程跳过 [when={when}]: {name}")
                    continue
            self.run_subflow(name, args)

    def _run_action(self, step_def):
        retry = step_def.get("retry", {})
        for attempt in range(retry.get("times", 1)):
            result = self.action(self._hwnd, step_def)
            if result:
                return result
            self._run_extra(step_def, "failure_extra")
            time.sleep(retry.get("interval", 0) / 1000)

        return []

    def run(self):
        logging.info(f"工作流开始: {self.name} v{self.version} | 起始步骤={self.step_name}")
        while not self._paused.is_set() and self.step_name and self.step_name != "任务结束":
            step_def = self.process_step(self.step_name)
            t0 = time.time()

            self._run_extra(step_def, "prefix")
            result = self._run_action(step_def)
            self.vp.apply_set(step_def, result)
            self._run_extra(step_def, "postfix")

            if result:
                self._run_extra(step_def, "success_extra")

            prev = self.step_name
            self.step_name = self.process_result(result, step_def)
            if self._single_step:
                self.step_name = "任务结束"
            elapsed = (time.time() - t0) * 1000
            logging.info(f"[{self.name}] {prev} → {self.step_name} | result={len(result) if isinstance(result, list) else result} | vars={self.vp.variables} | {elapsed:.0f}ms")
        logging.info(f"工作流结束: {self.name} v{self.version}")
        self._monitor_stop_event.set()
