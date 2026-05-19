import { useState, useEffect, type FC } from "react";
import { AutoComplete, Button, Input, InputNumber, Select, Tooltip, message } from "antd";
import { CloseOutlined, CheckOutlined, ArrowRightOutlined, DeleteOutlined, LeftOutlined, BugOutlined, PictureOutlined, ReloadOutlined, ApartmentOutlined, PlusOutlined } from "@ant-design/icons";
import type { Step } from "@/types/task";
import type { EditorCtx } from "./constants";
import { ACTION_OPTS, ACTIONS_WITH_TEMPLATES, ACTION_PARAMS, PARAM_META, REQUIRED_PARAMS } from "./constants";
import SubflowModalItem from "./SubflowModalItem";
import PosInput from "./PosInput";
import BoxInput from "./BoxInput";
import BoxPickerModal from "@/components/box-picker/BoxPickerModal";
import PreprocessEditor from "./PreprocessEditor";
import KeyInput from "@/components/settings-field/components/KeyInput";
import CoordPickerModal from "@/components/coord-picker/CoordPickerModal";
import VarOpBuilder from "@/components/var-op-builder/VarOpBuilder";
import { useCharacterStore } from "@/store/character";
import { useEditorStore } from "@/store/editor-store";

/* ================================================================
   StepPanel — dashboard + single-expand editing panel
   ================================================================ */

interface Props {
  stepName: string; step: Step; isCommon: boolean; ctx: EditorCtx;
  onClose: () => void; onRename: (name: string) => void;
  onUpdate: (field: string, value: unknown) => void; onDelete: () => void;
}

// ---- Card registry ----

type CardKey = "flow" | "params" | "prefix" | "postfix" | "failure_extra" | "success_extra" | "set" | "retry" | "extends";

const CARDS: { key: CardKey; label: string; color: string; light: string; desc: string; summary(s: Step): string }[] = [
  { key: "flow",   label: "流程跳转", color: "#16a34a", light: "#dcfce7", desc: "成功 / 失败 / 无条件",
    summary: s => [s.success && `✓${s.success}`, s.failure && `✗${s.failure}`, s.next && `→${s.next}`].filter(Boolean).join("  ") || "" },
  { key: "params", label: "执行参数", color: "#ca8a04", light: "#fef9c3", desc: "模板图片 / 阈值 / 坐标",
    summary: s => { const n = ((s.params?.args as string[]) ?? []).length + Object.keys(s.params ?? {}).filter(k => k !== "args").length; return n ? `${n} 个参数` : ""; } },
  { key: "prefix", label: "前置步骤", color: "#16a34a", light: "#dcfce7", desc: "主步骤前执行",
    summary: s => s.prefix?.length ? `${s.prefix.length} 个` : "" },
  { key: "postfix",label: "后置步骤", color: "#f59e0b", light: "#fef3c7", desc: "主步骤后执行",
    summary: s => s.postfix?.length ? `${s.postfix.length} 个` : "" },
  { key: "failure_extra", label: "失败附加", color: "#dc2626", light: "#fecaca", desc: "失败时额外执行",
    summary: s => s.failure_extra?.length ? `${s.failure_extra.length} 个` : "" },
  { key: "success_extra", label: "成功附加", color: "#2563eb", light: "#bfdbfe", desc: "成功时额外执行",
    summary: s => s.success_extra?.length ? `${s.success_extra.length} 个` : "" },
  { key: "set",    label: "set 变量", color: "#9333ea", light: "#e9d5ff", desc: "设置运行时变量",
    summary: s => s.set?.length ? `${s.set.length} 个` : "" },
  { key: "retry",  label: "失败重试", color: "#dc2626", light: "#fecaca", desc: "失败后自动重试",
    summary: s => s.retry?.times ? `${s.retry.times}次 · ${s.retry.interval ?? 0}ms` : "" },
  { key: "extends",label: "继承模板", color: "#8b5cf6", light: "#ddd6fe", desc: "复用已有步骤配置",
    summary: s => s.extends || "" },
];

// ---- Inline sub-editors ----

