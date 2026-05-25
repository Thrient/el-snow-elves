import { useState, type FC } from "react";
import { Button, Input, InputNumber, Select, Tooltip, message } from "antd";
import { CloseOutlined, CopyOutlined, DeleteOutlined, LeftOutlined, BugOutlined, ReloadOutlined, ApartmentOutlined } from "@ant-design/icons";
import type { Step } from "@/types/task";
import type { EditorCtx } from "./constants";
import { ACTION_OPTS, ACTION_PARAMS, REQUIRED_PARAMS } from "./constants";
import FlowEditor from "./FlowEditor";
import ParamsEditor from "./ParamsEditor";
import SubListEditor from "./SubListEditor";
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
  onCopy?: () => void;
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

// ---- Main ----

const StepPanel: FC<Props> = ({ stepName, step, isCommon, ctx, onClose, onRename, onUpdate, onDelete, onCopy }) => {
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
        {onCopy && (
          <Tooltip title="复制步骤"><Button type="text" size="small" icon={<CopyOutlined />} onClick={onCopy} /></Tooltip>
        )}
        <Tooltip title="删除步骤"><Button type="text" size="small" danger icon={<DeleteOutlined />} onClick={onDelete} /></Tooltip>
        <Tooltip title="关闭面板"><Button type="text" size="small" icon={<CloseOutlined />} onClick={onClose} /></Tooltip>
      </div>

      {/* ── Body ── */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4 thin-scrollbar">

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
                  if (!(k in clean)) clean[k] = k === "args" ? [] : "";
                }
                const updated = { ...step, action: newAction, params: clean };
                useEditorStore.getState().updateStep(stepName, updated, isCommon);
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
                valueTypes={ctx.valueTypes}
                variables={[
                  ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
                  ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
                  ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
                ]}
                onInsert={(expr) => onUpdate("action", expr)}
              />
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
