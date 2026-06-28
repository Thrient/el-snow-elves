import type { ReactNode } from "react";
import {
  AimOutlined, FieldTimeOutlined, ScanOutlined, DeploymentUnitOutlined,
  BorderOutlined, CodeSandboxOutlined, PushpinOutlined, FieldNumberOutlined,
  ColumnWidthOutlined, ColumnHeightOutlined, PauseOutlined, CaretRightOutlined,
  BulbOutlined, UserOutlined, DesktopOutlined, EditOutlined, PictureOutlined,
  SearchOutlined, ClockCircleOutlined, EyeOutlined, EyeInvisibleOutlined, BgColorsOutlined,
  SwapOutlined, BranchesOutlined, BellOutlined,
} from "@ant-design/icons";
import type { VarType, SubflowRef } from "./index";

// ── Action definitions ──

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
  { value: "exits_color",         label: "exits_color",         desc: "检测颜色是否存在",   icon: <BgColorsOutlined />,       color: "#06b6d4", group: "颜色操作" },
  { value: "touch_color",         label: "touch_color",         desc: "找色并点击",         icon: <BgColorsOutlined />,       color: "#0891b2", group: "颜色操作" },
  { value: "wait_color",          label: "wait_color",          desc: "等待颜色出现",       icon: <BgColorsOutlined />,       color: "#0e7490", group: "颜色操作" },
  { value: "wait_color_disappear",label: "wait_color_disappear",desc: "等待颜色消失",       icon: <BgColorsOutlined />,       color: "#155e75", group: "颜色操作" },
  { value: "key_click",      label: "key_click",      desc: "发送按键",        icon: <CodeSandboxOutlined />,    color: "#6366f1", group: "输入操作" },
  { value: "input",          label: "input",          desc: "输入文本",        icon: <EditOutlined />,           color: "#14b8a6", group: "输入操作" },
  { value: "mouse_click",    label: "mouse_click",    desc: "点击坐标",        icon: <PushpinOutlined />,        color: "#ec4899", group: "输入操作" },
  { value: "mouse_drag",    label: "mouse_drag",    desc: "拖拽鼠标",        icon: <ColumnWidthOutlined />,     color: "#f43f5e", group: "输入操作" },
  { value: "set_character",  label: "set_character",  desc: "捕获角色头像",    icon: <UserOutlined />,           color: "#8b5cf6", group: "角色账号" },
  { value: "switch_account", label: "switch_account", desc: "切换游戏账号",    icon: <SwapOutlined />,           color: "#1677ff", group: "角色账号" },
  { value: "monitor_start",  label: "monitor_start",  desc: "开始自动战斗",    icon: <CaretRightOutlined />,     color: "#52c41a", group: "战斗系统" },
  { value: "monitor_stop",   label: "monitor_stop",   desc: "停止自动战斗",    icon: <PauseOutlined />,          color: "#ff4d4f", group: "战斗系统" },
  { value: "notify",        label: "notify",        desc: "发送通知提示",    icon: <BellOutlined />,          color: "#fa8c16", group: "流程控制" },
  { value: "ai_vision",     label: "ai_vision",     desc: "AI视觉分析",      icon: <EyeOutlined />,           color: "#722ed1", group: "AI" },
  { value: "{True}",         label: "{True}",         desc: "表达式",      icon: <BranchesOutlined />,       color: "#d4513b", group: "流程控制" },
];