const FlowEditor: FC<{ step: Step; stepOpts: { value: string; label: string }[]; stepName: string; onUpdate: Props["onUpdate"] }> =
  ({ step, stepOpts, stepName, onUpdate }) => {
    const items = [
      { k: "success" as const, label: "成功跳转", hint: "执行成功后跳转", color: "#16a34a", icon: <CheckOutlined /> },
      { k: "failure" as const, label: "失败跳转", hint: "执行失败后跳转", color: "#dc2626", icon: <CloseOutlined /> },
      { k: "next"    as const, label: "无条件跳转", hint: "无论结果都跳转", color: "#6b7280", icon: <ArrowRightOutlined /> },
    ];
    return (
      <div className="space-y-2">
        {items.map(({ k, label, hint, color, icon }) => (
          <div key={k} className="group rounded-xl border border-dashed bg-white transition-colors"
            style={{ borderColor: `${color}4d`, background: `linear-gradient(135deg, ${color}0a, #fff)` }}>
            <div className="flex items-center gap-2 px-3.5 py-2">
              <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
                style={{ background: `${color}18`, color }}>
                {icon}
              </span>
              <span className="text-[12px] text-[#374151]">{label}</span>
              <span className="text-[10px] text-[#8b8fa3]">{hint}</span>
              <Select className="flex-1 min-w-0 ml-auto" size="small" allowClear showSearch
                placeholder="选择目标步骤" popupMatchSelectWidth={false}
                value={(step as any)[k] || undefined}
                options={stepOpts.filter(o => o.value !== stepName)}
                onChange={(v) => onUpdate(k, v ?? "")} />
            </div>
          </div>
        ))}
      </div>
    );
  };

