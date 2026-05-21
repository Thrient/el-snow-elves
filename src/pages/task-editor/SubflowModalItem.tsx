import { useMemo, type FC } from "react";
import { Button, Input, InputNumber, Popover, Select } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import type { EditorCtx } from "./constants";
import VarOpBuilder from "@/components/var-op-builder/VarOpBuilder";
import { extractAllParams } from "@/utils/expression";

interface Props {
  index: number; item: any; ctx: EditorCtx; arr: any[]; color?: string; onChange: (v: any[]) => void;
}

const SubflowModalItem: FC<Props> = ({ index: i, item, ctx, arr, color = "#9ca3af", onChange }) => {
  const stepName = typeof item === "string" ? item : item.step;
  const itemWhen = typeof item === "object" ? (item.when ?? "") : "";
  const argsObj = typeof item === "object" && item.args && typeof item.args === "object"
    ? item.args as Record<string, unknown> : undefined;
  const argsEntries = argsObj ? Object.entries(argsObj) : [];
  const argsCount = argsEntries.filter(([k]) => k).length;
  const repeatMatch = stepName.match(/^(.+)\*(\d+)$/);
  const baseName = repeatMatch ? repeatMatch[1] : stepName;
  const repeatCount = repeatMatch ? parseInt(repeatMatch[2]) : 1;

  /** Get default params for a step — stepParamsMap cache or recursive transitive scan */
  const getStepDefaults = (name: string): Record<string, unknown> =>
    ctx.stepParamsMap[name] ?? extractAllParams(name, ctx.allStepsData);

  const updateItem = (updater: (o: any) => any) => {
    const u = [...arr];
    u[i] = updater(typeof u[i] === "string" ? { step: u[i] } : { ...u[i] });
    onChange(u);
  };
  const setArgs = (entries: [string, unknown][]) => {
    if (entries.length === 0) { updateItem((o) => { o.args = undefined; return o; }); return; }
    const obj: Record<string, unknown> = {};
    for (const [k, v] of entries) if (k) obj[k] = v;
    updateItem((o) => { o.args = Object.keys(obj).length > 0 ? obj : undefined; return o; });
  };
  const handleStepChange = (v: string | undefined) => {
    const newBase = v ?? "";
    updateItem((o) => {
      o.step = repeatCount > 1 && v ? `${v}*${repeatCount}` : newBase;
      // Always replace args with new step's defaults (or clear if none)
      const def = getStepDefaults(newBase);
      o.args = Object.keys(def).length > 0 ? { ...def } : undefined;
      return o;
    });
  };

  const stepParamKeys = useMemo(() => {
    const def = getStepDefaults(baseName);
    return Object.keys(def).map((k) => ({ value: k, label: k }));
  }, [ctx.stepParamsMap, ctx.allStepsData, baseName]);

  return (
    <div className="group rounded-xl border border-dashed bg-white transition-colors flex-1 min-w-0"
      style={{ borderColor: `${color}4d`, background: `linear-gradient(135deg, ${color}0a, #fff)` }}>
      <div className="flex items-center gap-1.5 px-4 py-2.5">
        <span className="w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-semibold shrink-0"
          style={{ background: `${color}18`, color }}>{i + 1}</span>
        <Select size="small" variant="borderless" className="flex-1 min-w-0 font-semibold" showSearch allowClear
          placeholder="选择步骤" value={baseName || undefined} popupMatchSelectWidth={false}
          options={[...ctx.taskSteps, ...ctx.taskCommonSteps, ...ctx.globalCommonSteps]} onChange={handleStepChange} />
        <div className="flex items-center gap-1 shrink-0 ml-auto">
          <span className="text-[10px] text-[#9ca3af]">×</span>
          <InputNumber size="small" variant="borderless" min={1} max={99} style={{ width: 36 }} value={repeatCount}
            onChange={(v) => updateItem((o) => { o.step = v && v > 1 ? `${baseName}*${v}` : baseName; return o; })} />
          {/* when — VarOpBuilder */}
          <VarOpBuilder
            context="when"
            valueTypes={ctx.valueTypes}
            variables={[
              ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
              ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
              ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
            ]}
            value={itemWhen}
            onInsert={(expr) => updateItem((o) => { o.when = expr; return o; })}
          >
            <span className={`text-[10px] px-1.5 py-0.5 rounded cursor-pointer shrink-0 border transition-colors inline-block text-center min-w-[40px]
              ${itemWhen ? "border-[#d4513b] bg-[#fef3ef] text-[#d4513b] font-medium" : "border-dashed border-[#d0d5dd] text-[#9ca3af] hover:border-[#d4513b] hover:text-[#d4513b]"}`}>
              when{itemWhen ? "*" : ""}
            </span>
          </VarOpBuilder>
        {/* args */}
        {argsCount > 0 ? (
          <Popover trigger="click" placement="bottomRight"
            overlayInnerStyle={{ padding: 0, borderRadius: 12, boxShadow: "0 8px 40px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04)" }}
            content={
              <div className="flex flex-col select-none" style={{ width: 380 }}>
                {/* ── Header ── */}
                <div className="px-5 pt-4 pb-3 flex items-center gap-3">
                  <span className="text-xs font-bold tracking-tight text-[#171717]">args</span>
                  <span className="text-[10px] font-medium tracking-wide uppercase text-[#a8a29e] bg-[#f5f5f4] px-2 py-0.5 rounded-md">参数覆盖</span>
                  <div className="flex-1" />
                  <span className="shrink-0 text-[11px] font-bold tabular-nums min-w-[22px] h-[22px] flex items-center justify-center rounded-lg text-white"
                    style={{ background: "linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)", boxShadow: "0 2px 6px rgba(99,102,241,0.3)" }}>
                    {argsCount}
                  </span>
                </div>

                {/* ── Divider ── */}
                <div className="mx-5 h-px" style={{ background: "linear-gradient(to right, #e5e7eb, #f5f5f5, transparent)" }} />

                {/* ── Parameter rows ── */}
                <div className="px-5 py-4">
                  <div className="flex flex-col gap-2">
                    {argsEntries.map(([key, val], ei) => {
                      const defaults = getStepDefaults(baseName);
                      const defaultVal = defaults[key];
                      const isModified = !!key && key in defaults && val !== defaultVal;
                      return (
                        <div key={ei} className="relative flex items-center rounded-xl overflow-hidden transition-all duration-200 hover:shadow-md"
                          style={{
                            background: isModified ? "#fffdf7" : "#fafafa",
                            border: `1.5px solid ${isModified ? "#fbbf24" : "#e5e7eb"}`,
                            boxShadow: isModified ? "0 2px 8px rgba(251,191,36,0.12)" : "0 1px 2px rgba(0,0,0,0.04)",
                          }}
                        >
                          {isModified && (
                            <span className="absolute left-0 top-1 bottom-1 w-[4px] rounded-r-full" style={{ background: "linear-gradient(180deg, #f59e0b, #fbbf24, #f59e0b)" }} />
                          )}
                          <Input
                            size="small"
                            variant="borderless"
                            className="!text-[11px]"
                            style={{
                              flex: 1, minWidth: 56, borderRadius: 0, fontWeight: 700,
                              paddingLeft: isModified ? 14 : 12, paddingRight: 0,
                              color: isModified ? "#92400e" : "#404040",
                            }}
                            placeholder="参数名"
                            value={key || ""}
                            onChange={(e) => {
                              const next = [...argsEntries];
                              next[ei] = [e.target.value, val];
                              setArgs(next);
                            }}
                          />
                          <span className="shrink-0 text-xs font-bold select-none px-1"
                            style={{ color: isModified ? "#f59e0b" : "#d4d4d8" }}>
                            =
                          </span>
                          <Input
                            size="small"
                            variant="borderless"
                            className="!text-[11px]"
                            style={{
                              flex: 1.5, minWidth: 80, borderRadius: 0,
                              fontFamily: "ui-monospace, SF Mono, Consolas, 'Liberation Mono', monospace",
                              fontSize: 11, paddingRight: 4,
                              color: isModified ? "#78350f" : "#262626",
                            }}
                            placeholder={typeof defaultVal === "string" ? defaultVal : "值"}
                            value={typeof val === "string" ? val : JSON.stringify(val)}
                            onChange={(e) => {
                              const next = [...argsEntries];
                              next[ei] = [key, e.target.value];
                              setArgs(next);
                            }}
                          />
                          <div className="shrink-0 pr-2">
                            <VarOpBuilder
                              context="args"
                              valueTypes={ctx.valueTypes}
                              variables={[
                                ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
                                ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
                                ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
                              ]}
                              onInsert={(expr) => { const next = [...argsEntries]; next[ei] = [key, expr]; setArgs(next); }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            }>
            <span className="text-[10px] px-1.5 py-0.5 rounded-md cursor-pointer shrink-0 border border-transparent bg-[#4f46e5] text-white font-bold shadow-sm shadow-indigo-200 hover:bg-[#4338ca] transition-all duration-200 inline-flex items-center gap-1 text-center select-none">
              <span>args</span>
              <span className="tabular-nums opacity-80">{argsCount}</span>
            </span>
          </Popover>
        ) : null}
          <Button type="text" size="small"
            className="!text-[#c0c4cc] hover:!text-[#dc2626] opacity-0 group-hover:opacity-100 transition-all shrink-0"
            onClick={() => { const u = [...arr]; u.splice(i, 1); onChange(u); }}><DeleteOutlined className="text-[11px]" /></Button>
        </div>
      </div>
    </div>
  );
};

export default SubflowModalItem;
