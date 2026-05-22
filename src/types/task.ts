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
  | 'el-autocomplete-subflow'

export type CellOption = {
  label: string
  value: string | number
}

export type AutocompleteContext = {
  taskName?: string
  version?: string
  taskId?: string
  steps?: string[]
  common?: string[]
  variables?: string[]
}

export type Cell = {
  span: number
  model: CellModel
  text?: string
  store?: string
  // Common
  disabled?: boolean
  placeholder?: string
  size?: 'large' | 'middle' | 'small'
  // InputNumber / Slider
  min?: number
  max?: number
  step?: number
  precision?: number
  controls?: boolean
  readOnly?: boolean
  // Select / CheckboxGroup / Radio
  options?: CellOption[]
  allowClear?: boolean
  mode?: 'multiple' | 'tags'
  showSearch?: boolean
  maxTagCount?: number
  // Switch / Select
  loading?: boolean
  // Input / TextArea
  maxLength?: number
  showCount?: boolean
  rows?: number
  autoSize?: boolean | { minRows: number; maxRows: number }
  // Checkbox
  indeterminate?: boolean
  // Radio
  optionType?: 'default' | 'button'
  buttonStyle?: 'outline' | 'solid'
  // Slider
  dots?: boolean
  marks?: Record<number, string>
  range?: boolean
  vertical?: boolean
  included?: boolean
  // DatePicker
  format?: string
  picker?: 'date' | 'week' | 'month' | 'quarter' | 'year'
  showTime?: boolean
  // ColorPicker
  showText?: boolean
  // Autocomplete
  autocompleteContext?: AutocompleteContext
}

export type VarType = "text" | "number" | "switch" | "list"

export type TaskBase = {
  id: string
  name: string
  version: string
  values: Record<string, unknown>
  /** 变量类型 — 用户创建变量时手动指定，优于自动推断 */
  valueTypes?: Record<string, VarType>
  debugStart?: string
  debugSingle?: boolean
}

export type Task = TaskBase & {
  description: string
  author: string
  layout: Cell[][]
}

// --- Full task types (with steps/common/monitors/start) ---

export interface SubflowRef {
  step: string
  args?: Record<string, unknown>
  when?: string
}

export interface StepRetry {
  times: number
  interval: number
}

export interface Step {
  action?: string
  description?: string
  params?: Record<string, unknown>
  prefix?: (string | SubflowRef)[]
  postfix?: (string | SubflowRef)[]
  failure_extra?: (string | SubflowRef)[]
  success_extra?: (string | SubflowRef)[]
  success?: string
  failure?: string
  next?: string
  extends?: string
  retry?: StepRetry
  set?: { name: string; value: unknown }[]
}

export interface MonitorConfig {
  loop?: string[]
  interval?: number
}

export interface FullTask extends Task {
  start: string
  steps: Record<string, Step>
  common: Record<string, Step>
  monitors: MonitorConfig
}

export interface Suggestion {
  label: string
  value: string
  type: 'action' | 'template' | 'step' | 'variable' | 'subflow'
  description?: string
}