const ParamsEditor: FC<{ step: Step; ctx: EditorCtx; onUpdate: Props["onUpdate"] }> = ({ step, ctx, onUpdate }) => {
  const [coordOpen, setCoordOpen] = useState(false);
  const [boxOpen, setBoxOpen] = useState(false);
  const [templateOptions, setTemplateOptions] = useState<{ value: string; label: string }[]>([]);
  const params = step.params ?? {};
  const args = (params.args as string[]) ?? [];
  const required = step.action ? (REQUIRED_PARAMS[step.action] ?? []) : [];
  const other = Object.keys(params).filter(k => k !== "args").sort((a, b) => {
    const aReq = required.includes(a) ? 0 : 1;
    const bReq = required.includes(b) ? 0 : 1;
    return aReq - bReq;
  });
  const showArgs = step.action ? ACTIONS_WITH_TEMPLATES.has(step.action) : false;
  const allowed = step.action ? (ACTION_PARAMS[step.action] ?? []) : [];

  // 自动注入必填参数
  useEffect(() => {
    const missing = required.filter(k => params[k] === undefined);
    if (missing.length > 0) {
      const p = { ...params };
      for (const k of missing) p[k] = "";
      onUpdate("params", p);
    }
  }, [step.action]);

  const canAdd = allowed.filter(k => params[k] === undefined);

  useEffect(() => {
    if (!showArgs) return;
    (async () => {
      try {
        const names: string[] = await window.pywebview?.api.emit(
          "API:AUTOCOMPLETE:TEMPLATES",
          ctx.taskName ?? null,
          ctx.version ?? null
        );
        setTemplateOptions((names ?? []).map((name) => ({ value: name, label: name })));
      } catch {
        setTemplateOptions([]);
      }
    })();
  }, [showArgs, ctx.taskName, ctx.version, ctx.refreshKey]);

  const renderParamInput = (key: string, value: unknown) => {
    if (key === "preprocess") {
      return (
        <PreprocessEditor
          value={(value ?? {}) as Record<string, unknown>}
          onChange={(v) => onUpdate("params", { ...params, preprocess: v })}
          onRemove={() => { const p = { ...params }; delete p.preprocess; onUpdate("params", p); }} />
      );
    }
    if (key === "box") {
      return <BoxInput params={params} onUpdate={onUpdate} hwnd={ctx.hwnd} onBoxOpen={() => setBoxOpen(true)} />;
    }
    if (key === "pos") {
      return <PosInput params={params} onUpdate={onUpdate} hwnd={ctx.hwnd} onCoordOpen={() => setCoordOpen(true)} />;
    }
    if (key === "hwnd") {
      return (
        <AutoComplete
          size="small"
          className="w-full"
          value={(value as string) ?? ""}
          onChange={(v) => onUpdate("params", { ...params, hwnd: v ?? "" })}
          options={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars]}
          placeholder="{hwnd}"
          allowClear
          filterOption={(input, option) =>
            option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
          }
        />
      );
    }
    if (key === "click_mode") {
      return (
        <Select size="small" style={{ width: 150 }} allowClear
          value={(value as string) || undefined}
          placeholder="默认 random"
          options={[
            { value: "random", label: "random — 随机选一个" },
            { value: "first", label: "first — 第一个" },
            { value: "last", label: "last — 最后一个" },
            { value: "all", label: "all — 全部点击" },
            { value: "all_reverse", label: "all_reverse — 倒序全部" },
          ]}
          onChange={(v) => onUpdate("params", { ...params, click_mode: v ?? "" })} />
      );
    }
    if (key === "text") {
      return (
        <div className="flex items-center gap-1 w-full">
          <AutoComplete
            size="small"
            className="flex-1"
            value={(value as string) ?? ""}
            onChange={(v) => onUpdate("params", { ...params, text: v ?? "" })}
            options={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars]}
            placeholder="输入文本，支持 {变量}"
            filterOption={(input, option) =>
              option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
            }
          />
          <VarOpBuilder
            context="params"
            variables={[
              ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
              ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
              ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
            ]}
            onInsert={(expr) => onUpdate("params", { ...params, text: (value as string ?? "") + expr })}
          >
            <button className="flex items-center justify-center rounded border-0 bg-transparent cursor-pointer shrink-0 transition-colors"
              style={{ width: 20, height: 20, color: "#c4bbb2" }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}
            >fx</button>
          </VarOpBuilder>
        </div>
      );
    }
    if (key === "key") {
      return (
        <KeyInput value={(value as string) ?? ""}
          onChange={(v) => onUpdate("params", { ...params, key: v })}
          varOptions={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars]} />
      );
    }
    if (key === "account_name") {
      return (
        <AutoComplete
          size="small"
          style={{ width: 160 }}
          value={value as string}
          onChange={(v) => onUpdate("params", { ...params, account_name: v })}
          options={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars]}
          placeholder="{account_name}"
          allowClear
          filterOption={(input, option) =>
            option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
          }
        />
      );
    }
    // Number params
    if (key === "threshold" || key === "seconds" || key === "k" || key === "count" || key === "x" || key === "y" ||
        key === "pre_delay" || key === "post_delay") {
      const raw = typeof value === "string" ? value : String(value ?? "");
      return (
        <Input size="small" className="font-mono text-[12px]" style={{ width: 80 }}
          value={raw}
          onChange={(e) => {
            const v = e.target.value;
            if (v === "" || v === "null") {
              onUpdate("params", { ...params, [key]: v === "null" ? null : "" });
              return;
            }
            const n = Number(v);
            onUpdate("params", { ...params, [key]: !isNaN(n) ? n : v });
          }} />
      );
    }
    // plain text fallback
    const raw = typeof value === "string" ? value : JSON.stringify(value ?? "");
    return (
      <div className="flex items-center gap-1">
        <Input size="small" className="font-mono text-[12px]" style={{ width: 140 }}
          value={raw}
          onChange={(e) => {
            let v: unknown = e.target.value;
            const n = Number(v);
            if (v !== "" && !isNaN(n)) v = n;
            onUpdate("params", { ...params, [key]: v });
          }} />
        <VarOpBuilder
          context="params"
          variables={[
            ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
            ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
            ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
          ]}
          onInsert={(expr) => {
            let newVal = (typeof value === "string" ? value : JSON.stringify(value ?? "")) + expr;
            const n = Number(newVal);
            if (newVal !== "" && !isNaN(n)) newVal = String(n);
            onUpdate("params", { ...params, [key]: newVal });
          }}
        >
          <button className="flex items-center justify-center rounded border-0 bg-transparent cursor-pointer shrink-0 transition-colors"
            style={{ width: 20, height: 20, color: "#c4bbb2" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}
          >fx</button>
        </VarOpBuilder>
      </div>
    );
  };

  return (
    <div className="space-y-2.5">
      {/* 模板图片 args */}
      {showArgs && (
        <div className="rounded-xl border border-dashed bg-white"
          style={{ borderColor: "rgba(59,130,246,0.25)", background: "linear-gradient(135deg, rgba(59,130,246,0.04), #fff)" }}>
          <div className="flex items-center gap-2 px-3.5 py-2.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
              style={{ background: "rgba(59,130,246,0.1)", color: "#3b82f6" }}>
              <PictureOutlined />
            </span>
            <span className="text-[12px] font-semibold text-[#1a1a2e]">模板图片</span>
            <Tooltip title="模板图片名列表，不含路径和 .bmp 后缀。支持 {变量} 嵌入" placement="top">
              <span className="text-[10px] text-[#c0c4cc] cursor-help hover:text-[#6b7280]">?</span>
            </Tooltip>
            <span className="text-[10px] text-[#8b8fa3] ml-auto">输入图片名后回车添加</span>
          </div>
          <div className="px-3.5 pb-3">
            <Select mode="tags" className="w-full" size="small" placeholder="输入图片名回车添加，如 按钮登录"
              value={args} options={templateOptions}
              filterOption={(input, option) => (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())}
              onChange={(v) => onUpdate("params", { ...params, args: v })} />
          </div>
        </div>
      )}

      {/* 已添加的参数 */}
      {other.map(key => {
        const meta = PARAM_META[key];
        if (key === "preprocess") {
          return <div key={key}>{renderParamInput(key, params[key])}</div>;
        }
        const accentColor = meta?.color ?? "#9ca3af";
        // pos / box / key / hwnd / text need more space
        if (key === "pos" || key === "box" || key === "key" || key === "hwnd" || key === "text") {
          return (
            <div key={key} className="group rounded-xl border border-dashed bg-white transition-colors"
              style={{ borderColor: `${accentColor}4d`, background: `linear-gradient(135deg, ${accentColor}0a, #fff)` }}>
              <div className="flex items-center justify-between px-3.5 py-2">
                <Tooltip title={meta?.tip || meta?.desc} placement="left">
                  <div className="flex items-center gap-1.5 cursor-help">
                    <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0" style={{ background: `${accentColor}18`, color: accentColor, fontSize: "13px" }}>
                      {meta?.icon}
                    </span>
                    <span className="text-[12px] text-[#374151] select-none">{meta?.label ?? key}</span>
                  </div>
                </Tooltip>
                <button onClick={() => { const p = { ...params }; delete p[key]; onUpdate("params", p); }}
                  className="text-[#c0c4cc] hover:text-[#ff4d4f] opacity-0 group-hover:opacity-100 transition-all text-xs shrink-0 border-0 bg-transparent cursor-pointer">×</button>
              </div>
              <div className="px-3.5 pb-2.5">
                {renderParamInput(key, params[key])}
              </div>
            </div>
          );
        }
        // Standard compact row card
        return (
          <div key={key} className="group rounded-xl border border-dashed bg-white transition-colors"
            style={{ borderColor: `${accentColor}4d`, background: `linear-gradient(135deg, ${accentColor}0a, #fff)` }}>
            <div className="flex items-center justify-between px-3.5 py-2">
              <Tooltip title={meta?.tip || meta?.desc} placement="left">
                <div className="flex items-center gap-1.5 cursor-help min-w-0">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0" style={{ background: `${accentColor}18`, color: accentColor, fontSize: "13px" }}>
                    {meta?.icon}
                  </span>
                  <span className="text-[12px] text-[#374151] select-none truncate">{meta?.label ?? key}</span>
                  {meta?.range && (
                    <span className="text-[10px] text-[#c0c4cc] font-mono shrink-0 hidden sm:inline">{meta.range}</span>
                  )}
                </div>
              </Tooltip>
              <div className="flex items-center gap-1.5 shrink-0">
                {renderParamInput(key, params[key])}
                <button onClick={() => { const p = { ...params }; delete p[key]; onUpdate("params", p); }}
                  className="text-[#c0c4cc] hover:text-[#ff4d4f] opacity-0 group-hover:opacity-100 transition-all text-xs border-0 bg-transparent cursor-pointer">×</button>
              </div>
            </div>
          </div>
        );
      })}

      {/* 添加参数 */}
      {canAdd.length > 0 && (
        <div className="rounded-xl border border-dashed bg-white"
          style={{ borderColor: "rgba(148,163,184,0.3)", background: "linear-gradient(135deg, rgba(148,163,184,0.03), #fff)" }}>
          <div className="flex items-center gap-2 px-3.5 py-2">
            <span className="text-[11px] font-medium text-[#8b8fa3] shrink-0">添加参数</span>
            <span className="h-px flex-1" style={{ background: "linear-gradient(to right, #e5e7eb, transparent)" }} />
          </div>
          <div className="px-3.5 pb-3 flex flex-wrap gap-1.5">
          {canAdd.map(k => {
            const meta = PARAM_META[k];
            const accent = meta?.color ?? "#9ca3af";
            return (
              <Tooltip key={k} title={meta?.desc}>
                <button onClick={() => onUpdate("params", { ...params, [k]: "" })}
                  className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg border border-dashed border-[#dde0e6] text-[#6b7280] bg-white hover:text-[#1677ff] hover:border-[#1677ff] hover:shadow-sm transition-all cursor-pointer border-0 bg-transparent"
                  style={{ border: `1px dashed ${accent}40`, background: `${accent}06` } as React.CSSProperties}>
                  <span className="flex items-center justify-center w-4 h-4 rounded shrink-0 text-[10px]" style={{ background: `${accent}18`, color: accent }}>
                    {meta?.icon}
                  </span>
                  {meta?.label ?? k}
                </button>
              </Tooltip>
            );
          })}
          </div>
        </div>
      )}
      {ctx.hwnd && <CoordPickerModal open={coordOpen} hwnd={ctx.hwnd}
        onClose={() => setCoordOpen(false)}
        onPick={(x, y) => onUpdate("params", { ...params, pos: [x, y] })} />}
      {ctx.hwnd && <BoxPickerModal open={boxOpen} hwnd={ctx.hwnd}
        onClose={() => setBoxOpen(false)}
        onPick={(x1, y1, x2, y2) => onUpdate("params", { ...params, box: [x1, y1, x2, y2] })} />}
    </div>
  );
};

