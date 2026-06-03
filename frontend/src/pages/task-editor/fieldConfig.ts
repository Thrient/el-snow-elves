import type { CellModel } from "@/types/task";

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
