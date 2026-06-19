import type { VariableItem, VariableCategory } from "./index";
import type { VarType } from "@/types/task-editor";

export const VARIABLE_CATEGORY_LABELS: Record<VariableCategory, string> = {
  config: "全局设置",
  task: "任务变量",
  system: "系统变量",
  step: "步骤名称",
};

export const SYSTEM_VARIABLES: VariableItem[] = [
  { syntax: "{result}", label: "{result} — 当前步骤返回值", category: "system" },
];

/** 用户可见的类型元数据 */
export const VAR_TYPE_META: Record<VarType, { label: string; desc: string; icon: string }> = {
  text:   { label: "文本", desc: "适合文字、名称、编号等任意文本内容", icon: "Aa" },
  number: { label: "数字", desc: "适合计数、坐标、阈值等需要计算的数值", icon: "12" },
  switch: { label: "开关", desc: "只有真/假两种状态，适合开关、条件判断", icon: "⇄" },
  list:   { label: "列表", desc: "一组值的有序集合，适合遍历、多选等场景", icon: "[ ]" },
  object: { label: "对象", desc: "键值对结构，支持 {变量.属性} 访问嵌套字段", icon: "{ }" },
};

export const VAR_TYPE_OPTS: { value: VarType; label: string; desc: string }[] =
  Object.entries(VAR_TYPE_META).map(([value, { label, desc }]) => ({ value: value as VarType, label, desc }));