// ── Param metadata ──

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
  color:      { label: "目标颜色",  color: "#06b6d4", icon: <BgColorsOutlined />,      desc: "要匹配的目标颜色 [R, G, B]，如 [255, 0, 0] 红色",                    range: "[0~255, 0~255, 0~255]" },
  tolerance:  { label: "颜色容差",  color: "#0891b2", icon: <FieldNumberOutlined />,  desc: "RGB 欧氏距离的容差阈值。0=精确匹配，值越大越宽松",                     range: "0~255，默认 10" },
  seconds:    { label: "超时时间",  color: "#f59e0b", icon: <FieldTimeOutlined />,    desc: "最长等待时间，到达时间仍未匹配则判定失败。null 表示一直等待",     range: "默认 1800 ms" },
  k:          { label: "确认帧数",  color: "#8b5cf6", icon: <ScanOutlined />,         desc: "需连续多少帧都未匹配才确认消失。值越大越可靠但越慢",               range: "默认 1" },
  click_mode: { label: "点击方式",  color: "#06b6d4", icon: <DeploymentUnitOutlined />, desc: "匹配到多个目标时的选择策略",                                       range: "random / first / last / all / all_reverse" },
  box:        { label: "匹配区域",  color: "#ec4899", icon: <BorderOutlined />,       desc: "限制搜索范围 [x1, y1, x2, y2]。缩小区域可大幅提速并减少误匹配",    range: "默认 [0, 0, 1335, 750]" },
  key:        { label: "按键名称",  color: "#3b82f6", icon: <CodeSandboxOutlined />,  desc: "模拟按下的键名。支持 A-Z / Enter / Escape / Space / Tab 等",       range: "如 Enter、A、Num0" },
  pos:        { label: "点击坐标",  color: "#10b981", icon: <PushpinOutlined />,       desc: "点击的屏幕绝对坐标 [x, y]。可点击定位按钮在窗口上拾取" },
  start_pos:  { label: "起始坐标",  color: "#10b981", icon: <PushpinOutlined />,       desc: "拖拽起始的屏幕绝对坐标 [x, y]。可点击定位按钮在窗口上拾取" },
  end_pos:    { label: "终点坐标",  color: "#f43f5e", icon: <PushpinOutlined />,       desc: "拖拽终点的屏幕绝对坐标 [x, y]。鼠标左键从 start_pos 拖至此位置" },
  count:      { label: "重复次数",  color: "#84cc16", icon: <FieldNumberOutlined />,  desc: "按键或点击连续执行的次数",                                          range: "默认 1" },
  x:          { label: "X 偏移",    color: "#3b82f6", icon: <ColumnWidthOutlined />,  desc: "点击位置在匹配坐标上的 X 轴像素偏移",                                range: "默认 0" },
  y:          { label: "Y 偏移",    color: "#10b981", icon: <ColumnHeightOutlined />, desc: "点击位置在匹配坐标上的 Y 轴像素偏移",                                range: "默认 0" },
  end_x:      { label: "终点 X 偏移", color: "#e11d48", icon: <ColumnWidthOutlined />,  desc: "拖拽终点在匹配坐标上的 X 轴像素偏移",                                range: "默认 0" },
  end_y:      { label: "终点 Y 偏移", color: "#be123c", icon: <ColumnHeightOutlined />, desc: "拖拽终点在匹配坐标上的 Y 轴像素偏移",                                range: "默认 0" },
  duration:   { label: "时长(ms)",  color: "#f97316", icon: <FieldTimeOutlined />,     desc: "持续时间。拖拽=耗时，通知=显示时长，0=不自动关闭",                    range: "拖拽 500ms / 通知 5000ms" },
  press:       { label: "按下时长", color: "#f97316", icon: <FieldTimeOutlined />,   desc: "按下后保持的持续时间。0=普通点击，>0=长按",                       range: "默认 0 ms" },
  pre_delay:  { label: "操作前延迟",color: "#f97316", icon: <PauseOutlined />,         desc: "执行操作前等待的时间，确保界面稳定后再操作",                         range: "默认 1500 ms" },
  post_delay: { label: "操作后延迟",color: "#84cc16", icon: <CaretRightOutlined />,    desc: "执行操作后等待的时间，确保界面响应完成后再继续",                     range: "默认 1500 ms" },
  dealy:     { label: "重试间隔",  color: "#f59e0b", icon: <FieldTimeOutlined />,    desc: "匹配失败后重试的间隔，避免高频轮询消耗性能",                         range: "默认 500 ms" },
  preprocess: { label: "图像预处理",color: "#8b5cf6", icon: <BulbOutlined />,          desc: "对截图的额外图像处理，提高特定场景下的匹配准确率。二值化、反转、自适应等独立开关组合" },
  method:     { label: "匹配算法",  color: "#db2777", icon: <ScanOutlined />,         desc: "模板匹配算法。ccoeff=相关系数（默认，不抗旋转缩放），sift=特征点（抗旋转缩放透视）", range: "ccoeff / sift" },
  account_name: { label: "账号名称", color: "#1677ff", icon: <UserOutlined />,          desc: "已录制的账号名，用于登录时注入凭证。通常用变量 {account_name} 在任务配置中设定" },
  hwnd:         { label: "目标窗口", color: "#6366f1", icon: <DesktopOutlined />,      desc: "操作的目标窗口句柄。默认 {hwnd} 为当前窗口，可填固定句柄或变量", range: "如 0x12345 或 {my_hwnd}" },
  text:         { label: "输入文本", color: "#14b8a6", icon: <EditOutlined />,          desc: "模拟键盘逐字输入到窗口。支持 {变量} 表达式", range: "如 Hello World 或 {my_text}" },
  combo:        { label: "连招配置", color: "#52c41a", icon: <CaretRightOutlined />,   desc: "在全局设置中定义的连招名称。如 连招:常规连招", range: "连招数据键名" },
  prompt:       { label: "分析提示", color: "#722ed1", icon: <EditOutlined />,          desc: "告诉 AI 如何分析截图", range: "如 '提取图中文字'" },
  title:        { label: "通知标题", color: "#fa8c16", icon: <BellOutlined />,           desc: "通知弹窗的标题文字，支持 {变量}" },
  description:  { label: "通知内容", color: "#fa8c16", icon: <EditOutlined />,           desc: "通知弹窗的正文内容，支持 {变量}" },
  type:         { label: "通知类型", color: "#fa8c16", icon: <BellOutlined />,           desc: "通知样式：success 绿 / info 蓝 / warning 黄 / error 红", range: "默认 info" },
};