const SubListEditor: FC<{
  list: any[]; ctx: EditorCtx; isKeyValue?: boolean; color: string; onChange: (v: any[]) => void;
}> = ({ list, ctx, isKeyValue, color, onChange }) => {
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
          className={`group rounded-xl border border-dashed bg-white transition-colors cursor-grab active:cursor-grabbing
            ${dropTarget === i ? "border-indigo-400 shadow-md shadow-indigo-100 -translate-y-0.5" : ""}`}
          style={{ borderColor: dropTarget === i ? "#818cf8" : `${color}4d`, background: `linear-gradient(135deg, ${color}0a, #fff)` }}>
          <div className="flex items-center gap-2 px-3.5 py-2">
            <span className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-semibold shrink-0"
              style={{ background: `${color}18`, color }}>{i + 1}</span>
            <AutoComplete size="small" variant="borderless" placeholder="变量名" className="flex-1 font-mono text-[12px]" value={item.name}
              popupMatchSelectWidth={false}
              options={[...ctx.taskValueVars]}
              filterOption={(iv, opt) => opt?.label?.toLowerCase().includes(iv.toLowerCase()) ?? false}
              onChange={(v) => { const u = [...arr]; u[i] = { ...u[i], name: v }; onChange(u); }} />
            <span className="font-mono text-[10px] text-[#8b8fa3] shrink-0">=</span>
            <AutoComplete className="flex-1" size="small" variant="borderless" placeholder="值" value={item.value as string}
              popupMatchSelectWidth={false}
              options={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars, ...ctx.taskSteps, ...ctx.taskCommonSteps, ...ctx.globalCommonSteps]}
              filterOption={(iv, opt) => opt?.label?.toLowerCase().includes(iv.toLowerCase()) ?? false}
              onChange={(v) => { const u = [...arr]; u[i] = { ...u[i], value: v }; onChange(u); }} />
            <VarOpBuilder
              context="set"
              variables={[
                ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
                ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
                ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
              ]}
              onInsert={(expr) => { const u = [...arr]; u[i] = { ...u[i], value: expr }; onChange(u); }}
            >
              <span className="text-[#c0c4cc] hover:text-[#d4513b] opacity-0 group-hover:opacity-100 transition-all shrink-0 cursor-pointer select-none mx-0.5"
                style={{ fontSize: 14, lineHeight: 1 }}>fx</span>
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
      <div className="rounded-xl border border-dashed bg-white"
        style={{ borderColor: "rgba(148,163,184,0.3)", background: "linear-gradient(135deg, rgba(148,163,184,0.03), #fff)" }}>
        <div className="flex items-center gap-2 px-3.5 py-2">
          <span className="text-[11px] font-medium text-[#8b8fa3] shrink-0">
            添加{isKeyValue ? "变量" : "步骤"}
          </span>
          <span className="h-px flex-1" style={{ background: "linear-gradient(to right, #e5e7eb, transparent)" }} />
        </div>
        <div className="px-3.5 pb-3 flex flex-wrap gap-1.5">
          <button onClick={() => onChange([...arr, isKeyValue ? { name: "", value: "" } : { step: "" }])}
            className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg border border-dashed border-[#dde0e6] text-[#6b7280] bg-white hover:text-[#1677ff] hover:border-[#1677ff] hover:shadow-sm transition-all cursor-pointer"
            style={{ background: "transparent" } as React.CSSProperties}>
            <PlusOutlined className="text-[10px]" />
            新增{isKeyValue ? "变量" : "步骤"}
          </button>
        </div>
      </div>
    </div>
  );
};

