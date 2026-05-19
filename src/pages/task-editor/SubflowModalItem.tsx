import { useMemo, type FC } from "react";
import { AutoComplete, Button, InputNumber, Popover, Select } from "antd";
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

  const varOnlyOptions = useMemo(
    () => [...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars],
    [ctx.builtinVars, ctx.configVars, ctx.taskValueVars],
  );
  const allOptions = useMemo(
    () => [...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars,
           ...ctx.taskSteps, ...ctx.taskCommonSteps, ...ctx.globalCommonSteps],
    [ctx.builtinVars, ctx.configVars, ctx.taskValueVars,
     ctx.taskSteps, ctx.taskCommonSteps, ctx.globalCommonSteps],
  );

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
            variables={[
              ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
              ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
              ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
            ]}
            value={itemWhen}
            onInsert={(expr) => updateItem((o) => { o.when = expr; return o; })}
          >
            <span className={`text-[10px] px-1.5 py-0.5 rounded cursor-pointer shrink-0 border transition-colors inline-block text-center min-w-[40px]
              ${itemWhen ? "border-[#6366f1] bg-[#eef2ff] text-[#6366f1] font-medium" : "border-dashed border-[#d0d5dd] text-[#9ca3af] hover:border-[#6366f1] hover:text-[#6366f1]"}`}>
              when{itemWhen ? "*" : ""}
            </span>
          </VarOpBuilder>
        {/* args */}
        {stepParamKeys.length > 0 || argsCount > 0 ? (
          <Popover trigger="click" placement="bottomRight"
            content={
              <div className="flex flex-col" style={{ width: 340, gap: 10 }}>
                {/* Header */}
                <div className="flex items-center gap-2">
                  <div className="w-1 h-4 rounded-full" style={{ background: "#1677ff" }} />
                  <span className="text-xs font-semibold" style={{ color: "#3d3630" }}>args 参数</span>
                  {argsCount > 0 && (
                    <span className="text-[10px] font-medium px-1.5 py-px rounded" style={{ background: "#eef2ff", color: "#3b82f6" }}>
                      {argsCount}
                    </span>
                  )}
                  <span className="text-[10px] ml-auto" style={{ color: "#b8afa6" }}>覆盖默认值</span>
                </div>

                {/* Param rows */}
                <div className="flex flex-col" style={{ gap: 6 }}>
                  {argsEntries.map(([key, val], ei) => {
                    const defaults = getStepDefaults(baseName);
                    const defaultVal = defaults[key];
                    const isModified = !!key && val !== defaultVal;
                    return (
                      <div key={ei}
                        className="flex items-stretch rounded-lg border bg-white transition-all duration-150 overflow-hidden"
                        style={{ borderColor: isModified ? "#d4513b33" : "#e8e3dc" }}
                      >
                        {/* Key */}
                        <AutoComplete
                          size="small"
                          variant="borderless"
                          className="font-medium"
                          style={{ flex: "1 1 0", minWidth: 60, borderRadius: 0, paddingLeft: 10 }}
                          placeholder="参数名"
                          value={key || undefined}
                          options={stepParamKeys}
                          filterOption={(iv, opt) => opt?.label?.toLowerCase().includes(iv.toLowerCase()) ?? false}
                          onChange={(v) => {
                            const d = getStepDefaults(baseName)[v ?? ""];
                            const next = [...argsEntries];
                            next[ei] = [v ?? "", d !== undefined ? (typeof d === "string" ? d : String(d)) : val];
                            setArgs(next);
                          }}
                        />
                        {/* Divider */}
                        <div style={{ width: 1, background: "#e8e3dc", flexShrink: 0, margin: "4px 0" }} />
                        {/* = */}
                        <span className="flex items-center justify-center text-[10px] shrink-0"
                          style={{ width: 20, color: isModified ? "#d4513b" : "#b8afa6", fontWeight: isModified ? 600 : 400 }}>
                          =
                        </span>
                        {/* Divider */}
                        <div style={{ width: 1, background: "#e8e3dc", flexShrink: 0, margin: "4px 0" }} />
                        {/* Value */}
                        <AutoComplete
                          size="small"
                          variant="borderless"
                          style={{ flex: "1 1 0", minWidth: 60, borderRadius: 0, fontFamily: "monospace", fontSize: 12 }}
                          placeholder={typeof defaultVal === "string" ? `默认: ${defaultVal}` : "值"}
                          value={typeof val === "string" ? val : JSON.stringify(val)}
                          options={allOptions}
                          filterOption={(iv, opt) => opt?.label?.toLowerCase().includes(iv.toLowerCase()) ?? false}
                          onChange={(v) => { const next = [...argsEntries]; next[ei] = [key, v]; setArgs(next); }}
                        />
                        {/* Variable picker button */}
                        <VarOpBuilder
                          context="args"
                          variables={[
                            ...ctx.builtinVars.map(v => ({ syntax: v.value, label: v.label, category: "system" as const })),
                            ...ctx.configVars.map(v => ({ syntax: v.value, label: v.label, category: "config" as const })),
                            ...ctx.taskValueVars.map(v => ({ syntax: v.value, label: v.label, category: "task" as const })),
                          ]}
                          onInsert={(expr) => { const next = [...argsEntries]; next[ei] = [key, expr]; setArgs(next); }}
                        >
                          <button className="shrink-0 flex items-center justify-center text-xs transition-all duration-150 outline-none border-0 bg-transparent cursor-pointer"
                            style={{ width: 18, height: 18, color: "#c4bbb2", fontSize: 11 }}
                            onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}
                          >fx</button>
                        </VarOpBuilder>
                        {/* Modified indicator */}
                        {isModified && (
                          <div style={{ width: 3, background: "#d4513b", flexShrink: 0 }} />
                        )}
                        {/* Remove */}
                        <button
                          className="shrink-0 flex items-center justify-center text-xs transition-all duration-150 outline-none border-0 bg-transparent cursor-pointer"
                          style={{ width: 26, color: "#c4bbb2" }}
                          onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
                          onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}
                          onClick={() => {
                            if (argsEntries.length <= 1) setArgs([]);
                            else {
                              const next = [...argsEntries]; next.splice(ei, 1); setArgs(next);
                            }
                          }}
                        >
                          ×
                        </button>
                      </div>
                    );
                  })}
                </div>

                {argsEntries.length === 0 && (
                  <div className="text-center py-2 text-[11px]" style={{ color: "#c4bbb2" }}>
                    此步骤无模板参数
                  </div>
                )}
              </div>
            }>
            <span className={`text-[10px] px-1.5 py-0.5 rounded cursor-pointer shrink-0 border transition-colors inline-block text-center min-w-[40px]
              ${argsCount > 0 ? "border-[#1677ff] bg-[#eef2ff] text-[#1677ff] font-medium"
                : "border-dashed border-[#d0d5dd] text-[#9ca3af] hover:border-[#1677ff] hover:text-[#1677ff]"}`}>
              {argsCount > 0 ? `args ${argsCount}` : "args"}
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
