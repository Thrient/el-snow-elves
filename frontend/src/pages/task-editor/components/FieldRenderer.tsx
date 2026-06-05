import type { FC } from "react";
import { Input, InputNumber, Select, Switch } from "antd";
import type { Cell } from "@/types/task-editor";

interface FieldRendererProps {
  field: string;
  cell: Cell;
  ri: number;
  ci: number;
  onUpdateCell: (ri: number, ci: number, patch: Partial<Cell>) => void;
}

const FieldLabel: FC<{ children: string }> = ({ children }) => (
  <span className="text-[11px] font-medium text-slate-500 block mb-1 select-none">{children}</span>
);

const baseInputCls = "!text-xs !rounded-xl";

const FieldRenderer: FC<FieldRendererProps> = ({ field, cell, ri, ci, onUpdateCell }) => {
  const val = (cell as unknown as Record<string, unknown>)[field];
  const set = (v: unknown) => onUpdateCell(ri, ci, { [field]: v === undefined || v === "" || v === false ? undefined : v });

  switch (field) {
    case "text":
      return (
        <div key="text">
          <FieldLabel>标签</FieldLabel>
          <Input size="small" className={baseInputCls} value={(val as string) ?? ""} placeholder="控件标签"
            onChange={(e) => set(e.target.value || undefined)} />
        </div>
      );
    case "placeholder":
      return (
        <div key="ph">
          <FieldLabel>占位提示</FieldLabel>
          <Input size="small" className={baseInputCls} value={(val as string) ?? ""} placeholder="placeholder"
            onChange={(e) => set(e.target.value || undefined)} />
        </div>
      );
    case "disabled":
      return (
        <div key="dis">
          <FieldLabel>禁用</FieldLabel>
          <div className="pt-0.5"><Switch size="small" checked={(val as boolean) ?? false} onChange={set as (v: boolean) => void} /></div>
        </div>
      );
    case "min":
      return (
        <div key="min">
          <FieldLabel>最小值</FieldLabel>
          <InputNumber size="small" className={`w-full ${baseInputCls}`}
            value={(val as number) ?? undefined} placeholder="不限" onChange={(v) => set(v ?? undefined)} />
        </div>
      );
    case "max":
      return (
        <div key="max">
          <FieldLabel>最大值</FieldLabel>
          <InputNumber size="small" className={`w-full ${baseInputCls}`}
            value={(val as number) ?? undefined} placeholder="不限" onChange={(v) => set(v ?? undefined)} />
        </div>
      );
    case "step":
      return (
        <div key="step">
          <FieldLabel>步长</FieldLabel>
          <InputNumber size="small" className={`w-full ${baseInputCls}`}
            value={(val as number) ?? undefined} placeholder="1" onChange={(v) => set(v ?? undefined)} />
        </div>
      );
    case "rows":
      return (
        <div key="rows">
          <FieldLabel>行数</FieldLabel>
          <InputNumber size="small" className={`w-full ${baseInputCls}`} min={1} value={(val as number) ?? 4}
            onChange={(v) => onUpdateCell(ri, ci, { rows: v ?? 4 })} />
        </div>
      );
    case "allowClear":
      return (
        <div key="ac">
          <FieldLabel>可清除</FieldLabel>
          <div className="pt-0.5"><Switch size="small" checked={(val as boolean) ?? false} onChange={set as (v: boolean) => void} /></div>
        </div>
      );
    case "maxLength":
      return (
        <div key="ml">
          <FieldLabel>最大长度</FieldLabel>
          <InputNumber size="small" className={`w-full ${baseInputCls}`} min={0} value={val as number} placeholder="不限"
            onChange={(v) => set(v ?? undefined)} />
        </div>
      );
    case "mode":
      return (
        <div key="mode">
          <FieldLabel>多选</FieldLabel>
          <div className="pt-0.5">
            <Switch size="small" checked={(val as string) === "multiple"}
              onChange={(v) => set(v ? "multiple" : undefined)} />
          </div>
        </div>
      );
    case "optionType":
      return (
        <div key="ot">
          <FieldLabel>样式</FieldLabel>
          <Select size="small" className="w-full" value={val as string} allowClear placeholder="默认"
            options={[{ value: "default", label: "默认" }, { value: "button", label: "按钮" }]}
            onChange={(v) => set(v || undefined)} />
        </div>
      );
    case "format":
      return (
        <div key="fmt">
          <FieldLabel>日期格式</FieldLabel>
          <Input size="small" className={baseInputCls} value={(val as string) ?? ""} placeholder="YYYY-MM-DD"
            onChange={(e) => set(e.target.value || undefined)} />
        </div>
      );
    default:
      return null;
  }
};

export default FieldRenderer;
