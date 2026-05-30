import { useState, useMemo, type FC } from "react";
import { Button, Input, InputNumber, Select, Switch, Tooltip, Divider } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import type { Cell, CellModel, CellOption, VarType } from "@/types/task";
import MiniPreview from "@/components/mini-preview/MiniPreview";

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

const MODEL_SHORT: Record<string, string> = {
  "el-input": "Aa", "el-input-number": "#", "el-switch": "⇄", "el-select": "☰",
  "el-textarea": "¶", "el-checkbox": "☑", "el-checkbox-group": "☑☑", "el-radio": "◉",
  "el-slider": "—", "el-date-picker": "📅", "el-color-picker": "◐",
};

const MODELS_WITH_OPTIONS = new Set<CellModel>(["el-select", "el-checkbox-group", "el-radio"]);
const MODELS_WITH_PLACEHOLDER = new Set<CellModel>([
  "el-input", "el-input-number", "el-select", "el-textarea", "el-date-picker",
]);

interface Props {
  values: Record<string, unknown>;
  valueTypes?: Record<string, VarType>;
  layout: Cell[][];
  onChange: (values: Record<string, unknown>) => void;
  onValueTypesChange?: (valueTypes: Record<string, VarType>) => void;
  onLayoutChange: (layout: Cell[][]) => void;
}

type Selection = { ri: number; ci: number } | null;

/* ── sub-components ── */

const Field: FC<{ label: string; children: React.ReactNode; className?: string }> = ({ label, children, className }) => (
  <div className={className}>
    <span className="text-[10px] text-[#8b8fa3] block mb-0.5">{label}</span>
    {children}
  </div>
);


/* ── main component ── */

