import {
  useState, useEffect, useCallback,
  type FC,
} from "react";
import { Button, Input, InputNumber } from "antd";
import type { Cell, CellOption, VarType } from "@/types/task";
import { MODEL_META } from "@/types/task-editor/field-config";
import { MODEL_FIELDS, OPTION_MODELS } from "@/types/task-editor/field-config";
import FieldRenderer from "./components/FieldRenderer";

/* ── sub-components ── */

const FieldLabel: FC<{ children: string }> = ({ children }) => (
  <span className="text-[11px] font-medium text-slate-500 block mb-1 select-none">{children}</span>
);

const SectionIcon: FC<{ color: string; children: React.ReactNode }> = ({ color, children }) => (
  <div className="w-6 h-6 rounded-lg flex items-center justify-center shrink-0"
    style={{ backgroundColor: `${color}14`, color }}>
    {children}
  </div>
);

/* ── main ── */

export interface ControlEditorModalProps {
  open: boolean;
  cell: Cell | null;
  ri: number;
  ci: number;
  values: Record<string, unknown>;
  valueTypes: Record<string, VarType>;
  onClose: () => void;
  onUpdateCell: (ri: number, ci: number, patch: Partial<Cell>) => void;
  onRemoveCell: (ri: number, ci: number) => void;
  onChangeControl: () => void;
  onChangeValue: (store: string, value: unknown) => void;
}

