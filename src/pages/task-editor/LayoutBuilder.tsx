import {
  useState, useCallback, useMemo,
  type FC, type DragEvent as ReactDragEvent,
} from "react";
import { Button, Input, Modal, message } from "antd";
import type { Cell, CellModel, VarType } from "@/types/task";
import { VAR_TYPE_OPTS, compatibleModels } from "@/utils/type-compat";
import MiniPreview from "@/components/mini-preview/MiniPreview";
import ComponentPickerModal from "./ComponentPickerModal";
import ControlEditorModal from "./ControlEditorModal";

/* ── helpers ── */

function cloneLayout(l: Cell[][]): Cell[][] {
  return l.map((r) => r.map((c) => ({ ...c })));
}

function usedStores(layout: Cell[][]): Set<string> {
  const s = new Set<string>();
  for (const r of layout) for (const c of r) if (c.store) s.add(c.store);
  return s;
}

function rowUsedSpan(row: Cell[]): number {
  return row.reduce((s, c) => s + (c.span ?? 1), 0);
}

/* ── model display metadata ── */

const MODEL_META: Record<string, { label: string; short: string; color: string; bg: string }> = {
  "el-input":        { label: "文本输入", short: "Aa", color: "#6366f1", bg: "#eef2ff" },
  "el-input-number": { label: "数字输入", short: "12", color: "#10b981", bg: "#ecfdf5" },
  "el-switch":       { label: "开关",     short: "⇄",  color: "#f59e0b", bg: "#fffbeb" },
  "el-select":       { label: "下拉选择", short: "☰",  color: "#8b5cf6", bg: "#f5f3ff" },
  "el-textarea":     { label: "多行文本", short: "¶",  color: "#06b6d4", bg: "#ecfeff" },
  "el-checkbox":     { label: "复选框",   short: "☑",  color: "#ef4444", bg: "#fef2f2" },
  "el-checkbox-group":{ label: "多选组",  short: "☑☑",color: "#ec4899", bg: "#fdf2f8" },
  "el-radio":        { label: "单选组",   short: "◉",  color: "#f97316", bg: "#fff7ed" },
  "el-slider":       { label: "滑块",     short: "—",  color: "#6366f1", bg: "#eef2ff" },
  "el-date-picker":  { label: "日期选择", short: "📅", color: "#14b8a6", bg: "#f0fdfa" },
  "el-color-picker": { label: "颜色选择", short: "◐",  color: "#a855f7", bg: "#faf5ff" },
  "el-input-tags":  { label: "标签输入", short: "#",  color: "#0891b2", bg: "#ecfeff" },
};

const DEFAULT_CELL_SPAN = 12;

/* ── props ── */

export interface LayoutBuilderProps {
  initialLayout?: Cell[][];
  initialValues?: Record<string, unknown>;
  initialValueTypes?: Record<string, VarType>;
  onConfirm?: (layout: Cell[][], values: Record<string, unknown>, valueTypes: Record<string, VarType>) => void;
  onCancel?: () => void;
}

/* ── main ── */