// ---- Main ----

const StepPanel: FC<Props> = ({ stepName, step, isCommon, ctx, onClose, onRename, onUpdate, onDelete }) => {
  const [expanded, setExpanded] = useState<CardKey | null>(null);
  const [nameEdit, setNameEdit] = useState(false);
  const [nameDraft, setNameDraft] = useState(stepName);

  const card = expanded ? CARDS.find(c => c.key === expanded)! : null;

  return (
    <div className="flex flex-col h-full bg-[#fafbfc]">
      {/* ── Header ── */}
      <div className="shrink-0 px-4 py-3 flex items-center gap-2 bg-white border-b border-[#eef0f2]">
        {isCommon && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-[#fff7e6] text-[#f59e0b] font-semibold tracking-wide shrink-0">公共</span>
        )}
        {nameEdit ? (
          <Input size="small" autoFocus className="!font-semibold flex-1" value={nameDraft}
            onChange={e => setNameDraft(e.target.value)}
            onBlur={() => { if (nameDraft && nameDraft !== stepName) onRename(nameDraft); setNameEdit(false); }}
            onPressEnter={() => { if (nameDraft && nameDraft !== stepName) onRename(nameDraft); setNameEdit(false); }} />
        ) : (
          <h3 className="flex-1 min-w-0 text-sm font-semibold text-[#1a1a2e] truncate cursor-pointer select-none"
            onDoubleClick={() => { setNameDraft(stepName); setNameEdit(true); }}
            title="双击重命名">{stepName}</h3>
        )}
        <Tooltip title="删除步骤"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={onDelete} /></Tooltip>
        <Tooltip title="关闭面板"><Button type="text" size="small" icon={<CloseOutlined />} onClick={onClose} /></Tooltip>
      </div>

      {/* ── Body ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">

        {/* Basic info */}
        <div className="rounded-xl border border-[#eef0f2] bg-white p-3.5 space-y-2.5">
          <div className="flex items-center gap-2">
            <div className="w-1 h-4 rounded-full bg-[#1677ff]" />
            <span className="text-[11px] font-semibold text-[#1a1a2e]">基础</span>
          </div>
          <div className="flex items-center gap-1">
            <Select className="flex-1" size="small" allowClear showSearch placeholder="选择动作…"
              value={step.action || undefined} popupMatchSelectWidth={false}
              onChange={v => {
                const newAction = v ?? "";
                const allowed = newAction ? (ACTION_PARAMS[newAction] ?? []) : [];
                const oldParams = (step.params ?? {}) as Record<string, unknown>;
                const clean: Record<string, unknown> = {};
                for (const k of Object.keys(oldParams)) {
                  if (k === "args" || allowed.includes(k)) clean[k] = oldParams[k];
                }
                for (const k of (REQUIRED_PARAMS[newAction] ?? [])) {
                  if (!(k in clean)) clean[k] = "";
                }
                useEditorStore.getState().updateStep(stepName, {
                  ...step, action: newAction, params: clean,
                }, isCommon);
                onUpdate("action", newAction);
              }}
              options={ACTION_OPTS.map(o => ({
                value: o.value,
                label: (
                  <span className="flex items-center gap-1.5">
                    <span style={{ color: o.color, fontSize: 13, display: "inline-flex" }}>{o.icon}</span>
                    <code className="text-[11px] font-semibold px-1.5 py-px rounded" style={{ background: `${o.color}14`, color: o.color }}>
                      {o.label}
                    </code>
                  </span>
                ),
              }))}
              optionRender={(option) => {
                const o = ACTION_OPTS.find((a) => a.value === option.value);
                if (!o) return option.label;
                return (
                  <div className="flex items-center gap-2 px-1 py-0.5">
                    <span className="flex items-center justify-center rounded shrink-0" style={{ width: 24, height: 24, background: `${o.color}14`, color: o.color, fontSize: 13 }}>
                      {o.icon}
                    </span>
                    <div className="flex flex-col gap-0.5 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <code className="text-[11px] font-semibold px-1.5 py-px rounded" style={{ background: `${o.color}14`, color: o.color }}>
                          {o.label}
                        </code>
                        <span className="text-[9px] uppercase tracking-wider font-semibold px-1 rounded" style={{ background: "#f3f0ec", color: "#9a8e82" }}>
                          {o.group}
                        </span>
                      </div>
                      <span className="text-[11px] leading-tight" style={{ color: "#8b8fa3" }}>{o.desc}</span>
                    </div>
                  </div>
                );
              }}
            />
            {step.action && (step.action === "{True}" || step.action.startsWith("{")) && (
              <VarOpBuilder
                context="when"
                value={step.action}
                variables={[
                  ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
                  ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
                  ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
                ]}
                onInsert={(expr) => onUpdate("action", expr)}
              >
                <button className="flex items-center justify-center rounded border-0 bg-transparent cursor-pointer shrink-0 transition-colors"
                  style={{ width: 20, height: 20, color: "#6366f1", fontSize: 11, fontWeight: 600 }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "#eef2ff"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                >fx</button>
              </VarOpBuilder>
            )}
          </div>
        </div>

        {/* ── Debug execution ── */}
        {ctx.hwnd && (
          <div className="rounded-xl border border-dashed border-[#ffa940] bg-[#fffbe6] p-3.5 space-y-2">
            <div className="flex items-center gap-2">
              <BugOutlined className="text-[#fa8c16] text-sm" />
              <span className="text-[11px] font-semibold text-[#1a1a2e]">调试运行</span>
              <span className="text-[10px] text-[#8b8fa3]">窗口 {ctx.hwnd}</span>
            </div>
            <div className="flex gap-2">
              <Button size="small" type="primary"
                style={{ borderColor: '#fa8c16', background: '#fa8c16' }}
                onClick={() => {
                  const task = useEditorStore.getState().currentTask;
                  if (!task) return;
                  const charStore = useCharacterStore.getState();
                  const hwnd = charStore.selectedHwnd;
                  if (!hwnd) { message.warning("请先在窗口管理中选择一个窗口"); return; }
                  charStore.pushExecute(hwnd, {
                    id: task.id, name: task.name, version: task.version,
                    values: task.values, debugStart: stepName,
                  });
                  message.success(`已添加到窗口 ${hwnd}：从「${stepName}」开始`);
                }}>
                从此步骤开始
              </Button>
              <Button size="small"
                style={{ borderColor: '#fa8c16', color: '#fa8c16' }}
                onClick={() => {
                  const task = useEditorStore.getState().currentTask;
                  if (!task) return;
                  const charStore = useCharacterStore.getState();
                  const hwnd = charStore.selectedHwnd;
                  if (!hwnd) { message.warning("请先在窗口管理中选择一个窗口"); return; }
                  charStore.pushExecute(hwnd, {
                    id: task.id, name: task.name, version: task.version,
                    values: task.values, debugStart: stepName, debugSingle: true,
                  });
                  message.success(`已添加到窗口 ${hwnd}：单步执行「${stepName}」`);
                }}>
                单步执行
              </Button>
            </div>
            <div className="text-[10px] text-[#8b8fa3] leading-relaxed">
              从此步骤开始：覆盖任务入口，后续正常流转。<br />
              单步执行：仅执行此步骤，完成后立即结束（忽略跳转）。
            </div>
          </div>
        )}

        {/* Dashboard or Expanded */}
        {expanded === null ? (
          /* ── Dashboard ── */
          <div className="grid grid-cols-2 gap-2">
            {CARDS.map(c => {
              const s = c.summary(step);
              const on = s !== "";
              return (
                <button key={c.key} onClick={() => setExpanded(c.key)}
                  className={`group flex flex-col gap-2 px-3.5 py-3 rounded-xl border border-solid text-left transition-all duration-150 outline-none
                    focus-visible:ring-2 focus-visible:ring-[#1677ff]/20
                    ${on
                      ? "border-[#eef0f2] bg-white hover:border-[#d0d5dd] hover:shadow-sm"
                      : "border-dashed border-[#dde0e6] bg-white/50 hover:border-[#1677ff] hover:bg-[#f0f5ff]"}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: on ? c.color : "#d0d5dd" }} />
                      <span className="text-[11px] font-semibold text-[#1a1a2e]">{c.label}</span>
                    </div>
                    {on && (
                      <span className="w-4 h-4 rounded-full flex items-center justify-center shrink-0"
                        style={{ background: c.light, color: c.color }}>
                        <span className="text-[8px] leading-none font-bold">●</span>
                      </span>
                    )}
                  </div>
                  <div className="flex-1 flex items-center min-w-0">
                    <span className={`text-[10px] leading-tight truncate w-full ${on ? "text-[#6b7280]" : "text-[#c0c4cc]"}`}>
                      {on ? s : c.desc}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          /* ── Expanded section ── */
          card && (
          <div className="rounded-xl border border-[#eef0f2] bg-white overflow-hidden">
            {/* Section header with back button */}
            <div className="flex items-center gap-2 px-3 py-1.5" style={{ background: card.light }}>
              <button onClick={() => setExpanded(null)}
                className="inline-flex items-center gap-0.5 text-[11px] leading-none font-medium transition-colors hover:opacity-70 shrink-0 outline-none border-0 bg-transparent cursor-pointer"
                style={{ color: card.color }}>
                <LeftOutlined className="text-[10px] leading-none align-middle" />
                <span>仪表盘</span>
              </button>
              <span className="text-[10px] leading-none opacity-40" style={{ color: card.color }}>|</span>
              <span className="text-[11px] leading-none font-semibold" style={{ color: card.color }}>{card.label}</span>
              <span className="text-[10px] leading-none text-[#8b8fa3] ml-auto">{card.desc}</span>
            </div>
            {/* Section body */}
            <div className="p-4">
                {expanded === "flow" && (
                  <FlowEditor step={step} stepOpts={[...ctx.taskSteps, ...ctx.taskCommonSteps, ...ctx.globalCommonSteps]} stepName={stepName} onUpdate={onUpdate} />
                )}
                {expanded === "params" && (
                  <ParamsEditor step={step} ctx={ctx} onUpdate={onUpdate} />
                )}
                {(expanded === "prefix" || expanded === "postfix" || expanded === "failure_extra" || expanded === "success_extra") && (
                  <SubListEditor list={(step as any)[expanded] ?? []} ctx={ctx}
                    color={CARDS.find(c => c.key === expanded)!.color}
                    onChange={(v) => onUpdate(expanded, v)} />
                )}
                {expanded === "set" && (
                  <SubListEditor list={step.set ?? []} ctx={ctx} isKeyValue
                    color={CARDS.find(c => c.key === "set")!.color}
                    onChange={(v) => onUpdate("set", v)} />
                )}
                {expanded === "retry" && (
                  <div className="rounded-xl border border-dashed bg-white"
                    style={{ borderColor: "rgba(220,38,38,0.3)", background: "linear-gradient(135deg, rgba(220,38,38,0.04), #fff)" }}>
                    <div className="flex items-center gap-2 px-3.5 py-2.5">
                      <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
                        style={{ background: "rgba(220,38,38,0.1)", color: "#dc2626" }}>
                        <ReloadOutlined />
                      </span>
                      <span className="text-[12px] font-semibold text-[#1a1a2e]">失败重试</span>
                      <span className="text-[10px] text-[#8b8fa3] ml-auto">失败后自动重试</span>
                    </div>
                    <div className="px-3.5 pb-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] text-[#374151] shrink-0 w-[60px]">重试次数</span>
                        <InputNumber size="small" min={0} variant="borderless" className="flex-1"
                          value={step.retry?.times ?? 0}
                          onChange={v => onUpdate("retry", { times: v ?? 0, interval: step.retry?.interval ?? 0 })} />
                        <span className="text-[11px] text-[#c0c4cc] shrink-0">次</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] text-[#374151] shrink-0 w-[60px]">重试间隔</span>
                        <InputNumber size="small" min={0} step={100} variant="borderless" className="flex-1"
                          value={step.retry?.interval ?? 0}
                          onChange={v => onUpdate("retry", { times: step.retry?.times ?? 1, interval: v ?? 0 })} />
                        <span className="text-[11px] text-[#c0c4cc] shrink-0">ms</span>
                      </div>
                      {step.retry?.times ? (
                        <div className="text-[10px] text-[#8b8fa3] leading-relaxed">
                          失败后将自动重试 {step.retry.times} 次，每次间隔 {step.retry.interval ?? 0}ms
                        </div>
                      ) : (
                        <div className="text-[10px] text-[#c0c4cc] leading-relaxed">
                          设为 0 表示不重试，失败后直接终止
                        </div>
                      )}
                    </div>
                  </div>
                )}
                {expanded === "extends" && (
                  <div className="rounded-xl border border-dashed bg-white"
                    style={{ borderColor: "rgba(139,92,246,0.3)", background: "linear-gradient(135deg, rgba(139,92,246,0.04), #fff)" }}>
                    <div className="flex items-center gap-2 px-3.5 py-2.5">
                      <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
                        style={{ background: "rgba(139,92,246,0.1)", color: "#8b5cf6" }}>
                        <ApartmentOutlined />
                      </span>
                      <span className="text-[12px] font-semibold text-[#1a1a2e]">继承模板</span>
                      <span className="text-[10px] text-[#8b8fa3] ml-auto">复用已有步骤配置</span>
                    </div>
                    <div className="px-3.5 pb-3">
                      <Select className="w-full" size="small" allowClear showSearch placeholder="选择一个步骤作为模板"
                        value={step.extends || undefined} popupMatchSelectWidth={false}
                        options={[...ctx.taskSteps, ...ctx.taskCommonSteps, ...ctx.globalCommonSteps].filter(o => o.value !== stepName)}
                        onChange={v => onUpdate("extends", v ?? "")} />
                      {step.extends ? (
                        <div className="text-[10px] text-[#8b8fa3] leading-relaxed mt-2">
                          将继承「{step.extends}」的全部配置，当前步骤的显式设置会覆盖继承值
                        </div>
                      ) : (
                        <div className="text-[10px] text-[#c0c4cc] leading-relaxed mt-2">
                          选择一个步骤以继承其动作与参数配置
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default StepPanel;
