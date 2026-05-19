import type { ReactNode } from "react";
import {
  AimOutlined,
  FieldTimeOutlined,
  ScanOutlined,
  DeploymentUnitOutlined,
  BorderOutlined,
  CodeSandboxOutlined,
  PushpinOutlined,
  FieldNumberOutlined,
  ColumnWidthOutlined,
  ColumnHeightOutlined,
  PauseOutlined,
  CaretRightOutlined,
  BulbOutlined,
  UserOutlined,
  DesktopOutlined,
  EditOutlined,
  PictureOutlined,
  SearchOutlined,
  ClockCircleOutlined,
  EyeInvisibleOutlined,
  SwapOutlined,
  BranchesOutlined,
} from "@ant-design/icons";

export interface ActionOpt {
  value: string;
  label: string;
  desc: string;
  icon: ReactNode;
  color: string;
  group: string;
}

export const ACTION_OPTS: ActionOpt[] = [
  { value: "touch",          label: "touch",          desc: "识别模板并点击",  icon: <PictureOutlined />,      color: "#3b82f6", group: "图像操作" },
  { value: "exits",          label: "exits",          desc: "检测模板是否存在", icon: <SearchOutlined />,        color: "#10b981", group: "图像操作" },
  { value: "wait",           label: "wait",           desc: "等待模板出现",    icon: <ClockCircleOutlined />,    color: "#f59e0b", group: "图像操作" },
  { value: "wait_disappear", label: "wait_disappear", desc: "等待模板消失",    icon: <EyeInvisibleOutlined />,   color: "#f97316", group: "图像操作" },
  { value: "key_click",      label: "key_click",      desc: "发送按键",        icon: <CodeSandboxOutlined />,    color: "#6366f1", group: "输入操作" },
  { value: "input",          label: "input",          desc: "输入文本",        icon: <EditOutlined />,           color: "#14b8a6", group: "输入操作" },
  { value: "mouse_click",    label: "mouse_click",    desc: "点击坐标",        icon: <PushpinOutlined />,        color: "#ec4899", group: "输入操作" },
  { value: "set_character",  label: "set_character",  desc: "捕获角色头像",    icon: <UserOutlined />,           color: "#8b5cf6", group: "角色账号" },
  { value: "switch_account", label: "switch_account", desc: "切换游戏账号",    icon: <SwapOutlined />,           color: "#1677ff", group: "角色账号" },
  { value: "{True}",         label: "{True}",         desc: "表达式",      icon: <BranchesOutlined />,       color: "#d4513b", group: "流程控制" },
];

export interface ParamMeta {
  label: string;
  color: string;
  icon: ReactNode;
  desc: string;
  tip?: string;
  range?: string;
}

