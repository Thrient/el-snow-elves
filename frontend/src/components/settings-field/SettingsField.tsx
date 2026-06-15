import type { FC } from "react";
import {
  Checkbox,
  ColorPicker,
  DatePicker,
  Input,
  InputNumber,
  Radio,
  Select,
  Slider,
  Switch,
} from "antd";
import dayjs from "dayjs";
import type { Cell } from "@/types/task";
import AutocompleteInput from "@/pages/task-editor/components/autocomplete-input/AutocompleteInput";
import KeyInput from "./components/KeyInput";
import ComboEditor from "./components/ComboEditor";

interface Props {
  cell: Cell
  value: unknown
  onChange: (value: unknown) => void
  labelWidth?: number
}

const SettingsField: FC<Props> = ({ cell, value, onChange, labelWidth }) => {
  const label = cell.text && (
    <span
      className="text-sm text-[#4a423b] whitespace-nowrap shrink-0 overflow-hidden text-ellipsis inline-block font-semibold text-right"
      style={{ width: labelWidth ?? 64 }}
      title={cell.text}
    >
      {cell.text}：
    </span>
  );

  switch (cell.model) {
    case "el-text":
      return <span className="text-sm text-[#333]">{cell.text}</span>;

    case "el-switch":
      return (
        <div className="flex items-center gap-2">
          {label}
          <Switch
            checked={!!value}
            disabled={cell.disabled}
            loading={cell.loading}
            size={cell.size === 'large' || cell.size === 'middle' ? 'default' : cell.size}
            onChange={onChange}
          />
        </div>
      );

    case "el-input-number":
      return (
        <div className="flex items-center gap-2">
          {label}
          <InputNumber
            className="flex-1"
            value={value as number}
            min={cell.min}
            max={cell.max}
            step={cell.step}
            precision={cell.precision}
            disabled={cell.disabled}
            placeholder={cell.placeholder}
            readOnly={cell.readOnly}
            controls={cell.controls}
            size={cell.size}
            onChange={(v) => onChange(v)}
          />
        </div>
      );

    case "el-input":
      return (
        <div className="flex items-center gap-2">
          {label}
          <Input
            className="flex-1"
            value={value as string}
            placeholder={cell.placeholder}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
            maxLength={cell.maxLength}
            showCount={cell.showCount}
            size={cell.size}
            readOnly={cell.readOnly}
            onChange={(e) => onChange(e.target.value)}
          />
        </div>
      );

    case "el-textarea":
      return (
        <div className="flex items-start gap-2">
          {label}
          <Input.TextArea
            className="flex-1"
            value={value as string}
            placeholder={cell.placeholder}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
            maxLength={cell.maxLength}
            showCount={cell.showCount}
            rows={cell.rows}
            autoSize={cell.autoSize}
            onChange={(e) => onChange(e.target.value)}
          />
        </div>
      );

    case "el-checkbox":
      return (
        <div className="flex items-center gap-2">
          <Checkbox
            checked={!!value}
            disabled={cell.disabled}
            indeterminate={cell.indeterminate}
            onChange={(e) => onChange(e.target.checked)}
          >
            {cell.text}
          </Checkbox>
        </div>
      );

    case "el-checkbox-group":
      return (
        <div className="flex items-center gap-2">
          {label}
          <Checkbox.Group
            className="flex-1"
            value={value as (string | number)[]}
            options={cell.options}
            disabled={cell.disabled}
            onChange={(v) => onChange(v)}
          />
        </div>
      );

    case "el-radio":
      return (
        <div className="flex flex-col gap-1">
          {label}
          <Radio.Group
            className="flex-1"
            value={value as string | number}
            options={cell.options}
            disabled={cell.disabled}
            optionType={cell.optionType}
            buttonStyle={cell.buttonStyle}
            size={cell.size}
            onChange={(e) => onChange(e.target.value)}
          />
        </div>
      );

    case "el-select": {
      const selectValue: unknown = (cell.mode === "multiple")
        ? (Array.isArray(value) ? value : (value !== undefined && value !== null && value !== "" ? [value] : []))
        : value;
      return (
        <div className="flex items-center gap-2">
          {label}
          <Select
            className="flex-1"
            value={selectValue as string | number | (string | number)[]}
            options={cell.options}
            allowClear={cell.allowClear}
            placeholder={cell.placeholder}
            disabled={cell.disabled}
            mode={cell.mode}
            showSearch={cell.showSearch}
            loading={cell.loading}
            size={cell.size}
            maxTagCount={cell.maxTagCount}
            onChange={(v) => onChange(v)}
          />
        </div>
      );
    }
    case "el-input-tags": {
      // Always tags mode — value is always array
      const tagsValue: string[] = Array.isArray(value)
        ? value
        : (value !== undefined && value !== null && value !== "" ? [String(value)] : []);
      return (
        <div className="flex items-center gap-2">
          {label}
          <Select
            className="flex-1"
            mode="tags"
            value={tagsValue}
            placeholder={cell.placeholder ?? "输入后按回车添加标签"}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
            size={cell.size}
            maxTagCount={cell.maxTagCount}
            onChange={(v) => onChange(v)}
          />
        </div>
      );
    }

    case "el-slider":
      if (cell.range) {
        return (
          <div className="flex items-center gap-2">
            {label}
            <Slider
              className="flex-1"
              range
              value={value as [number, number]}
              min={cell.min}
              max={cell.max}
              step={cell.step}
              disabled={cell.disabled}
              dots={cell.dots}
              marks={cell.marks}
              vertical={cell.vertical}
              included={cell.included}
              onChange={(v) => onChange(v)}
            />
          </div>
        );
      }
      return (
        <div className="flex items-center gap-2">
          {label}
          <Slider
            className="flex-1"
            value={value as number}
            min={cell.min}
            max={cell.max}
            step={cell.step}
            disabled={cell.disabled}
            dots={cell.dots}
            marks={cell.marks}
            vertical={cell.vertical}
            included={cell.included}
            onChange={(v: number) => onChange(v)}
          />
        </div>
      );

    case "el-date-picker":
      return (
        <div className="flex items-center gap-2">
          {label}
          <DatePicker
            className="flex-1"
            value={value ? dayjs(value as string) : null}
            format={cell.format}
            picker={cell.picker}
            showTime={cell.showTime}
            placeholder={cell.placeholder}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
            size={cell.size}
            onChange={(_, dateString) => onChange(dateString)}
          />
        </div>
      );

    case "el-color-picker":
      return (
        <div className="flex items-center gap-2">
          {label}
          <ColorPicker
            value={value as string}
            format={cell.format as 'hex' | 'rgb' | 'hsb'}
            showText={cell.showText}
            allowClear={cell.allowClear}
            disabled={cell.disabled}
            size={cell.size}
            onChange={(_, hex) => onChange(hex)}
          />
        </div>
      );

    case "el-key-input":
      return (
        <div className="flex items-center gap-2">
          {label}
          <KeyInput
            value={value as string}
            onChange={(v) => onChange(v)}
          />
        </div>
      );

    case "el-autocomplete-action":
      return (
        <div className="flex items-center gap-2">
          {label}
          <AutocompleteInput
            type="action"
            value={value as string}
            onChange={onChange}
            placeholder={cell.placeholder ?? "选择或输入 action"}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
          />
        </div>
      );

    case "el-autocomplete-template":
      return (
        <div className="flex items-center gap-2">
          {label}
          <AutocompleteInput
            type="template"
            value={value as string}
            onChange={onChange}
            context={cell.autocompleteContext}
            placeholder={cell.placeholder ?? "选择或输入模板图片名"}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
          />
        </div>
      );

    case "el-autocomplete-step":
      return (
        <div className="flex items-center gap-2">
          {label}
          <AutocompleteInput
            type="step"
            value={value as string}
            onChange={onChange}
            context={cell.autocompleteContext}
            placeholder={cell.placeholder ?? "选择或输入步骤名"}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
          />
        </div>
      );

    case "el-autocomplete-variable":
      return (
        <div className="flex items-center gap-2">
          {label}
          <AutocompleteInput
            type="variable"
            value={value as string}
            onChange={onChange}
            context={cell.autocompleteContext}
            placeholder={cell.placeholder ?? "选择或输入变量"}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
          />
        </div>
      );

    case "el-autocomplete-subflow":
      return (
        <div className="flex items-center gap-2">
          {label}
          <AutocompleteInput
            type="subflow"
            value={value as string}
            onChange={onChange}
            context={cell.autocompleteContext}
            placeholder={cell.placeholder ?? "选择或输入子流程名"}
            disabled={cell.disabled}
            allowClear={cell.allowClear}
          />
        </div>
      );

    case "el-combo-editor":
      return (
        <div className="flex flex-col gap-1 w-full">
          {label && <span className="text-sm font-bold text-heading">{cell.text}</span>}
          <ComboEditor
            value={value as never}
            onChange={(v) => onChange(v)}
          />
        </div>
      );

    default:
      return <span className="text-xs text-[#999]">未知: {cell.model}</span>;
  }
};

export default SettingsField;
