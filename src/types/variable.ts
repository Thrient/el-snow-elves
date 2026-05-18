export type VariableCategory = "config" | "task" | "system" | "step";

export interface VariableItem {
  syntax: string;
  label: string;
  category: VariableCategory;
  description?: string;
}

export const VARIABLE_CATEGORY_LABELS: Record<VariableCategory, string> = {
  config: "全局设置",
  task: "任务变量",
  system: "系统变量",
  step: "步骤名称",
};

export const SYSTEM_VARIABLES: VariableItem[] = [
  { syntax: "{result}", label: "{result} — 当前步骤返回值", category: "system" },
];