// ── Action param config ──

export const ACTION_PARAMS: Record<string, string[]> = {
  touch:          ["threshold", "click_mode", "box", "pos", "x", "y", "count", "press", "pre_delay", "post_delay", "seconds", "k", "preprocess", "method", "hwnd"],
  exits:          ["threshold", "box", "preprocess", "method", "hwnd"],
  wait:           ["threshold", "box", "seconds", "dealy", "k", "preprocess", "method", "hwnd"],
  wait_disappear: ["threshold", "box", "seconds", "dealy", "k", "preprocess", "method", "hwnd"],
  exits_color:    ["color", "tolerance", "box", "hwnd"],
  touch_color:    ["color", "tolerance", "box", "pos", "click_mode", "count", "press", "pre_delay", "post_delay", "hwnd"],
  wait_color:     ["color", "tolerance", "box", "seconds", "k", "hwnd"],
  wait_color_disappear: ["color", "tolerance", "box", "seconds", "k", "hwnd"],
  key_click:      ["key", "count", "press", "pre_delay", "post_delay", "hwnd"],
  input:          ["text", "pre_delay", "post_delay", "hwnd"],
  mouse_click:    ["pos", "count", "press", "pre_delay", "post_delay", "hwnd"],
  mouse_drag:     ["start_pos", "end_pos", "x", "y", "end_x", "end_y", "duration", "count", "pre_delay", "post_delay", "hwnd"],
  set_character:  ["hwnd"],
  switch_account: ["account_name"],
  monitor_start:  ["combo"],
  monitor_stop:   [],
  ai_vision:      ["box", "prompt", "hwnd"],
  notify:         ["title", "description", "type", "duration"],
  "{True}":       [],
};

export const REQUIRED_PARAMS: Record<string, string[]> = {
  touch: ["args"],
  exits: ["args"],
  wait: ["args"],
  wait_disappear: ["args"],
  key_click: ["key"],
  input: ["text"],
  mouse_click: ["pos"],
  mouse_drag: ["start_pos", "end_pos"],
  exits_color: ["color"],
  touch_color: ["color"],
  wait_color: ["color"],
  wait_color_disappear: ["color"],
  switch_account: ["account_name"],
  monitor_start: ["combo"],
  ai_vision:     ["prompt"],
  notify:        ["title"],
};

export const PARAM_DEFAULTS: Record<string, unknown> = {
  threshold: 0.85,
  tolerance: 10,
  seconds: 1800,
  k: 1,
  click_mode: "random",
  count: 1,
  x: 0,
  y: 0,
  end_x: 0,
  end_y: 0,
  duration: 500,
  press: 0,
  pre_delay: 1500,
  post_delay: 1500,
  dealy: 500,
  method: "ccoeff",
  type: "info",
};

export const ACTIONS_WITH_TEMPLATES = new Set(["touch", "exits", "wait", "wait_disappear"]);

// ── Builtin variables ──

export const BUILTIN_VARS: { value: string; label: string }[] = [
  { value: "{result}",    label: "{result}" },
  { value: "{time}",      label: "{time}" },
  { value: "{hwnd}",      label: "{hwnd}" },
  { value: "{ChildHwnd}", label: "{ChildHwnd}" },
];

// ── Editor context ──

export interface EditorCtx {
  stepKeys: string[];
  builtinVars: { value: string; label: string }[];
  configVars: { value: string; label: string }[];
  taskValueVars: { value: string; label: string }[];
  taskSteps: { value: string; label: string }[];
  taskCommonSteps: { value: string; label: string }[];
  globalCommonSteps: { value: string; label: string }[];
  stepParamsMap: Record<string, Record<string, unknown>>;
  allStepsData: Record<string, {
    action?: string; params?: Record<string, unknown>;
    prefix?: (string | SubflowRef)[]; postfix?: (string | SubflowRef)[];
    failure_extra?: (string | SubflowRef)[]; success_extra?: (string | SubflowRef)[];
    next?: string; success?: string; failure?: string;
  }>;
  refreshKey: number;
  hwnd: string;
  taskName?: string;
  version?: string;
  values?: Record<string, unknown>;
  valueTypes?: Record<string, VarType>;
  layout?: { model?: string; store?: string }[][];
}
