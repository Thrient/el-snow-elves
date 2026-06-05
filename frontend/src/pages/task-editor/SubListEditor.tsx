import { useState, type FC } from "react";
import type React from "react";
import { AutoComplete } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import type { EditorCtx } from "@/types/task-editor/actions";
import SubflowModalItem from "./SubflowModalItem";
import VarOpBuilder from "@/pages/task-editor/components/var-op-builder/VarOpBuilder";

interface SubListEditorProps {
  list: any[];
  ctx: EditorCtx;
  isKeyValue?: boolean;
  color: string;
  onChange: (v: any[]) => void;
}

const SubListEditor: FC<SubListEditorProps> = ({ list, ctx, isKeyValue, color, onChange }) => {
  const arr = list ?? [];
  const [dragIdx, setDragIdx] = useState<number | null>(null);
  const [dropTarget, setDropTarget] = useState<number | null>(null);

  const handleDragStart = (i: number) => setDragIdx(i);
  const handleDragEnd = () => { setDragIdx(null); setDropTarget(null); };
  const handleDragOver = (i: number, e: React.DragEvent) => {
    e.preventDefault();
    if (dragIdx !== null && dragIdx !== i) setDropTarget(i);
  };
  const handleDrop = (i: number) => {
    if (dragIdx === null || dragIdx === i) return;
    const u = [...arr];
    const [moved] = u.splice(dragIdx, 1);
    u.splice(i, 0, moved);
    onChange(u);
  };

  return (
    <div className="space-y-2">
      {arr.map((item, i) => isKeyValue ? (
        <div key={i} draggable
          onDragStart={() => handleDragStart(i)} onDragEnd={handleDragEnd}
          onDragOver={(e) => handleDragOver(i, e)} onDrop={() => handleDrop(i)}
          className={`group rounded-xl border border-dashed bg-container transition-colors cursor-grab active:cursor-grabbing
            ${dropTarget === i ? "border-indigo-400 shadow-md shadow-indigo-100 -translate-y-0.5" : ""}`}
          style={{ borderColor: dropTarget === i ? "#818cf8" : `${color}4d`, background: `linear-gradient(135deg, ${color}0a, #fff)` }}>
          <div className="flex items-center gap-2 px-3.5 py-2">
            <span className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-semibold shrink-0"
              style={{ background: `${color}18`, color }}>{i + 1}</span>
            <AutoComplete size="small" variant="borderless" placeholder="变量名" className="flex-1 font-mono text-[12px]" value={item.name}
              popupMatchSelectWidth={false}
              options={ctx.taskValueVars.map(v => ({ value: v.value.replace(/^\{|\}$/g, ""), label: v.label.replace(/^\{|\}$/g, "") }))}
              filterOption={(iv, opt) => opt?.label?.toLowerCase().includes(iv.toLowerCase()) ?? false}
              onChange={(v) => { const u = [...arr]; u[i] = { ...u[i], name: (v ?? "").replace(/^\{|\}$/g, "") }; onChange(u); }} />
            <span className="font-mono text-[10px] text-muted shrink-0">=</span>
            <AutoComplete className="flex-1" size="small" variant="borderless" placeholder="值" value={item.value as string}
              popupMatchSelectWidth={false}
              options={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars, ...ctx.taskSteps, ...ctx.taskCommonSteps, ...ctx.globalCommonSteps]}
              filterOption={(iv, opt) => opt?.label?.toLowerCase().includes(iv.toLowerCase()) ?? false}
              onChange={(v) => { const u = [...arr]; u[i] = { ...u[i], value: v }; onChange(u); }} />
            <VarOpBuilder
              context="set"
              valueTypes={ctx.valueTypes}
              variables={[
                ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
                ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
                ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
              ]}
              onInsert={(expr) => { const u = [...arr]; u[i] = { ...u[i], value: expr }; onChange(u); }}
            >
              <span className="text-[#9ca3af] hover:text-[#d4513b] opacity-0 group-hover:opacity-100 transition-all shrink-0 cursor-pointer select-none mx-0.5 text-[11px] font-semibold leading-none">fx</span>
            </VarOpBuilder>
            <span className="text-[#c0c4cc] opacity-0 group-hover:opacity-100 transition-all shrink-0 text-[10px] select-none cursor-grab">⠿</span>
            <button onClick={() => onChange(arr.filter((_, j) => j !== i))}
              className="text-[#c0c4cc] hover:text-[#ff4d4f] opacity-0 group-hover:opacity-100 transition-all text-xs shrink-0 border-0 bg-transparent cursor-pointer">×</button>
          </div>
        </div>
      ) : (
        <div key={i} draggable
          onDragStart={() => handleDragStart(i)} onDragEnd={handleDragEnd}
          onDragOver={(e) => handleDragOver(i, e)} onDrop={() => handleDrop(i)}
          className={dropTarget === i ? "rounded-xl ring-2 ring-indigo-400 ring-offset-1" : ""}>
          <SubflowModalItem index={i} item={item} ctx={ctx} arr={arr} color={color} onChange={onChange} />
        </div>
      ))}
      {arr.length === 0 && (
        <div className="text-center py-1">
          <span className="text-[11px] text-[#c0c4cc]">
            {isKeyValue ? "暂无变量，点击下方添加" : "暂无子步骤，点击下方添加"}
          </span>
        </div>
      )}
      <div className="rounded-xl border border-dashed bg-container"
        style={{ borderColor: "rgba(148,163,184,0.3)", background: "linear-gradient(135deg, rgba(148,163,184,0.03), #fff)" }}>
        <div className="flex items-center gap-2 px-3.5 py-2">
          <span className="text-[11px] font-medium text-muted shrink-0">
            添加{isKeyValue ? "变量" : "步骤"}
          </span>
          <span className="h-px flex-1" style={{ background: "linear-gradient(to right, #e5e7eb, transparent)" }} />
        </div>
        <div className="px-3.5 pb-3 flex flex-wrap gap-1.5">
          <button onClick={() => onChange([...arr, isKeyValue ? { name: "", value: "" } : { step: "" }])}
            className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg border border-dashed border-[#dde0e6] text-secondary bg-container hover:text-[#1677ff] hover:border-[#1677ff] hover:shadow-sm transition-all cursor-pointer"
            style={{ background: "transparent" } as React.CSSProperties}>
            <PlusOutlined className="text-[10px]" />
            新增{isKeyValue ? "变量" : "步骤"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubListEditor;
