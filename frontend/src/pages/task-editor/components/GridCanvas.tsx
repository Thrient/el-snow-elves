import {
  useState, useMemo, useCallback,
  type FC, type DragEvent as ReactDragEvent,
} from "react";
import { Button } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import MiniPreview from "@/pages/task-editor/components/mini-preview/MiniPreview";
import type { Cell, VarType } from "@/types/task-editor";
import ControlEditorModal from "../ControlEditorModal";
import { MODEL_META, DEFAULT_CELL_SPAN } from "@/types/task-editor/field-config";

/* ── helpers ── */

function rowUsedSpan(row: Cell[]): number {
  return row.reduce((s, c) => s + (c.span ?? 1), 0);
}

/* ── props ── */

export interface GridCanvasProps {
  layout: Cell[][];
  sel: { ri: number; ci: number } | null;
  setSel: (sel: { ri: number; ci: number } | null) => void;
  dragFromLeft: { key: string } | null;
  values: Record<string, unknown>;
  valueTypes: Record<string, VarType>;
  onAddRow: () => void;
  onDeleteRow: (ri: number) => void;

  onCellDrop: (toRi: number, toCi: number, e: ReactDragEvent) => void;
  onCellDragStart: (ri: number, ci: number, e: ReactDragEvent) => void;
  onRowDragOver: (ri: number, e: ReactDragEvent) => void;
  onRowDragStart: (ri: number, e: ReactDragEvent) => void;
  onRowDrop: (toRi: number, e: ReactDragEvent) => void;
  onDrop: (ri: number, ci: number, e: ReactDragEvent) => void;
  onCellUpdate: (ri: number, ci: number, patch: Partial<Cell>) => void;
  onCellRemove: (ri: number, ci: number) => void;
  onChangeControl: (cell: Cell, ri: number, ci: number) => void;
  onChangeValue: (store: string, value: unknown) => void;
  onCancel: () => void;
  onConfirm: () => void;
}

/* ── main ── */

