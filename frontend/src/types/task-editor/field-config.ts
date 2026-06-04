import type { CellModel } from "./index";

export const OPTION_MODELS = new Set<CellModel>(["el-select", "el-checkbox-group", "el-radio"]);

export const MODEL_FIELDS: Record<string, string[]> = {
  "el-input":         ["text","placeholder","disabled","maxLength","allowClear"],
  "el-input-number":  ["text","placeholder","disabled","min","max","step"],
  "el-select":        ["text","placeholder","disabled","mode","allowClear"],
  "el-textarea":      ["text","placeholder","disabled","rows","maxLength"],
  "el-slider":        ["text","disabled","min","max","step"],
  "el-switch":        ["text","disabled"],
  "el-checkbox":      ["text","disabled"],
  "el-checkbox-group":["text","disabled"],
  "el-radio":         ["text","disabled","optionType"],
  "el-date-picker":   ["text","placeholder","disabled","format"],
  "el-color-picker":  ["text","disabled"],
  "el-input-tags":    ["text","placeholder","disabled","allowClear"],
};

export const MODEL_META: Record<string, { label: string; short: string; color: string; bg: string }> = {
  "el-input":         { label: "文本输入", short: "Aa", color: "#6366f1", bg: "#eef2ff" },
  "el-input-number":  { label: "数字输入", short: "12", color: "#10b981", bg: "#ecfdf5" },
  "el-switch":        { label: "开关",     short: "⇄",  color: "#f59e0b", bg: "#fffbeb" },
  "el-select":        { label: "下拉选择", short: "☰",  color: "#8b5cf6", bg: "#f5f3ff" },
  "el-textarea":      { label: "多行文本", short: "¶",  color: "#06b6d4", bg: "#ecfeff" },
  "el-checkbox":      { label: "复选框",   short: "☑",  color: "#ef4444", bg: "#fef2f2" },
  "el-checkbox-group":{ label: "多选组",   short: "☑☑", color: "#ec4899", bg: "#fdf2f8" },
  "el-radio":         { label: "单选组",   short: "◉",  color: "#f97316", bg: "#fff7ed" },
  "el-slider":        { label: "滑块",     short: "—",  color: "#6366f1", bg: "#eef2ff" },
  "el-date-picker":   { label: "日期选择", short: "📅", color: "#14b8a6", bg: "#f0fdfa" },
  "el-color-picker":  { label: "颜色选择", short: "◐",  color: "#a855f7", bg: "#faf5ff" },
  "el-input-tags":    { label: "标签输入", short: "#",  color: "#0891b2", bg: "#ecfeff" },
};

export const DEFAULT_CELL_SPAN = 12;