const ControlEditorModal: FC<ControlEditorModalProps> = ({
  open, cell, ri, ci, values,
  onClose, onUpdateCell, onRemoveCell, onChangeControl, onChangeValue,
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (open && cell) {
      const t = requestAnimationFrame(() => setVisible(true));
      return () => cancelAnimationFrame(t);
    }
    setVisible(false);
  }, [open, cell]);

  const handleClose = useCallback(() => {
    setVisible(false);
    setTimeout(onClose, 200);
  }, [onClose]);

  if (!open || !cell) return null;

  const meta = MODEL_META[cell.model ?? "el-input"] ?? MODEL_META["el-input"];
  const store = cell.store ?? "";
  const fields = MODEL_FIELDS[cell.model ?? "el-input"] ?? [];

  /* ── field renderer ── */

  const renderField = (field: string) => (
    <FieldRenderer field={field} cell={cell} ri={ri} ci={ci} onUpdateCell={onUpdateCell} />
  );

  /* ── animation helpers ── */

  const animStyle = (delay: number): React.CSSProperties => ({
    opacity: visible ? 1 : 0,
    transform: visible ? "translateY(0) scale(1)" : "translateY(16px) scale(0.97)",
    transition: `all 0.35s cubic-bezier(0.16, 1, 0.3, 1) ${delay}s`,
  });

  /* ── card wrapper ── */

  const cardStyle: React.CSSProperties = {
    background: "linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(248,250,252,0.95) 100%)",
    border: "1px solid rgba(226,232,240,0.8)",
    boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)",
    borderRadius: 16,
    padding: 20,
  };

  return (
    <div
      className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl overflow-hidden"
      style={{
        background: visible ? "rgba(15,23,42,0.25)" : "rgba(15,23,42,0)",
        backdropFilter: visible ? "blur(4px)" : "blur(0px)",
        transition: "all 0.3s ease-out",
      }}
      onClick={handleClose}
    >
      {/* modal panel */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-[520px] overflow-y-auto flex flex-col"
        style={{
          maxHeight: "min(78vh, 540px)",
          opacity: visible ? 1 : 0,
          transform: visible ? "translateY(0) scale(1)" : "translateY(32px) scale(0.94)",
          transition: "all 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
          background: "linear-gradient(180deg, #ffffff 0%, #fafbfc 100%)",
          borderRadius: 24,
          boxShadow: [
            "0 0 0 1px rgba(0,0,0,0.04)",
            "0 25px 60px rgba(0,0,0,0.12)",
            "0 10px 24px rgba(0,0,0,0.08)",
            "0 0 0 1px rgba(0,0,0,0.02) inset",
          ].join(", "),
        }}
      >
        {/* decorative top accent line */}
        <div
          className="absolute top-0 left-8 right-8 h-[3px] rounded-b-full opacity-70"
          style={{ background: `linear-gradient(90deg, transparent, ${meta.color}60, ${meta.color}, ${meta.color}60, transparent)` }}
        />

        {/* ═══ HEADER ═══ */}
        <div className="relative shrink-0 px-6 pt-7 pb-5" style={animStyle(0.04)}>
          <div className="flex items-start gap-3.5">
            {/* control type icon */}
            <div
              className="w-11 h-11 rounded-2xl flex items-center justify-center text-base font-bold shrink-0 shadow-sm"
              style={{
                background: `linear-gradient(135deg, ${meta.bg} 0%, ${meta.bg}cc 100%)`,
                color: meta.color,
                boxShadow: `0 4px 12px ${meta.color}20, 0 1px 3px rgba(0,0,0,0.06), inset 0 1px 0 rgba(255,255,255,0.8)`,
              }}
            >
              {meta.short}
            </div>

            <div className="flex flex-col gap-0.5 min-w-0 flex-1 pt-0.5">
              <div className="flex items-center gap-2">
                <span
                  className="text-[11px] font-bold px-2 py-0.5 rounded-lg tracking-wide"
                  style={{ background: meta.bg, color: meta.color }}
                >
                  {meta.label}
                </span>
                {store && (
                  <code className="text-[11px] font-semibold text-indigo-600 truncate bg-indigo-50/80 px-2 py-0.5 rounded-lg">
                    {`{${store}}`}
                  </code>
                )}
              </div>
              <span className="text-[11px] text-slate-400 mt-0.5 font-medium">
                行 {ri + 1} · 位置 {ci + 1} · {cell.span ?? 12} 列宽
              </span>
            </div>

            {/* close button */}
            <button
              className="w-8 h-8 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-400 hover:text-slate-600
                flex items-center justify-center transition-all duration-200 shrink-0"
              onClick={handleClose}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>
        </div>

        {/* ═══ SCROLLABLE BODY ═══ */}
        <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4 thin-scrollbar" style={animStyle(0.08)}>
          {/* ── Basic Info Card ── */}
          <section style={cardStyle}>
            <div className="flex items-center gap-2.5 mb-4">
              <SectionIcon color={meta.color}>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <circle cx="6" cy="6" r="4.5" stroke="currentColor" strokeWidth="1.5" />
                  <circle cx="6" cy="6" r="1.8" fill="currentColor" />
                </svg>
              </SectionIcon>
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">基本信息</span>
            </div>
            <div className="grid grid-cols-4 gap-3">
              <div>
                <FieldLabel>变量名</FieldLabel>
                <Input size="small" className="!rounded-xl !text-xs" value={store} readOnly />
              </div>
              <div>
                <FieldLabel>宽度 (1-24)</FieldLabel>
                <InputNumber size="small" className="w-full !rounded-xl" min={1} max={24}
                  value={cell.span ?? 12}
                  onChange={(v) => onUpdateCell(ri, ci, { span: v ?? 12 })} />
              </div>
              <div>
                <FieldLabel>默认值</FieldLabel>
                <Input size="small" className="!rounded-xl !text-xs"
                  value={store ? (typeof values[store] === "string" ? values[store] as string : JSON.stringify(values[store])) : ""}
                  onChange={(e) => {
                    if (!store) return;
                    onChangeValue(store, e.target.value);
                  }} />
              </div>
              <div className="flex items-end pb-0.5">
                <Button size="small" className="!rounded-xl !text-xs !w-full"
                  onClick={onChangeControl}>
                  更换控件
                </Button>
              </div>
            </div>
          </section>

          {/* ── Properties Card ── */}
          {fields.length > 0 && (
            <section style={cardStyle}>
              <div className="flex items-center gap-2.5 mb-4">
                <SectionIcon color={meta.color}>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <rect x="0.5" y="0.5" width="4.5" height="4.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
                    <rect x="7" y="0.5" width="4.5" height="4.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
                    <rect x="0.5" y="7" width="4.5" height="4.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
                    <rect x="7" y="7" width="4.5" height="4.5" rx="1" stroke="currentColor" strokeWidth="1.3" />
                  </svg>
                </SectionIcon>
                <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">属性配置</span>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {fields.map((f) => renderField(f))}
              </div>
            </section>
          )}

          {/* ── Options Card ── */}
          {OPTION_MODELS.has(cell.model ?? "el-input") && (
            <section style={cardStyle}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2.5">
                  <SectionIcon color={meta.color}>
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <rect x="1" y="1" width="10" height="10" rx="2.5" stroke="currentColor" strokeWidth="1.3" />
                      <path d="M3.5 6l2 2L8.5 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </SectionIcon>
                  <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">选项列表</span>
                  <span className="text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full font-medium">
                    {(cell.options ?? []).length}
                  </span>
                </div>
                <Button type="dashed" size="small" className="!text-[11px] !rounded-xl"
                  onClick={() => {
                    const opts = [...(cell.options ?? []), { label: "", value: "" }];
                    onUpdateCell(ri, ci, { options: opts });
                  }}>
                  + 添加选项
                </Button>
              </div>

              <div className="flex flex-col gap-2 max-h-[150px] overflow-y-auto thin-scrollbar">
                {(cell.options ?? []).length === 0 && (
                  <div className="text-[11px] text-slate-400 py-5 text-center bg-slate-50 rounded-xl flex flex-col items-center gap-1.5">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="opacity-25">
                      <path d="M10 5v5M10 15h.01" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      <rect x="3" y="3" width="14" height="14" rx="4" stroke="currentColor" strokeWidth="1.5" />
                    </svg>
                    暂无选项，点击上方按钮添加
                  </div>
                )}
                {(cell.options ?? []).map((opt: CellOption, oi: number) => (
                  <div key={oi} className="flex items-center gap-2 bg-slate-50 p-2.5 rounded-xl group">
                    <span className="text-[10px] text-slate-400 font-mono font-semibold shrink-0 w-5 text-right">{oi + 1}</span>
                    <Input size="small" placeholder="标签" className="flex-1 !text-xs !rounded-xl"
                      value={opt.label}
                      onChange={(e) => {
                        const opts = (cell.options ?? []).map((o, i) => i === oi ? { ...o, label: e.target.value } : o);
                        onUpdateCell(ri, ci, { options: opts });
                      }} />
                    <Input size="small" placeholder="值" className="flex-1 !text-xs !rounded-xl"
                      value={typeof opt.value === "number" ? String(opt.value) : opt.value}
                      onChange={(e) => {
                        const opts = (cell.options ?? []).map((o, i) => i === oi ? { ...o, value: e.target.value } : o);
                        onUpdateCell(ri, ci, { options: opts });
                      }} />
                    <button
                      className="w-6 h-6 rounded-lg bg-white hover:bg-rose-100 text-slate-300 hover:text-rose-500
                        flex items-center justify-center text-sm transition-all duration-200 shrink-0 shadow-sm
                        opacity-0 group-hover:opacity-100"
                      onClick={() => {
                        onUpdateCell(ri, ci, { options: (cell.options ?? []).filter((_, i) => i !== oi) });
                      }}
                    >
                      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                        <path d="M1 1l8 8M9 1L1 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* ═══ FOOTER ═══ */}
        <div
          className="relative shrink-0 px-6 py-4 flex items-center gap-3"
          style={{
            ...animStyle(0.12),
            background: "linear-gradient(180deg, rgba(250,251,252,0) 0%, rgba(248,250,252,0.9) 30%, #f8fafc 100%)",
            borderTop: "1px solid rgba(226,232,240,0.6)",
          }}
        >
          <button
            className="text-[12px] font-medium px-4 py-2 rounded-xl bg-white hover:bg-rose-50 text-slate-500 hover:text-rose-500
              border border-slate-200 hover:border-rose-200 transition-all duration-200 flex items-center gap-1.5 shadow-sm"
            onClick={() => { onRemoveCell(ri, ci); handleClose(); }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M3 3.5l6 6M9 3.5l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            删除控件
          </button>
          <div className="flex-1" />
          <button
            className="text-[12px] font-medium px-4 py-2 rounded-xl text-slate-500 hover:text-slate-700
              hover:bg-slate-100 transition-all duration-200"
            onClick={handleClose}
          >
            取消
          </button>
          <button
            className="text-[12px] font-semibold px-5 py-2 rounded-xl transition-all duration-200 flex items-center gap-1.5 shadow-sm"
            style={{
              background: `linear-gradient(135deg, ${meta.color}ee, ${meta.color}dd)`,
              color: "#fff",
              boxShadow: `0 2px 8px ${meta.color}30, 0 1px 3px rgba(0,0,0,0.1)`,
            }}
            onClick={handleClose}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M2 6.5l2.5 2.5L10 3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            完成
          </button>
        </div>
      </div>
    </div>
  );
};

export default ControlEditorModal;