const GridCanvas: FC<GridCanvasProps> = ({
  layout, sel, setSel, dragFromLeft,
  values, valueTypes,
  onAddRow, onDeleteRow,
  onCellDrop, onCellDragStart, onRowDragOver, onRowDragStart, onRowDrop, onDrop,
  onCellUpdate, onCellRemove, onChangeControl, onChangeValue,
  onCancel, onConfirm,
}) => {
  const [ctxMenu, setCtxMenu] = useState<{ x: number; y: number; ri: number; ci: number } | null>(null);

  const selCell = useMemo(() => {
    return sel ? layout[sel.ri]?.[sel.ci] ?? null : null;
  }, [sel, layout]);

  /* ── cell context menu actions ── */

  const handleCellContextMenu = useCallback((ri: number, ci: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setCtxMenu({ x: e.clientX, y: e.clientY, ri, ci });
    setSel({ ri, ci });
  }, [setSel]);

  const handleSpanChange = useCallback((span: number) => {
    if (!ctxMenu) return;
    onCellUpdate(ctxMenu.ri, ctxMenu.ci, { span });
    setCtxMenu(null);
  }, [ctxMenu, onCellUpdate]);

  const handleChangeControl = useCallback(() => {
    if (!ctxMenu) return;
    const cell = layout[ctxMenu.ri]?.[ctxMenu.ci];
    if (cell) {
      onChangeControl(cell, ctxMenu.ri, ctxMenu.ci);
    }
    setCtxMenu(null);
  }, [ctxMenu, layout, onChangeControl]);

  const handleRemoveCell = useCallback(() => {
    if (!ctxMenu) return;
    onCellRemove(ctxMenu.ri, ctxMenu.ci);
  }, [ctxMenu, onCellRemove]);

  return (
    <div className="relative flex-1 bg-container/90 backdrop-blur-sm rounded-2xl border border-slate-100 flex flex-col overflow-hidden shadow-lg">
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
        <Button size="small" onClick={onAddRow} className="!text-[11px] !rounded-xl !shadow-sm">+ 添加行</Button>
      </div>

      {/* grid area */}
      <div
        className="flex-1 overflow-y-auto p-5 bg-[radial-gradient(ellipse_at_top,rgba(248,250,252,0.8),rgba(241,245,249,0.4))] thin-scrollbar"
        onClick={() => { setSel(null); setCtxMenu(null); }}
        onContextMenu={(e) => { e.preventDefault(); setCtxMenu(null); }}
      >
        {layout.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-400">
            <div className="w-20 h-20 rounded-3xl bg-container shadow-md border border-slate-100 flex items-center justify-center">
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
                  className={`rounded-2xl transition-all duration-300 bg-container shadow-sm
                    ${canDrop && dragFromLeft ? "ring-2 ring-indigo-200 shadow-lg" : "shadow-sm hover:shadow-md"}`}
                  onDragOver={(e) => { e.preventDefault(); onRowDragOver(ri, e); }}
                  onDrop={(e) => { onRowDrop(ri, e); onDrop(ri, row.length, e); }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {/* row header */}
                  <div className="flex items-center gap-2 px-3 py-2 rounded-t-[14px] bg-gradient-to-r from-slate-50 to-white">
                    <span
                      draggable
                      onDragStart={(e) => onRowDragStart(ri, e)}
                      className="w-6 h-6 rounded-lg bg-slate-100 text-[10px] font-bold text-slate-500 flex items-center justify-center shadow-sm cursor-grab active:cursor-grabbing hover:bg-slate-200 hover:text-slate-700 transition-colors select-none"
                      title="拖动排序"
                    >
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
                    <button className="text-rose-300 hover:text-rose-500 hover:scale-110 transition-colors duration-200 border-none outline-none bg-transparent p-0 leading-none"
                      onClick={(e) => { e.stopPropagation(); onDeleteRow(ri); }}>
                      <DeleteOutlined className="text-xs" style={{ color: "inherit" }} />
                    </button>
                  </div>

                  {/* cells row */}
                  <div
                    className="relative gap-2 px-2 pb-2 grid grid-cols-[repeat(24,1fr)] min-h-16 items-stretch"
                  >
                    {row.map((cell, ci) => {
                      const span = cell.span ?? 1;
                      const meta = MODEL_META[cell.model ?? "el-input"] ?? MODEL_META["el-input"];
                      const isSel = sel?.ri === ri && sel?.ci === ci;

                      return (
                        <div
                          key={ci}
                          draggable
                          onDragStart={(e) => onCellDragStart(ri, ci, e)}
                          onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                          onDrop={(e) => onCellDrop(ri, ci, e)}
                          onContextMenu={(e) => handleCellContextMenu(ri, ci, e)}
                          onClick={(e) => { e.stopPropagation(); setSel({ ri, ci }); }}
                          className={`relative rounded-xl transition-all duration-200 cursor-pointer
                            flex flex-col justify-center px-2 py-1.5 min-w-0 overflow-hidden group
                            ${isSel
                              ? "ring-2 ring-indigo-300 shadow-lg -translate-y-0.5 z-10"
                              : "shadow-sm hover:shadow-md hover:-translate-y-0.5"}`}
                          style={{
                            gridColumn: `span ${span}`,
                            background: isSel
                              ? `linear-gradient(135deg, ${meta.bg} 0%, #ffffff 100%)`
                              : `linear-gradient(135deg, ${meta.bg} 0%, rgba(255,255,255,0.6) 100%)`,
                          }}
                        >
                          <div className="absolute left-0 top-1 bottom-1 w-[4px] rounded-r-full" style={{ backgroundColor: meta.color, opacity: isSel ? 1 : 0.7 }} />
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
                          <div className="flex scale-[0.85] w-full pointer-events-none opacity-70 group-hover:opacity-100 transition-opacity duration-200">
                            <MiniPreview cell={cell} />
                          </div>
                          {isSel && (
                            <button
                              className="absolute top-2 right-2 text-rose-300 hover:text-rose-500 hover:scale-110 transition-colors border-none outline-none bg-transparent p-0 leading-none"
                              onClick={(e) => { e.stopPropagation(); onCellRemove(ri, ci); }}
                            >
                              <DeleteOutlined className="text-xs" style={{ color: "inherit" }} />
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
                        onDrop={(e) => onDrop(ri, row.length, e)}
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
        onUpdateCell={onCellUpdate}
        onRemoveCell={onCellRemove}
        onChangeControl={() => {
          if (!selCell) return;
          onChangeControl(selCell, sel!.ri, sel!.ci!);
        }}
        onChangeValue={onChangeValue}
      />

      {/* bottom bar */}
      <div className="flex items-center gap-3 px-5 py-3 border-t border-slate-100 bg-gradient-to-r from-slate-50 to-white shrink-0">
        <div className="flex-1" />
        <Button size="small" onClick={onCancel} className="!rounded-xl">取消</Button>
        <Button type="primary" size="small" onClick={onConfirm} className="!rounded-xl !shadow-md !shadow-indigo-200">保存布局</Button>
      </div>

      {/* ═══ Context Menu (right-click on cell) ═══ */}
      {ctxMenu && (
        <div
          className="fixed inset-0 z-40 animate-fadeIn"
          style={{ zoom: "calc(1 / var(--zoom))", background: "rgba(0,0,0,0.03)", backdropFilter: "blur(1px)" }}
          onClick={() => setCtxMenu(null)}
          onContextMenu={(e) => { e.preventDefault(); setCtxMenu(null); }}
        >
          <div
            className="absolute z-50 bg-container/95 backdrop-blur-xl rounded-2xl py-1.5 min-w-[180px] border border-slate-200/80 shadow-[0_20px_60px_rgba(0,0,0,0.12),0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden"
            style={{ left: ctxMenu.x, top: ctxMenu.y }}
          >
            <div className="px-4 py-1.5 text-[10px] font-semibold text-slate-400 tracking-wider uppercase select-none">调整宽度</div>
            <div className="grid grid-cols-4 gap-1 px-2 pb-1">
              {[6, 8, 12, 24].map((w) => (
                <div
                  key={w}
                  className="flex flex-col items-center gap-0.5 py-2 rounded-xl text-xs font-medium text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 transition-all duration-150 cursor-pointer select-none"
                  onClick={() => handleSpanChange(w)}
                >
                  <span className="text-sm font-bold">{w}</span>
                  <span className="text-[9px] opacity-50">列</span>
                </div>
              ))}
            </div>
            <div className="h-px bg-slate-100 mx-3 my-1" />
            <div
              className="w-full text-left px-4 py-2 text-[12px] text-slate-600 hover:bg-indigo-50 hover:text-indigo-600 transition-colors duration-150 cursor-pointer flex items-center gap-3 select-none"
              onClick={handleChangeControl}
            >
              <span className="w-6 h-6 rounded-lg bg-indigo-100 text-indigo-500 flex items-center justify-center text-xs shrink-0">⇄</span>
              更换控件
            </div>
            <div className="h-px bg-slate-100 mx-3 my-1" />
            <div
              className="w-full text-left px-4 py-2 text-[12px] text-rose-500 hover:bg-rose-50 transition-colors duration-150 cursor-pointer flex items-center gap-3 select-none"
              onClick={handleRemoveCell}
            >
              <span className="w-6 h-6 rounded-lg bg-rose-100 text-rose-400 flex items-center justify-center text-xs shrink-0">×</span>
              移除
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GridCanvas;