const TaskVarsSection: FC<Props> = ({ values, valueTypes = {}, layout, onChange, onValueTypesChange, onLayoutChange }) => {
  const [sel, setSel] = useState<Selection>(null);

  const orphanedKeys = useMemo(() => {
    const used = new Set<string>();
    for (const row of layout) for (const cell of row) if (cell.store) used.add(cell.store);
    return Object.keys(values).filter((k) => !used.has(k));
  }, [values, layout]);

  const selectedCell: Cell | undefined = sel ? layout[sel.ri]?.[sel.ci] : undefined;

  /* ── layout ops ── */

  const update = (ri: number, ci: number, patch: Partial<Cell>) => {
    onLayoutChange(layout.map((row, i) =>
      i === ri ? row.map((c, j) => (j === ci ? { ...c, ...patch } : c)) : row,
    ));
  };

  const isStoreUsedElsewhere = (ri: number, ci: number, store: string | undefined) => {
    if (!store) return false;
    for (let i = 0; i < layout.length; i++)
      for (let j = 0; j < layout[i].length; j++)
        if ((i !== ri || j !== ci) && layout[i][j].store === store) return true;
    return false;
  };

  const updateStore = (ri: number, ci: number, oldStore: string | undefined, newStore: string) => {
    const nextVals = { ...values };
    let nextTypes = { ...valueTypes };
    if (oldStore && oldStore !== newStore && !isStoreUsedElsewhere(ri, ci, oldStore)) {
      delete nextVals[oldStore];
      delete nextTypes[oldStore];
    }
    if (newStore && !(newStore in nextVals)) {
      nextVals[newStore] = "";
      nextTypes[newStore] = "text" as VarType;
    }
    onChange(nextVals);
    onValueTypesChange?.(nextTypes);
    update(ri, ci, { store: newStore || undefined });
  };

  const addRow = () => {
    const key = `var_${Date.now()}`;
    onChange({ ...values, [key]: "" });
    onValueTypesChange?.({ ...valueTypes, [key]: "text" as VarType });
    onLayoutChange([...layout, [{ span: 24, model: "el-input", text: "", store: key }]]);
    setSel({ ri: layout.length, ci: 0 });
  };

  const deleteRow = (ri: number) => {
    const nextVals = { ...values };
    const nextTypes = { ...valueTypes };
    for (const cell of layout[ri]) {
      if (cell.store && !isStoreUsedElsewhere(ri, -1, cell.store)) {
        delete nextVals[cell.store];
        delete nextTypes[cell.store];
      }
    }
    onChange(nextVals);
    onValueTypesChange?.(nextTypes);
    onLayoutChange(layout.filter((_, i) => i !== ri));
    if (sel?.ri === ri) setSel(null);
  };

  const moveRow = (ri: number, dir: -1 | 1) => {
    const t = ri + dir;
    if (t < 0 || t >= layout.length) return;
    const next = [...layout];
    [next[ri], next[t]] = [next[t], next[ri]];
    onLayoutChange(next);
    if (sel?.ri === ri) setSel({ ri: t, ci: sel.ci });
    else if (sel?.ri === t) setSel({ ri, ci: sel.ci });
  };

  const addCell = (ri: number) => {
    const key = `var_${Date.now()}`;
    const used = layout[ri].reduce((s, c) => s + (c.span ?? 24), 0);
    const span = Math.max(1, Math.min(6, 24 - used));
    onChange({ ...values, [key]: "" });
    onValueTypesChange?.({ ...valueTypes, [key]: "text" as VarType });
    onLayoutChange(layout.map((row, i) =>
      i === ri ? [...row, { span, model: "el-input" as const, text: "", store: key }] : row,
    ));
    setSel({ ri, ci: layout[ri].length });
  };

  const deleteCell = (ri: number, ci: number) => {
    const cell = layout[ri][ci];
    const nextVals = { ...values };
    const nextTypes = { ...valueTypes };
    if (cell.store && !isStoreUsedElsewhere(ri, ci, cell.store)) {
      delete nextVals[cell.store];
      delete nextTypes[cell.store];
    }
    onChange(nextVals);
    onValueTypesChange?.(nextTypes);
    const newRow = layout[ri].filter((_, j) => j !== ci);
    onLayoutChange(newRow.length === 0
      ? layout.filter((_, i) => i !== ri)
      : layout.map((row, i) => (i === ri ? newRow : row)),
    );
    setSel(null);
  };

  const adoptOrphan = (key: string) => {
    onLayoutChange([...layout, [{ span: 24, model: "el-input", text: "", store: key }]]);
    if (!(key in valueTypes)) onValueTypesChange?.({ ...valueTypes, [key]: "text" as VarType });
    setSel({ ri: layout.length, ci: 0 });
  };

  /* ── options helpers ── */
  const setOpts = (ri: number, ci: number, opts: CellOption[]) => {
    update(ri, ci, { options: opts.length > 0 ? opts : undefined });
  };

  /* ── render ── */

  const renderRow = (row: Cell[], ri: number) => {
    const totalSpan = row.reduce((s, c) => s + (c.span ?? 1), 0);
    const isOver = totalSpan > 24;

    return (
      <div key={ri} className="rounded-lg border border-[#e5e7eb] overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow">
        {/* header */}
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-[#f9fafb] border-b border-[#f3f4f6]">
          <span className="text-[10px] text-[#9ca3af] font-medium">行 {ri + 1}</span>
          <span className={`text-[9px] font-mono ${isOver ? 'text-[#ef4444]' : totalSpan === 24 ? 'text-[#22b07d]' : 'text-[#9ca3af]'}`}>
            {totalSpan}/24
          </span>
          <div className="flex-1" />
          <Tooltip title="上移"><Button type="text" size="small" disabled={ri === 0}
            className="!text-[10px] !p-0 !w-5 !h-5 !text-[#9ca3af]"
            onClick={() => moveRow(ri, -1)}>↑</Button></Tooltip>
          <Tooltip title="下移"><Button type="text" size="small" disabled={ri === layout.length - 1}
            className="!text-[10px] !p-0 !w-5 !h-5 !text-[#9ca3af]"
            onClick={() => moveRow(ri, 1)}>↓</Button></Tooltip>
          <span className="w-px h-3 bg-[#e5e7eb]" />
          <Button type="text" size="small"
            className="!text-[10px] !p-0 !w-5 !h-5 !text-[#6b7280]"
            onClick={() => addCell(ri)}>+</Button>
          <Button type="text" size="small"
            className="!text-[10px] !p-0 !w-5 !h-5 !text-[#d0d5dd] hover:!text-[#dc2626]"
            onClick={() => deleteRow(ri)}>×</Button>
        </div>

        {/* cells */}
        <div className="flex items-stretch min-h-52">
          {row.map((cell, ci) => {
            const span = cell.span ?? 1;
            const col = MODEL_COLOR[cell.model ?? "el-input"] ?? "#9ca3af";
            const isSel = sel?.ri === ri && sel?.ci === ci;

            return (
              <div key={ci} style={{ flex: span, minWidth: 0 }}
                className="border-r border-[#f3f4f6] last:border-r-0">
                <button
                  className={`w-full h-full text-left px-2.5 py-2 transition-colors cursor-pointer
                    ${isSel
                      ? 'bg-[#eef2ff] ring-1 ring-inset ring-[#b8c8ff]'
                      : 'hover:bg-[#fafbfd]'}`}
                  style={{ borderLeft: isSel ? `2px solid ${col}` : '2px solid transparent' }}
                  onClick={() => setSel(isSel ? null : { ri, ci })}
                >
                  <div className="flex items-center gap-1 mb-1">
                    <span className="inline-flex items-center justify-center w-4 h-4 rounded text-[9px] font-bold text-white shrink-0"
                      style={{ backgroundColor: col }}>
                      {MODEL_SHORT[cell.model ?? "el-input"] ?? "?"}
                    </span>
                    <span className="text-[9px] text-[#9ca3af] ml-auto">{span}</span>
                  </div>
                  <MiniPreview cell={cell} />
                  {cell.store && (
                    <div className="mt-1">
                      <code className="text-[9px] bg-[#f0f5ff] text-[#4b8bf4] px-1 py-px rounded">
                        {`{${cell.store}}`}
                      </code>
                    </div>
                  )}
                </button>
              </div>
            );
          })}
          {/* unused space */}
          {totalSpan < 24 && (
            <div style={{ flex: 24 - totalSpan }}
              className="border-l border-dashed border-[#e5e7eb] flex items-center justify-center bg-[#fcfcfd]">
              <span className="text-[9px] text-[#d0d5dd]">{24 - totalSpan}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex gap-4 min-h-320px">
      {/* ── Left: grid ── */}
      <div className="flex-1 flex flex-col gap-2 min-w-0 overflow-y-auto thin-scrollbar max-h-420px">
        {orphanedKeys.length > 0 && (
          <div className="bg-[#fffbeb] border border-[#fde68a] rounded-lg px-3 py-2 text-[10px] text-[#92400e]">
            <span className="font-semibold">未绑定布局的值：</span>
            {orphanedKeys.map((k) => (
              <span key={k} className="inline-flex items-center gap-1 ml-1.5">
                <code className="bg-[#fef3c7] px-1 rounded text-[#92400e] text-[10px]">{`{${k}}`}</code>
                <Button type="link" size="small" className="!text-[10px] !p-0 !h-auto"
                  onClick={() => adoptOrphan(k)}>创建行</Button>
              </span>
            ))}
          </div>
        )}

        {layout.length === 0 ? (
          <div className="flex-1 flex items-center justify-center text-[12px] text-[#9ca3af]">
            暂无布局 — 点击下方按钮添加第一行
          </div>
        ) : (
          layout.map((row, ri) => renderRow(row, ri))
        )}

        <Button type="dashed" size="small" block icon={<PlusOutlined />} onClick={addRow}>
          添加行
        </Button>
      </div>

      {/* ── Right: editor panel ── */}
      <div className="w-[310px] shrink-0 border-l border-[#eef0f2] pl-4 overflow-y-auto thin-scrollbar max-h-420px">
        {selectedCell ? (
          <CellEditor
            cell={selectedCell}
            ri={sel!.ri}
            ci={sel!.ci}
            onUpdate={update}
            onUpdateStore={updateStore}
            onDelete={deleteCell}
            onSetOpts={setOpts}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-[#9ca3af] text-[11px] text-center leading-relaxed">
            点击左侧单元格<br />编辑其属性
          </div>
        )}
      </div>
    </div>
  );
};

/* ── Cell editor panel ── */

interface CellEditorProps {
  cell: Cell;
  ri: number;
  ci: number;
  onUpdate: (ri: number, ci: number, patch: Partial<Cell>) => void;
  onUpdateStore: (ri: number, ci: number, oldStore: string | undefined, newStore: string) => void;
  onDelete: (ri: number, ci: number) => void;
  onSetOpts: (ri: number, ci: number, opts: CellOption[]) => void;
}

const CellEditor: FC<CellEditorProps> = ({ cell, ri, ci, onUpdate, onUpdateStore, onDelete, onSetOpts }) => {
  const model = cell.model ?? "el-input";
  const col = MODEL_COLOR[model] ?? "#9ca3af";

  return (
    <div className="flex flex-col gap-3">
      {/* header */}
      <div className="flex items-center gap-2">
        <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: col }} />
        <span className="text-[12px] font-semibold text-[#1a1a2e]">
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
              <span className="text-[10px] font-medium text-[#6b7280]">选项列表</span>
              <Button type="dashed" size="small" className="text-[10px]"
                onClick={() => onSetOpts(ri, ci, [...(cell.options ?? []), { label: "", value: "" }])}>
                + 添加
              </Button>
            </div>
            <div className="flex flex-col gap-1">
              {(cell.options ?? []).map((opt, oi) => (
                <div key={oi} className="flex items-center gap-1">
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
              ))}
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
        <span className="text-[10px] font-medium text-[#8b8fa3] block mb-1.5">预览</span>
        <div className="rounded-md border border-[#e5e7eb] bg-[#fcfcfd] px-3 py-2">
          <MiniPreview cell={cell} />
        </div>
      </div>
    </div>
  );
};

export default TaskVarsSection;
