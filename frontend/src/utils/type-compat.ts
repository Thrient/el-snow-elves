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

/**
 * 将字符串输入值转换为目标 VarType。
 * 列表用 JSON.parse，数字用 Number()，布尔用字符串比较，
 * 转换失败时回退到原始字符串。
 */
export function coerceValue(raw: string, type: VarType): unknown {
  if (raw === "" || raw === "null") {
    return type === "list" ? [] : type === "number" ? null : "";
  }
  switch (type) {
    case "number": {
      const n = Number(raw);
      return isNaN(n) ? raw : n;
    }
    case "switch":
      return raw === "true" || raw === "1";
    default:
      return raw;
  }
}

/**
 * 将值转换为适合在 Input 中显示的字符串。
 */
export function formatValue(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}
