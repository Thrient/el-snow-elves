export type CellModel =
  | 'el-text'
  | 'el-switch'
  | 'el-input-number'
  | 'el-key-input'
  | 'el-select'
  | 'el-input'
  | 'el-textarea'
  | 'el-checkbox'
  | 'el-checkbox-group'
  | 'el-radio'
  | 'el-slider'
  | 'el-date-picker'
  | 'el-color-picker'
  | 'el-input-tags'
  | 'el-autocomplete-action'
  | 'el-autocomplete-template'
  | 'el-autocomplete-step'
  | 'el-autocomplete-variable'
  | 'el-autocomplete-subflow';

export interface CellOption {
  label: string;
  value: string | number;
}

export interface AutocompleteContext {
  taskName?: string;
  version?: string;
  taskId?: string;
  steps?: string[];
  common?: string[];
  variables?: string[];
}

export interface Cell {
  span: number;
  model: CellModel;
  text?: string;
  store?: string;
  disabled?: boolean;
  placeholder?: string;
  size?: 'large' | 'middle' | 'small';
  min?: number;
  max?: number;
  step?: number;
  precision?: number;
  controls?: boolean;
  readOnly?: boolean;
  options?: CellOption[];
  allowClear?: boolean;
  mode?: 'multiple' | 'tags';
  showSearch?: boolean;
  maxTagCount?: number;
  loading?: boolean;
  maxLength?: number;
  showCount?: boolean;
  rows?: number;
  autoSize?: boolean | { minRows: number; maxRows: number };
  indeterminate?: boolean;
  optionType?: 'default' | 'button';
  buttonStyle?: 'outline' | 'solid';
  dots?: boolean;
  marks?: Record<number, string>;
  range?: boolean;
  vertical?: boolean;
  included?: boolean;
  format?: string;
  picker?: 'date' | 'week' | 'month' | 'quarter' | 'year';
  showTime?: boolean;
  showText?: boolean;
  autocompleteContext?: AutocompleteContext;
}

export type VarType = "text" | "number" | "switch" | "list";

export interface TaskBase {
  id: string;
  name: string;
  version: string;
  values: Record<string, unknown>;
  valueTypes?: Record<string, VarType>;
  debugStart?: string;
  debugSingle?: boolean;
}

export interface Task extends TaskBase {
  description: string;
  author: string;
  layout: Cell[][];
}

export interface SubflowRef {
  step: string;
  args?: Record<string, unknown>;
  when?: string;
}

export interface StepRetry {
  times: number;
  interval: number;
}

export interface Step {
  action?: string;
  description?: string;
  params?: Record<string, unknown>;
  prefix?: (string | SubflowRef)[];
  postfix?: (string | SubflowRef)[];
  failure_extra?: (string | SubflowRef)[];
  success_extra?: (string | SubflowRef)[];
  success?: string;
  failure?: string;
  next?: string;
  extends?: string;
  retry?: StepRetry;
  set?: { name: string; value: unknown }[];
}

export interface MonitorConfig {
  loop?: string[];
  interval?: number;
}

export interface FullTask extends Task {
  start: string;
  steps: Record<string, Step>;
  common: Record<string, Step>;
  monitors: MonitorConfig;
}

export interface Suggestion {
  label: string;
  value: string;
  type: 'action' | 'template' | 'step' | 'variable' | 'subflow';
  description?: string;
}
