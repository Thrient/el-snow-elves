export type VariableCategory = "config" | "task" | "system" | "step";

export interface VariableItem {
  syntax: string;
  label: string;
  category: VariableCategory;
  description?: string;
}
