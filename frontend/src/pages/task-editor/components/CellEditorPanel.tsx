import { type FC } from "react";
import { Button, Input, InputNumber, Select, Switch, Divider } from "antd";
import type { Cell, CellModel, CellOption } from "@/types/task-editor";
import MiniPreview from "@/pages/task-editor/components/mini-preview/MiniPreview";

/* ── constants ── */

const MODEL_OPTIONS: { value: CellModel; label: string }[] = [
  { value: "el-input", label: "文本" },
  { value: "el-input-number", label: "数字" },
  { value: "el-switch", label: "开关" },
  { value: "el-select", label: "下拉" },
  { value: "el-textarea", label: "多行" },
  { value: "el-checkbox", label: "勾选" },
  { value: "el-checkbox-group", label: "多选组" },
  { value: "el-radio", label: "单选组" },
  { value: "el-slider", label: "滑块" },
  { value: "el-date-picker", label: "日期" },
  { value: "el-color-picker", label: "颜色" },
];

const MODEL_COLOR: Record<string, string> = {
  "el-input": "#4b8bf4", "el-input-number": "#22b07d", "el-switch": "#f5a623",
  "el-select": "#7c5cfc", "el-textarea": "#0ea5e9", "el-checkbox": "#ef4444",
  "el-checkbox-group": "#ec4899", "el-radio": "#f97316", "el-slider": "#6366f1",
  "el-date-picker": "#14b8a6", "el-color-picker": "#a855f7",
};

const MODELS_WITH_OPTIONS = new Set<CellModel>(["el-select", "el-checkbox-group", "el-radio"]);
const MODELS_WITH_PLACEHOLDER = new Set<CellModel>([
  "el-input", "el-input-number", "el-select", "el-textarea", "el-date-picker",
]);

/* ── sub-components ── */

const Field: FC<{ label: string; children: React.ReactNode; className?: string }> = ({ label, children, className }) => (
  <div className={className}>
    <span className="text-[10px] text-muted block mb-0.5">{label}</span>
    {children}
  </div>
);

/* ── props ── */

interface CellEditorProps {
  cell: Cell;
  ri: number;
  ci: number;
  onUpdate: (ri: number, ci: number, patch: Partial<Cell>) => void;
  onUpdateStore: (ri: number, ci: number, oldStore: string | undefined, newStore: string) => void;
  onDelete: (ri: number, ci: number) => void;
  onSetOpts: (ri: number, ci: number, opts: CellOption[]) => void;
}

/* ── component ── */

