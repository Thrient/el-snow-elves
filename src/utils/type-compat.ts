import type { CellModel, VarType } from "@/types/task";

export type { VarType } from "@/types/task";

export type ValueType = "string" | "number" | "boolean" | "list" | "empty";

/** 用户可见的类型元数据 */
export const VAR_TYPE_META: Record<VarType, { label: string; desc: string; icon: string }> = {
  text:   { label: "文本", desc: "适合文字、名称、编号等任意文本内容", icon: "Aa" },
  number: { label: "数字", desc: "适合计数、坐标、阈值等需要计算的数值", icon: "12" },
  switch: { label: "开关", desc: "只有真/假两种状态，适合开关、条件判断", icon: "⇄" },
  list:   { label: "列表", desc: "一组值的有序集合，适合遍历、多选等场景", icon: "[ ]" },
};

export const VAR_TYPE_OPTS: { value: VarType; label: string; desc: string }[] =
  Object.entries(VAR_TYPE_META).map(([value, { label, desc }]) => ({ value: value as VarType, label, desc }));

/** VarType → ValueType 映射 */
const VTYPE_MAP: Record<VarType, ValueType> = {
  text: "string", number: "number", switch: "boolean", list: "list",
};

/** 检测值的运行时类型（无显式类型时回退） */
export function detectValueType(val: unknown, explicit?: VarType): ValueType {
  if (explicit && explicit in VTYPE_MAP) return VTYPE_MAP[explicit];
  if (val === null || val === undefined || val === "") return "empty";
  if (Array.isArray(val)) return "list";
  if (typeof val === "number") return "number";
  if (typeof val === "boolean") return "boolean";
  if (typeof val === "string") {
    if (/^-?\d+(\.\d+)?$/.test(val.trim())) return "number";
    if (val.trim().toLowerCase() === "true" || val.trim().toLowerCase() === "false") return "boolean";
    return "string";
  }
  return "string";
}

/** 根据显式类型获取兼容的布局控件 */
const COMPATIBLE: Record<ValueType, CellModel[]> = {
  string:  ["el-input", "el-textarea", "el-select", "el-input-tags", "el-date-picker", "el-color-picker", "el-radio", "el-checkbox-group"],
  number:  ["el-input-number", "el-slider", "el-select", "el-radio"],
  boolean: ["el-switch", "el-checkbox"],
  list:    ["el-input-tags", "el-checkbox-group", "el-select"],
  empty:   [],
};

export const ALL_COMPONENT_MODELS: CellModel[] = [
  "el-input", "el-input-number", "el-switch", "el-select", "el-input-tags", "el-textarea",
  "el-checkbox", "el-checkbox-group", "el-radio", "el-slider", "el-date-picker", "el-color-picker",
];

export function compatibleModels(val: unknown, explicit?: VarType): CellModel[] {
  const t = detectValueType(val, explicit);
  if (t === "empty") return ALL_COMPONENT_MODELS;
  return COMPATIBLE[t];
}
