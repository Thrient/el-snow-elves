import { useState, type FC } from "react";
import { Modal } from "antd";
import type { VarType } from "@/types/task";

interface UnboundVar {
  key: string;
  value: unknown;
  type: VarType;
}

export interface UnboundPanelProps {
  unboundVars: UnboundVar[];
  values: Record<string, unknown>;
  dragFromLeft: { key: string } | null;
  onDragStart: (key: string) => void;
  onDragEnd: () => void;
  onDeleteVar: (key: string) => void;
  onCreateVar: () => void;
}

const UnboundPanel: FC<UnboundPanelProps> = ({
  unboundVars, values,
  onDragStart, onDragEnd, onDeleteVar, onCreateVar,
}) => {
  const [leftCtxMenu, setLeftCtxMenu] = useState<{ x: number; y: number } | null>(null);

  return (
    <>
      <div
        className="w-[250px] shrink-0 bg-white/90 backdrop-blur-sm rounded-2xl border border-slate-100 flex flex-col overflow-hidden shadow-md"
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
              const typeIcon = type === "number" ? "12" : type === "switch" ? "⇄" : type === "list" ? "[ ]" : "Aa";
              const typeColor = type === "number" ? "#10b981" : type === "switch" ? "#f59e0b" : type === "list" ? "#ec4899" : "#6366f1";
              const valStr = value === null || value === undefined ? "" : String(value);

              return (
                <div
                  key={key}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData("text/plain", key);
                    e.dataTransfer.effectAllowed = "move";
                    onDragStart(key);
                  }}
                  onDragEnd={onDragEnd}
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
                      onClick={(e) => { e.stopPropagation(); onDeleteVar(key); }}
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

      {/* ═══ Left Context Menu (right-click on unbound panel) ═══ */}
      {leftCtxMenu && (
        <div
          className="fixed inset-0 z-40 animate-fadeIn"
          style={{ zoom: "calc(1 / var(--zoom))", background: "rgba(0,0,0,0.03)", backdropFilter: "blur(1px)" }}
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
                onCreateVar();
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
                    onOk: () => { for (const k of toDelete) onDeleteVar(k); },
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
    </>
  );
};

export default UnboundPanel;