const CellEditorPanel: FC<CellEditorProps> = ({ cell, ri, ci, onUpdate, onUpdateStore, onDelete, onSetOpts }) => {
  const model = cell.model ?? "el-input";
  const col = MODEL_COLOR[model] ?? "#9ca3af";

  return (
    <div className="flex flex-col gap-3">
      {/* header */}
      <div className="flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: col }} />
        <span className="text-[12px] font-semibold text-heading">
          {MODEL_OPTIONS.find((m) => m.value === model)?.label ?? model}
        </span>
        <span className="text-[10px] text-[#9ca3af]">
          行{ri + 1}·格{ci + 1}
        </span>
        <div className="flex-1" />
        <Button type="text" size="small" danger className="!text-[10px]"
          onClick={() => onDelete(ri, ci)}>删除</Button>
      </div>

      <Divider className="!my-0" />

      {/* basic */}
      <div className="grid grid-cols-2 gap-2">
        <Field label="变量绑定">
          <Input size="small" className="text-[11px]"
            value={cell.store ?? ""}
            placeholder="变量名"
            onChange={(e) => onUpdateStore(ri, ci, cell.store, e.target.value)} />
        </Field>
        <Field label="控件类型">
          <Select size="small" className="w-full"
            value={model}
            options={MODEL_OPTIONS}
            onChange={(m) => onUpdate(ri, ci, { model: m })} />
        </Field>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Field label="标签文本">
          <Input size="small" className="text-[11px]"
            value={cell.text ?? ""} placeholder="显示标签"
            onChange={(e) => onUpdate(ri, ci, { text: e.target.value || undefined })} />
        </Field>
        <Field label="列宽 (1-24)">
          <InputNumber size="small" className="w-full" min={1} max={24}
            value={cell.span ?? 1}
            onChange={(v) => onUpdate(ri, ci, { span: v ?? 1 })} />
        </Field>
      </div>

      {/* placeholder + disabled */}
      <div className="grid grid-cols-2 gap-2">
        {MODELS_WITH_PLACEHOLDER.has(model) ? (
          <Field label="占位提示">
            <Input size="small" className="text-[11px]"
              value={cell.placeholder ?? ""} placeholder="placeholder"
              onChange={(e) => onUpdate(ri, ci, { placeholder: e.target.value || undefined })} />
          </Field>
        ) : <div />}
        <Field label="禁用">
          <Switch size="small"
            checked={cell.disabled ?? false}
            onChange={(v) => onUpdate(ri, ci, { disabled: v || undefined })} />
        </Field>
      </div>

      {/* ── model-specific ── */}
      {model === "el-input" && (
        <div className="grid grid-cols-2 gap-2">
          <Field label="最大长度">
            <InputNumber size="small" className="w-full" min={0}
              value={cell.maxLength} placeholder="不限"
              onChange={(v) => onUpdate(ri, ci, { maxLength: v ?? undefined })} />
          </Field>
          <Field label="可清除">
            <Switch size="small"
              checked={cell.allowClear ?? false}
              onChange={(v) => onUpdate(ri, ci, { allowClear: v || undefined })} />
          </Field>
        </div>
      )}

      {model === "el-input-number" && (
        <div className="grid grid-cols-3 gap-2">
          <Field label="最小值">
            <InputNumber size="small" className="w-full"
              value={cell.min} placeholder="不限"
              onChange={(v) => onUpdate(ri, ci, { min: v ?? undefined })} />
          </Field>
          <Field label="最大值">
            <InputNumber size="small" className="w-full"
              value={cell.max} placeholder="不限"
              onChange={(v) => onUpdate(ri, ci, { max: v ?? undefined })} />
          </Field>
          <Field label="步长">
            <InputNumber size="small" className="w-full"
              value={cell.step} placeholder="1"
              onChange={(v) => onUpdate(ri, ci, { step: v ?? undefined })} />
          </Field>
        </div>
      )}

      {model === "el-slider" && (
        <div className="grid grid-cols-3 gap-2">
          <Field label="最小值">
            <InputNumber size="small" className="w-full"
              value={cell.min ?? 0}
              onChange={(v) => onUpdate(ri, ci, { min: v ?? 0 })} />
          </Field>
          <Field label="最大值">
            <InputNumber size="small" className="w-full"
              value={cell.max ?? 100}
              onChange={(v) => onUpdate(ri, ci, { max: v ?? 100 })} />
          </Field>
          <Field label="步长">
            <InputNumber size="small" className="w-full"
              value={cell.step ?? 1}
              onChange={(v) => onUpdate(ri, ci, { step: v ?? 1 })} />
          </Field>
        </div>
      )}

      {model === "el-textarea" && (
        <div className="grid grid-cols-2 gap-2">
          <Field label="行数">
            <InputNumber size="small" className="w-full" min={1}
              value={cell.rows ?? 4}
              onChange={(v) => onUpdate(ri, ci, { rows: v ?? 4 })} />
          </Field>
          <Field label="最大长度">
            <InputNumber size="small" className="w-full" min={0}
              value={cell.maxLength} placeholder="不限"
              onChange={(v) => onUpdate(ri, ci, { maxLength: v ?? undefined })} />
          </Field>
        </div>
      )}

      {model === "el-select" && (
        <div className="grid grid-cols-2 gap-2">
          <Field label="模式">
            <Select size="small" className="w-full"
              value={cell.mode} allowClear placeholder="单选"
              options={[{ value: "multiple", label: "多选" }, { value: "tags", label: "标签" }]}
              onChange={(v) => onUpdate(ri, ci, { mode: v || undefined })} />
          </Field>
          <Field label="可清除">
            <Switch size="small"
              checked={cell.allowClear ?? false}
              onChange={(v) => onUpdate(ri, ci, { allowClear: v || undefined })} />
          </Field>
        </div>
      )}

      {model === "el-radio" && (
        <Field label="样式">
          <Select size="small" className="w-full"
            value={cell.optionType} allowClear placeholder="默认"
            options={[{ value: "default", label: "默认" }, { value: "button", label: "按钮" }]}
            onChange={(v) => onUpdate(ri, ci, { optionType: v || undefined })} />
        </Field>
      )}

      {model === "el-date-picker" && (
        <Field label="日期格式">
          <Input size="small" className="text-[11px]"
            value={cell.format ?? ""} placeholder="YYYY-MM-DD"
            onChange={(e) => onUpdate(ri, ci, { format: e.target.value || undefined })} />
        </Field>
      )}

      {/* ── options ── */}
      {MODELS_WITH_OPTIONS.has(model) && (
        <>
          <Divider className="!my-0" />
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-medium text-secondary">选项列表</span>
              <Button type="dashed" size="small" className="text-[10px]"
                onClick={() => onSetOpts(ri, ci, [...(cell.options ?? []), { label: "", value: "" }])}>
                + 添加
              </Button>
            </div>
            <div className="flex flex-col gap-1">
              {(cell.options ?? []).map((opt, oi) => {
                const moveOpt = (from: number, to: number) => {
                  const opts = [...(cell.options ?? [])];
                  const [item] = opts.splice(from, 1);
                  opts.splice(to, 0, item);
                  onSetOpts(ri, ci, opts);
                };
                return (
                <div key={oi} className="flex items-center gap-1"
                  draggable
                  onDragStart={(e) => { e.dataTransfer.setData("text/plain", String(oi)); }}
                  onDragOver={(e) => { e.preventDefault(); }}
                  onDrop={(e) => {
                    e.preventDefault();
                    const from = Number(e.dataTransfer.getData("text/plain"));
                    if (from !== oi) moveOpt(from, oi);
                  }}
                >
                  <span className="text-[10px] text-[#c4bbb2] cursor-grab select-none shrink-0">⠿</span>
                  <Input size="small" placeholder="标签" className="flex-1 text-[11px]"
                    value={opt.label}
                    onChange={(e) => {
                      const opts = (cell.options ?? []).map((o, i) => (i === oi ? { ...o, label: e.target.value } : o));
                      onSetOpts(ri, ci, opts);
                    }} />
                  <Input size="small" placeholder="值" className="flex-1 text-[11px]"
                    value={typeof opt.value === "number" ? String(opt.value) : opt.value}
                    onChange={(e) => {
                      const opts = (cell.options ?? []).map((o, i) => (i === oi ? { ...o, value: e.target.value } : o));
                      onSetOpts(ri, ci, opts);
                    }} />
                  <Button type="text" size="small"
                    className="!text-[#d0d5dd] hover:!text-[#dc2626] shrink-0"
                    onClick={() => onSetOpts(ri, ci, (cell.options ?? []).filter((_, i) => i !== oi))}>
                    ×
                  </Button>
                </div>
                );
              })}
              {(cell.options ?? []).length === 0 && (
                <div className="text-[10px] text-[#9ca3af]">暂无选项</div>
              )}
            </div>
          </div>
        </>
      )}

      {/* preview */}
      <Divider className="!my-0" />
      <div>
        <span className="text-[10px] font-medium text-muted block mb-1.5">预览</span>
        <div className="rounded-md border border-[#e5e7eb] bg-[#fcfcfd] px-3 py-2">
          <MiniPreview cell={cell} />
        </div>
      </div>
    </div>
  );
};

export default CellEditorPanel;