const LayoutBuilder: FC<LayoutBuilderProps> = ({ initialLayout = [], initialValues = {}, initialValueTypes = {}, onConfirm, onCancel }) => {
  const [layout, setLayout] = useState<Cell[][]>(() => cloneLayout(initialLayout));
  const [values, setValues] = useState<Record<string, unknown>>({ ...initialValues });
  const [valueTypes, setValueTypes] = useState<Record<string, VarType>>({ ...initialValueTypes });

  // selection
  const [sel, setSel] = useState<{ ri: number; ci: number } | null>(null);
  const selCell = sel ? layout[sel.ri]?.[sel.ci] ?? null : null;

  // picker state
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pendingVar, setPendingVar] = useState<{ name: string; value: unknown; type: VarType; ri: number; ci: number } | null>(null);

  // drag state
  const [dragFromLeft, setDragFromLeft] = useState<{ key: string } | null>(null);

  // context menu state
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; ri: number; ci: number } | null>(null);
  const [leftCtxMenu, setLeftCtxMenu] = useState<{ x: number; y: number } | null>(null);

  // create variable modal
  const [createVarOpen, setCreateVarOpen] = useState(false);
  const [newVarName, setNewVarName] = useState("");
  const [newVarValue, setNewVarValue] = useState("");
  const [newVarType, setNewVarType] = useState<VarType>("text");

  /* ── computed ── */

  const unboundVars = useMemo(() => {
    const used = usedStores(layout);
    return Object.entries(values)
      .filter(([k]) => !used.has(k))
      .map(([k, v]) => ({ key: k, value: v, type: valueTypes[k] ?? "text" as const }));
  }, [values, layout, valueTypes]);

  /* ── layout ops ── */

  const addCell = useCallback((ri: number, ci: number, store: string, model: CellModel) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      const cell: Cell = { span: DEFAULT_CELL_SPAN, model, store };
      if (!next[ri]) {
        next.push([cell]);
      } else {
        next[ri].splice(ci, 0, cell);
      }
      return next;
    });
  }, []);

  const updateCell = useCallback((ri: number, ci: number, patch: Partial<Cell>) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      if (next[ri]) next[ri][ci] = { ...next[ri][ci], ...patch };
      return next;
    });
  }, []);

  const removeCell = useCallback((ri: number, ci: number) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      next[ri] = next[ri].filter((_, j) => j !== ci);
      return next.filter((r) => r.length > 0);
    });
    setSel(null);
    setCtxMenu(null);
  }, []);

  const moveCell = useCallback((fromRi: number, fromCi: number, toRi: number, toCi: number) => {
    setLayout((prev) => {
      const next = cloneLayout(prev);
      const cell = next[fromRi]?.[fromCi];
      if (!cell) return prev;
      next[fromRi].splice(fromCi, 1);
      if (next[fromRi].length === 0) next.splice(fromRi, 1);
      // Adjust target indices after removal
      let adjRi = toRi;
      let adjCi = toCi;
      if (fromRi === toRi && fromCi < toCi) adjCi = toCi - 1;
      if (fromRi < toRi) adjRi = toRi - 1;
      if (!next[adjRi]) next[adjRi] = [];
      next[adjRi].splice(adjCi, 0, cell);
      return next;
    });
    setSel({ ri: toRi, ci: toCi });
  }, []);

  const addRow = useCallback(() => {
    setLayout((prev) => [...cloneLayout(prev), []]);
  }, []);

  const deleteRow = useCallback((ri: number) => {
    setLayout((prev) => cloneLayout(prev).filter((_, i) => i !== ri));
    if (sel?.ri === ri) setSel(null);
  }, [sel]);

  /* ── picker callback ── */

  const handlePickerSelect = useCallback((model: CellModel) => {
    if (pendingVar) {
      addCell(pendingVar.ri, pendingVar.ci, pendingVar.name, model);
    }
    setPickerOpen(false);
    setPendingVar(null);
  }, [pendingVar, addCell]);

  /* ── drop handler (left → right) ── */

  const handleDrop = useCallback((ri: number, ci: number, e: ReactDragEvent) => {
    e.preventDefault();
    const key = e.dataTransfer.getData("text/plain");
    if (!key) return;
    const val = values[key];
    if (val === undefined) return;
    setPendingVar({ name: key, value: val, type: valueTypes[key] ?? "text", ri, ci });
    setPickerOpen(true);
  }, [values, valueTypes]);

  const handleDragOverRow = useCallback((ri: number, e: ReactDragEvent) => {
    e.preventDefault();
    const row = layout[ri];
    const used = row ? rowUsedSpan(row) : 0;
    const remaining = 24 - used;
    if (remaining >= DEFAULT_CELL_SPAN) {
      e.dataTransfer.dropEffect = "move";
    } else {
      e.dataTransfer.dropEffect = "none";
    }
  }, [layout]);

  /* ── cell drag (within grid) ── */

  const handleCellDragStart = useCallback((ri: number, ci: number, e: ReactDragEvent) => {
    e.dataTransfer.setData("application/layout-move", JSON.stringify({ ri, ci }));
    e.dataTransfer.effectAllowed = "move";
  }, []);

  const handleCellDrop = useCallback((toRi: number, toCi: number, e: ReactDragEvent) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData("application/layout-move");
    if (!raw) return;
    const { ri: fromRi, ci: fromCi } = JSON.parse(raw);
    if (fromRi === toRi && fromCi === toCi) return;
    moveCell(fromRi, fromCi, toRi, toCi);
  }, [moveCell]);

  /* ── confirm ── */

  const deleteVar = useCallback((key: string) => {
    setValues((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setValueTypes((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    // 同步清理 layout 中引用该变量的 cell
    setLayout((prev) => cloneLayout(prev).map((row) =>
      row.filter((cell) => cell.store !== key),
    ).filter((row) => row.length > 0));
  }, []);

  const handleCreateVar = useCallback(() => {
    if (!newVarName.trim()) {
      message.warning("变量名不能为空");
      return;
    }
    if (newVarName in values) {
      message.warning("变量名已存在");
      return;
    }
    const key = newVarName.trim();
    setValues((prev) => ({ ...prev, [key]: newVarValue }));
    setValueTypes((prev) => ({ ...prev, [key]: newVarType }));
    setCreateVarOpen(false);
    setNewVarName("");
    setNewVarValue("");
    setNewVarType("text");
    message.success(`变量 {${key}} 已创建`);
  }, [newVarName, newVarValue, newVarType, values]);

  const handleConfirm = () => {
    const final = cloneLayout(layout).filter((r) => r.length > 0);
    const used = usedStores(final);
    const finalVals: Record<string, unknown> = {};
    for (const k of used) finalVals[k] = values[k] ?? "";
    // also include unbound variables
    for (const [k, v] of Object.entries(values)) {
      if (!(k in finalVals)) finalVals[k] = v ?? "";
    }
    // Clean up valueTypes for deleted vars
    const finalTypes: Record<string, VarType> = {};
    for (const k of Object.keys(finalVals)) {
      finalTypes[k] = valueTypes[k] ?? "text";
    }
    onConfirm?.(final, finalVals, finalTypes);
  };

  /* ═══════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════ */

  return (
    <div className="flex gap-4 select-none" style={{ minHeight: 480, maxHeight: "calc(100vh - 200px)" }}>

      {/* ═══ LEFT: 待布局变量 ═══ */}
      <div
        className="w-[210px] shrink-0 bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-100 flex flex-col overflow-hidden shadow-md"
        onContextMenu={(e) => {
          e.preventDefault();
          setLeftCtxMenu({ x: e.clientX, y: e.clientY });
        }}
      >
        <div className="px-4 py-3.5 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-400 shadow-sm shadow-amber-200" />
            <span className="text-xs font-semibold text-slate-700">待布局</span>
            <span className="text-[10px] text-slate-400 ml-auto bg-slate-100 px-2 py-0.5 rounded-full font-medium">
              {unboundVars.length}
            </span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2.5 flex flex-col gap-1.5 thin-scrollbar">
          {unboundVars.length === 0 && Object.keys(values).length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-[11px] text-slate-300 text-center px-2">
              <div className="w-10 h-10 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-300 text-lg mb-1">∅</div>
              <span className="font-medium text-slate-400">暂无变量</span>
              <span className="text-[10px] text-slate-300">右键创建</span>
            </div>
          ) : unboundVars.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-[11px] text-slate-300 text-center px-2 gap-2">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-400 text-lg mb-1">✓</div>
              <span>所有变量已布局</span>
            </div>
          ) : (
            unboundVars.map(({ key, value, type }) => {
              const meta = VAR_TYPE_OPTS.find((o) => o.value === type);
              const typeIcon = type === "number" ? "12" : type === "bool" ? "⇄" : type === "list" ? "[ ]" : "Aa";
              const typeColor = type === "number" ? "#10b981" : type === "bool" ? "#f59e0b" : type === "list" ? "#ec4899" : "#6366f1";
              const valStr = value === null || value === undefined ? "" : String(value);

              return (
                <div
                  key={key}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/plain", key);
                    e.dataTransfer.effectAllowed = "move";
                    setDragFromLeft({ key });
                  }}
                  onDragEnd={() => setDragFromLeft(null)}
                  className="flex flex-col gap-1 px-3 py-2.5 rounded-xl border border-slate-100
                    bg-white hover:border-indigo-200 hover:shadow-md hover:-translate-y-0.5 cursor-grab active:cursor-grabbing
                    transition-all duration-200 group"
                >
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold text-white shadow-sm"
                      style={{ backgroundColor: typeColor }}>
                      {typeIcon}
                    </span>
                    <code className="text-[11px] font-semibold text-slate-700 truncate">{key}</code>
                    <button
                      className="w-5 h-5 rounded-md bg-white hover:bg-rose-100 text-slate-300 hover:text-rose-400 flex items-center justify-center text-xs ml-auto opacity-0 group-hover:opacity-100 transition-all shrink-0"
                      onClick={(e) => { e.stopPropagation(); deleteVar(key); }}
                      title="删除变量"
                    >×</button>
                  </div>
                  {valStr && (
                    <span className="text-[10px] text-slate-400 truncate pl-8 pr-1">{valStr}</span>
                  )}
                </div>
              );
            })
          )}
        </div>
        <div className="px-3 py-2.5 border-t border-slate-100 bg-gradient-to-r from-slate-50 to-white">
          <span className="text-[10px] text-slate-400 flex items-center gap-1.5">
            <span className="inline-block w-1 h-1 rounded-full bg-indigo-300" />
            拖入右侧布局区即可添加
          </span>
        </div>
      </div>

      {/* ═══ RIGHT: 布局画布 ═══ */}
      <div className="relative flex-1 bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-100 flex flex-col overflow-hidden shadow-lg">
        {/* toolbar */}
        <div className="flex items-center gap-3 px-5 py-3 border-b border-slate-100 bg-gradient-to-r from-slate-50 to-white shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-indigo-400 shadow-sm shadow-indigo-200" />
            <span className="text-xs font-bold text-slate-700">布局画布</span>
          </div>
          <span className="text-[10px] text-slate-400 font-medium bg-slate-100 px-2 py-0.5 rounded-full">
            {layout.reduce((s, r) => s + r.length, 0)} 控件 · {layout.length} 行
          </span>
          <div className="flex-1" />
          <Button size="small" onClick={addRow} className="!text-[11px] !rounded-xl !shadow-sm">+ 添加行</Button>
        </div>

        {/* grid area */}
        <div
          className="flex-1 overflow-y-auto p-5 bg-[radial-gradient(ellipse_at_top,rgba(248,250,252,0.8),rgba(241,245,249,0.4))] thin-scrollbar"
          onClick={() => { setSel(null); setCtxMenu(null); }}
          onContextMenu={(e) => { e.preventDefault(); setCtxMenu(null); }}
        >
          {layout.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-400">
              <div className="w-20 h-20 rounded-3xl bg-white shadow-md border border-slate-100 flex items-center justify-center">
                <span className="text-3xl text-slate-300">⊞</span>
              </div>
              <div className="flex flex-col items-center gap-1">
                <span className="text-sm font-medium text-slate-500">空白布局</span>
                <span className="text-xs text-slate-400">从左侧拖拽变量到此处开始构建布局</span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {layout.map((row, ri) => {
                const totalSpan = rowUsedSpan(row);
                const remaining = 24 - totalSpan;
                const canDrop = remaining >= DEFAULT_CELL_SPAN;

                return (
                  <div
                    key={ri}
                    className={`rounded-2xl border-2 transition-all duration-300 bg-white/80 backdrop-blur-sm
                      ${canDrop && dragFromLeft ? "border-indigo-300 ring-4 ring-indigo-100/60 shadow-lg" : "border-slate-100 shadow-sm hover:shadow-md"}`}
                    onDragOver={(e) => handleDragOverRow(ri, e)}
                    onDrop={(e) => handleDrop(ri, row.length, e)}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {/* row header */}
                    <div className="flex items-center gap-2 px-3 py-2 rounded-t-[14px] bg-gradient-to-r from-slate-50 to-white border-b border-slate-100">
                      <span className="w-6 h-6 rounded-lg bg-slate-100 text-[10px] font-bold text-slate-500 flex items-center justify-center shadow-sm">
                        {ri + 1}
                      </span>
                      <span className={`text-[10px] font-mono font-semibold ${totalSpan === 24 ? "text-emerald-500" : totalSpan > 24 ? "text-rose-400" : "text-slate-400"}`}>
                        {totalSpan}/24
                      </span>
                      {totalSpan > 24 && <span className="text-[9px] font-medium text-rose-400 bg-rose-50 px-1.5 py-0.5 rounded-full">溢出</span>}
                      {!canDrop && remaining > 0 && (
                        <span className="text-[9px] font-medium text-amber-500 bg-amber-50 px-1.5 py-0.5 rounded-full">不足</span>
                      )}
                      <div className="flex-1" />
                      <button className="w-5 h-5 rounded-full bg-slate-100 hover:bg-rose-100 text-slate-300 hover:text-rose-400 flex items-center justify-center text-xs transition-all duration-200"
                        onClick={(e) => { e.stopPropagation(); deleteRow(ri); }}>
                        ×
                      </button>
                    </div>

                    {/* cells row */}
                    <div
                      className="relative flex items-stretch gap-2 px-2 pb-2"
                      style={{ display: "grid", gridTemplateColumns: "repeat(24, 1fr)", minHeight: 72 }}
                    >
                      {row.map((cell, ci) => {
                        const span = cell.span ?? 1;
                        const meta = MODEL_META[cell.model ?? "el-input"] ?? MODEL_META["el-input"];
                        const isSel = sel?.ri === ri && sel?.ci === ci;

                        return (
                          <div
                            key={ci}
                            draggable
                            onDragStart={(e) => handleCellDragStart(ri, ci, e)}
                            onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                            onDrop={(e) => handleCellDrop(ri, ci, e)}
                            onContextMenu={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              setCtxMenu({ x: e.clientX, y: e.clientY, ri, ci });
                              setSel({ ri, ci });
                            }}
                            onClick={(e) => { e.stopPropagation(); setSel({ ri, ci }); }}
                            className={`relative rounded-xl border-2 transition-all duration-200 cursor-pointer
                              flex flex-col justify-center px-3 py-2.5 min-w-0 overflow-hidden group
                              ${isSel
                                ? "border-indigo-400 shadow-lg shadow-indigo-200/40 -translate-y-0.5 z-10"
                                : "border-transparent hover:border-slate-200 hover:shadow-md hover:-translate-y-0.5"}`}
                            style={{
                              gridColumn: `span ${span}`,
                              background: isSel
                                ? `linear-gradient(135deg, ${meta.bg} 0%, #ffffff 100%)`
                                : `linear-gradient(135deg, ${meta.bg} 0%, rgba(255,255,255,0.6) 100%)`,
                            }}
                          >
                            <div className="absolute left-0 top-2 bottom-2 w-[4px] rounded-r-full" style={{ backgroundColor: meta.color, opacity: isSel ? 1 : 0.7 }} />
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <span
                                className="text-[9px] font-bold px-1.5 py-0.5 rounded-md text-white shadow-sm"
                                style={{ backgroundColor: meta.color }}
                              >
                                {meta.label}
                              </span>
                              {cell.store && (
                                <code className="text-[10px] font-semibold text-indigo-600 truncate bg-indigo-50/80 px-1.5 py-0.5 rounded-md">{`{${cell.store}}`}</code>
                              )}
                              <span className="text-[9px] text-slate-400 ml-auto font-mono shrink-0 bg-slate-100 px-1.5 py-0.5 rounded-md">{span}c</span>
                            </div>
                            <div className="flex justify-center scale-[0.92] pointer-events-none opacity-70 group-hover:opacity-100 transition-opacity duration-200">
                              <MiniPreview cell={cell} />
                            </div>
                            {isSel && (
                              <button
                                className="absolute top-2 right-2 w-5 h-5 rounded-full bg-rose-50
                                  hover:bg-rose-500 text-rose-400 hover:text-white flex items-center justify-center
                                  text-[11px] transition-all duration-200 shadow-sm hover:shadow-md"
                                onClick={(e) => { e.stopPropagation(); removeCell(ri, ci); }}
                              >
                                ×
                              </button>
                            )}
                          </div>
                        );
                      })}

                      {/* remaining space / drop zone */}
                      {remaining > 0 && (
                        <div
                          className={`rounded-xl flex items-center justify-center transition-all duration-300 mx-1
                            ${canDrop && dragFromLeft
                              ? "border-2 border-dashed border-indigo-300 bg-indigo-50/40 text-indigo-400 shadow-inner shadow-indigo-100/50"
                              : "border-2 border-dashed border-slate-150 bg-slate-50/50 text-slate-300"}`}
                          style={{ gridColumn: `span ${remaining}`, minHeight: 64 }}
                          onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                          onDrop={(e) => handleDrop(ri, row.length, e)}
                        >
                          <span className={`text-[11px] font-medium text-center px-2 py-1 rounded-full transition-all duration-200 ${canDrop && dragFromLeft ? "bg-indigo-100/80 text-indigo-500" : ""}`}>
                            {canDrop ? "拖入此处" : `仅 ${remaining} 列可用`}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Control Editor Popup ── */}
        <ControlEditorModal
          open={!!selCell}
          cell={selCell}
          ri={sel?.ri ?? 0}
          ci={sel?.ci ?? 0}
          values={values}
          valueTypes={valueTypes}
          onClose={() => setSel(null)}
          onUpdateCell={updateCell}
          onRemoveCell={removeCell}
          onChangeControl={() => {
            if (!selCell) return;
            setPendingVar({ name: selCell.store ?? "", value: values[selCell.store ?? ""] ?? "", type: valueTypes[selCell.store ?? ""] ?? "text", ri: sel!.ri, ci: sel!.ci! });
            setPickerOpen(true);
          }}
          onChangeValue={(store, value) => {
            setValues((prev) => ({ ...prev, [store]: value }));
          }}
        />

        {/* bottom bar */}
        <div className="flex items-center gap-3 px-5 py-3 border-t border-slate-100 bg-gradient-to-r from-slate-50 to-white shrink-0">
          <div className="flex-1" />
          <Button size="small" onClick={onCancel} className="!rounded-xl">取消</Button>
          <Button type="primary" size="small" onClick={handleConfirm} className="!rounded-xl !shadow-md !shadow-indigo-200">保存布局</Button>
        </div>
      </div>

      {/* ═══ ComponentPickerModal ═══ */}
      <ComponentPickerModal
        open={pickerOpen}
        varName={pendingVar?.name ?? ""}
        varValue={pendingVar?.value ?? ""}
        varType={pendingVar?.type}
        onSelect={handlePickerSelect}
        onCancel={() => { setPickerOpen(false); setPendingVar(null); }}
      />

      {/* ═══ Context Menu (right-click on cell) ═══ */}
      {ctxMenu && (
        <div
          className="fixed inset-0 z-40 animate-fadeIn"
          style={{ background: "rgba(0,0,0,0.03)", backdropFilter: "blur(1px)" }}
          onClick={() => setCtxMenu(null)}
          onContextMenu={(e) => { e.preventDefault(); setCtxMenu(null); }}
        >
          <div
            className="absolute z-50 bg-white/95 backdrop-blur-xl rounded-2xl py-1.5 min-w-[180px] border border-slate-200/80 shadow-[0_20px_60px_rgba(0,0,0,0.12),0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden"
            style={{ left: ctxMenu.x, top: ctxMenu.y }}
          >
            <div className="px-4 py-1.5 text-[10px] font-semibold text-slate-400 tracking-wider uppercase select-none">调整宽度</div>
            <div className="grid grid-cols-4 gap-1 px-2 pb-1">
              {[6, 8, 12, 24].map((w) => (
                <div
                  key={w}
                  className="flex flex-col items-center gap-0.5 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 transition-all duration-150 cursor-pointer select-none"
                  onClick={() => {
                    updateCell(ctxMenu.ri, ctxMenu.ci, { span: w });
                    setCtxMenu(null);
                  }}
                >
                  <span className="text-sm font-bold">{w}</span>
                  <span className="text-[9px] opacity-50">列</span>
                </div>
              ))}
            </div>
            <div className="h-px bg-slate-100 mx-3 my-1" />
            <div
              className="w-full text-left px-4 py-2 text-[12px] text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 transition-colors duration-150 cursor-pointer flex items-center gap-3 select-none"
              onClick={() => {
                const cell = layout[ctxMenu.ri]?.[ctxMenu.ci];
                setPendingVar({ name: cell?.store ?? "", value: values[cell?.store ?? ""] ?? "", ri: ctxMenu.ri, ci: ctxMenu.ci });
                setPickerOpen(true);
                setCtxMenu(null);
              }}
            >
              <span className="w-6 h-6 rounded-lg bg-indigo-100 text-indigo-500 flex items-center justify-center text-xs shrink-0">⇄</span>
              更换控件
            </div>
            <div className="h-px bg-slate-100 mx-3 my-1" />
            <div
              className="w-full text-left px-4 py-2 text-[12px] text-rose-500 hover:bg-rose-50 transition-colors duration-150 cursor-pointer flex items-center gap-3 select-none"
              onClick={() => removeCell(ctxMenu.ri, ctxMenu.ci)}
            >
              <span className="w-6 h-6 rounded-lg bg-rose-100 text-rose-400 flex items-center justify-center text-xs shrink-0">×</span>
              移除
            </div>
          </div>
        </div>
      )}

      {/* ═══ Left Context Menu (right-click on unbound panel) ═══ */}
      {leftCtxMenu && (
        <div
          className="fixed inset-0 z-40 animate-fadeIn"
          style={{ background: "rgba(0,0,0,0.03)", backdropFilter: "blur(1px)" }}
          onClick={() => setLeftCtxMenu(null)}
          onContextMenu={(e) => { e.preventDefault(); setLeftCtxMenu(null); }}
        >
          <div
            className="absolute z-50 bg-white/95 backdrop-blur-xl rounded-2xl py-2 min-w-[170px] border border-slate-200/80 shadow-[0_20px_60px_rgba(0,0,0,0.12),0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden"
            style={{ left: leftCtxMenu.x, top: leftCtxMenu.y }}
          >
            <div className="px-4 py-1 text-[10px] font-semibold text-slate-400 tracking-wider uppercase select-none mb-0.5">变量操作</div>
            <div
              className="w-full text-left px-4 py-2.5 text-[12px] text-slate-700 hover:bg-indigo-50 transition-colors duration-150 cursor-pointer flex items-center gap-3 select-none"
              onClick={() => {
                setLeftCtxMenu(null);
                setCreateVarOpen(true);
              }}
            >
              <span className="w-7 h-7 rounded-xl bg-indigo-100 text-indigo-500 flex items-center justify-center text-base font-bold shrink-0 shadow-sm">+</span>
              <div className="flex flex-col gap-0.5">
                <span className="font-medium leading-tight">创建变量</span>
                <span className="text-[10px] text-slate-400 leading-tight">添加一个新的任务变量</span>
              </div>
            </div>
            <div className="h-px bg-slate-100 mx-3 my-1" />
            <div
              className="w-full text-left px-4 py-2.5 text-[12px] text-rose-500 hover:bg-rose-50 transition-colors duration-150 cursor-pointer flex items-center gap-3 select-none"
              onClick={() => {
                setLeftCtxMenu(null);
                const toDelete = unboundVars.map((v) => v.key);
                if (toDelete.length > 0) {
                  Modal.confirm({
                    title: "确认删除",
                    content: `确定要删除所有 ${toDelete.length} 个未布局变量吗？此操作不可撤销。`,
                    okText: "删除",
                    cancelText: "取消",
                    okButtonProps: { danger: true },
                    onOk: () => { for (const k of toDelete) deleteVar(k); },
                  });
                }
              }}
            >
              <span className="w-7 h-7 rounded-xl bg-rose-100 text-rose-400 flex items-center justify-center text-sm shrink-0 shadow-sm">×</span>
              <div className="flex flex-col gap-0.5">
                <span className="font-medium leading-tight">删除全部未布局变量</span>
                <span className="text-[10px] text-slate-400 leading-tight">清空所有未使用的变量</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ Create Variable Modal ═══ */}
      <Modal
        title={null}
        open={createVarOpen}
        onOk={handleCreateVar}
        onCancel={() => { setCreateVarOpen(false); setNewVarName(""); setNewVarValue(""); setNewVarType("text"); }}
        okText="创建变量"
        cancelText="取消"
        width={460}
        destroyOnClose
        okButtonProps={{ className: "!rounded-xl !shadow-md !shadow-indigo-200" }}
        cancelButtonProps={{ className: "!rounded-xl" }}
      >
        <div className="flex flex-col gap-5">
          {/* header */}
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center shrink-0 shadow-sm">
              <span className="text-indigo-500 text-lg font-bold">+</span>
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">创建变量</h3>
              <p className="text-[11px] text-slate-400">创建一个新的任务变量，后续可拖入布局</p>
            </div>
          </div>

          {/* name input */}
          <div>
            <span className="text-[11px] font-semibold text-slate-600 block mb-2">
              变量名 <span className="text-rose-400">*</span>
            </span>
            <Input
              size="middle"
              placeholder="输入变量名，例如 my_var"
              value={newVarName}
              onChange={(e) => setNewVarName(e.target.value)}
              onPressEnter={handleCreateVar}
              autoFocus
              prefix={<code className="text-[11px] text-slate-400">{`{`}</code>}
              suffix={<code className="text-[11px] text-slate-400">{`}`}</code>}
              className="!rounded-xl"
            />
          </div>

          {/* type selector */}
          <div>
            <span className="text-[11px] font-semibold text-slate-600 block mb-2">变量类型</span>
            <div className="grid grid-cols-2 gap-2">
              {VAR_TYPE_OPTS.map((o) => {
                const active = newVarType === o.value;
                const colors: Record<string, string> = {
                  text: "#6366f1", number: "#10b981", bool: "#f59e0b", list: "#ec4899",
                };
                const color = colors[o.value] ?? "#6366f1";
                return (
                  <button
                    key={o.value}
                    type="button"
                    onClick={() => setNewVarType(o.value)}
                    className={`text-left p-3 rounded-xl border-2 transition-all duration-150 ${
                      active
                        ? "border-current shadow-sm"
                        : "border-slate-100 hover:border-slate-200 hover:bg-slate-50"
                    }`}
                    style={active ? { borderColor: color, backgroundColor: `${color}08` } : undefined}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold text-white shrink-0"
                        style={{ backgroundColor: color }}
                      >
                        {o.value === "text" ? "Aa" : o.value === "number" ? "12" : o.value === "bool" ? "⇄" : "[ ]"}
                      </span>
                      <span className="text-xs font-semibold text-slate-700">{o.label}</span>
                      {active && (
                        <span className="w-4 h-4 rounded-full flex items-center justify-center ml-auto shrink-0" style={{ backgroundColor: color }}>
                          <span className="text-[8px] text-white font-bold">✓</span>
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400 leading-relaxed">{o.desc}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* value input */}
          <div>
            <span className="text-[11px] font-semibold text-slate-600 block mb-2">
              默认值 <span className="text-[10px] text-slate-400 font-normal">— 可选，留空则为空</span>
            </span>
            <Input
              size="middle"
              placeholder="例如 hello、123、true、[1,2,3]"
              value={newVarValue}
              onChange={(e) => setNewVarValue(e.target.value)}
              onPressEnter={handleCreateVar}
              className="!rounded-xl"
            />
          </div>

          {/* preview */}
          {newVarName.trim() && (
            <div className="rounded-2xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white px-5 py-4 shadow-sm">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">预览</span>
              <div className="flex items-center gap-2 flex-wrap">
                <code className="text-xs font-mono font-semibold bg-indigo-50 text-indigo-600 px-2.5 py-1.5 rounded-xl shadow-sm">
                  {`{${newVarName.trim()}}`}
                </code>
                {newVarValue && (
                  <>
                    <span className="text-[10px] text-slate-300">=</span>
                    <span className="text-xs text-slate-600 font-mono font-medium">{newVarValue}</span>
                  </>
                )}
              </div>
              <div className="mt-3 text-[10px] text-slate-400 flex items-center gap-1.5">
                <span className="inline-block w-1 h-1 rounded-full bg-slate-300" />
                类型：{VAR_TYPE_OPTS.find((o) => o.value === newVarType)?.label ?? newVarType}
                <span className="text-[10px] text-slate-300 ml-1">— {VAR_TYPE_OPTS.find((o) => o.value === newVarType)?.desc ?? ""}</span>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default LayoutBuilder;