export const PARAM_META: Record<string, ParamMeta> = {
  threshold:  { label: "匹配阈值",  color: "#ef4444", icon: <AimOutlined />,          desc: "匹配置信度，低于此值视为未匹配。越高越严格，越低越宽松",         range: "0 ~ 1，默认 0.85" },
  seconds:    { label: "超时时间",  color: "#f59e0b", icon: <FieldTimeOutlined />,    desc: "最长等待秒数，到达时间仍未匹配则判定失败。null 表示一直等待",     range: "默认 1.8s" },
  k:          { label: "确认帧数",  color: "#8b5cf6", icon: <ScanOutlined />,         desc: "需连续多少帧都未匹配才确认消失。值越大越可靠但越慢",               range: "默认 1" },
  click_mode: { label: "点击方式",  color: "#06b6d4", icon: <DeploymentUnitOutlined />, desc: "匹配到多个目标时的选择策略",                                       range: "random / first / last / all / all_reverse" },
  box:        { label: "匹配区域",  color: "#ec4899", icon: <BorderOutlined />,       desc: "限制搜索范围 [x1, y1, x2, y2]。缩小区域可大幅提速并减少误匹配",    range: "默认 [0, 0, 1335, 750]" },
  key:        { label: "按键名称",  color: "#3b82f6", icon: <CodeSandboxOutlined />,  desc: "模拟按下的键名。支持 A-Z / Enter / Escape / Space / Tab 等",       range: "如 Enter、A、Num0" },
  pos:        { label: "点击坐标",  color: "#10b981", icon: <PushpinOutlined />,       desc: "点击的屏幕绝对坐标 [x, y]。可点击定位按钮在窗口上拾取" },
  count:      { label: "重复次数",  color: "#84cc16", icon: <FieldNumberOutlined />,  desc: "按键或点击连续执行的次数",                                          range: "默认 1" },
  x:          { label: "X 偏移",    color: "#3b82f6", icon: <ColumnWidthOutlined />,  desc: "点击位置在匹配坐标上的 X 轴像素偏移",                                range: "默认 0" },
  y:          { label: "Y 偏移",    color: "#10b981", icon: <ColumnHeightOutlined />, desc: "点击位置在匹配坐标上的 Y 轴像素偏移",                                range: "默认 0" },
  pre_delay:  { label: "操作前延迟",color: "#f97316", icon: <PauseOutlined />,         desc: "执行操作前等待的时间，确保界面稳定后再操作",                         range: "默认 1500 ms" },
  post_delay: { label: "操作后延迟",color: "#84cc16", icon: <CaretRightOutlined />,    desc: "执行操作后等待的时间，确保界面响应完成后再继续",                     range: "默认 1500 ms" },
  preprocess: { label: "图像预处理",color: "#8b5cf6", icon: <BulbOutlined />,          desc: "对截图的额外图像处理，提高特定场景下的匹配准确率。二值化、反转、自适应等独立开关组合" },
  account_name: { label: "账号名称", color: "#1677ff", icon: <UserOutlined />,          desc: "已录制的账号名，用于登录时注入凭证。通常用变量 {account_name} 在任务配置中设定" },
  hwnd:         { label: "目标窗口", color: "#6366f1", icon: <DesktopOutlined />,      desc: "操作的目标窗口句柄。默认 {hwnd} 为当前窗口，可填固定句柄或变量", range: "如 0x12345 或 {my_hwnd}" },
  text:         { label: "输入文本", color: "#14b8a6", icon: <EditOutlined />,          desc: "模拟键盘逐字输入到窗口。支持 {变量} 表达式", range: "如 Hello World 或 {my_text}" },
};

export const ACTION_PARAMS: Record<string, string[]> = {
  touch:          ["threshold", "click_mode", "box", "pos", "x", "y", "pre_delay", "post_delay", "seconds", "k", "preprocess", "hwnd"],
  exits:          ["threshold", "seconds", "preprocess", "hwnd"],
  wait:           ["threshold", "seconds", "preprocess", "hwnd"],
  wait_disappear: ["threshold", "seconds", "preprocess", "hwnd"],
  key_click:      ["key", "pre_delay", "post_delay", "hwnd"],
  input:          ["text", "pre_delay", "post_delay", "hwnd"],
  mouse_click:    ["pos", "pre_delay", "post_delay", "hwnd"],
  set_character:  ["hwnd"],
  switch_account: ["account_name"],
  "{True}":       [],
};

/** 必填参数 — 切换动作时自动注入 */
export const REQUIRED_PARAMS: Record<string, string[]> = {
  key_click: ["key"],
  input: ["text"],
  mouse_click: ["pos"],
  switch_account: ["account_name"],
};

export const ACTIONS_WITH_TEMPLATES = new Set(["touch", "exits", "wait", "wait_disappear"]);
export const PLAIN_VALUE_PARAMS = new Set(["threshold", "seconds", "k", "pos", "box", "pre_delay", "post_delay"]);

export const BUILTIN_VARS: { value: string; label: string }[] = [
  { value: "{result}",    label: "{result}" },
  { value: "{hwnd}",      label: "{hwnd}" },
  { value: "{ChildHwnd}", label: "{ChildHwnd}" },
];

export interface EditorCtx {
  stepKeys: string[];
  builtinVars: { value: string; label: string }[];
  configVars: { value: string; label: string }[];
  taskValueVars: { value: string; label: string }[];
  taskSteps: { value: string; label: string }[];
  taskCommonSteps: { value: string; label: string }[];
  globalCommonSteps: { value: string; label: string }[];
  stepParamsMap: Record<string, Record<string, unknown>>;
  /** Raw step data — for looking up params directly */
  allStepsData: Record<string, {
    action?: string; params?: Record<string, unknown>;
    prefix?: any[]; postfix?: any[]; failure_extra?: any[]; success_extra?: any[];
    next?: string; success?: string; failure?: string;
  }>;
  /** Bump when user clicks refresh — children watch this to reload disk data */
  refreshKey: number;
  hwnd: string;
  taskName?: string;
  version?: string;
  /** Task runtime values — for variable type detection */
  values?: Record<string, unknown>;
  /** Layout — for inferring variable types from cell models */
  layout?: { model?: string; store?: string }[][];
}
