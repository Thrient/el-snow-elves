import type { CellModel, VarType } from "@/types/task";

export type { VarType } from "@/types/task";

type ValueType = "string" | "number" | "boolean" | "list" | "empty";

/** VarType → ValueType 映射 */
const VTYPE_MAP: Record<VarType, ValueType> = {
  text: "string", number: "number", switch: "boolean", list: "list", object: "string",
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

const ALL_COMPONENT_MODELS: CellModel[] = [
  "el-input", "el-input-number", "el-switch", "el-select", "el-input-tags", "el-textarea",
  "el-checkbox", "el-checkbox-group", "el-radio", "el-slider", "el-date-picker", "el-color-picker",
];

export function compatibleModels(val: unknown, explicit?: VarType): CellModel[] {
  const t = detectValueType(val, explicit);
  if (t === "empty") return ALL_COMPONENT_MODELS;
  return COMPATIBLE[t];
}
