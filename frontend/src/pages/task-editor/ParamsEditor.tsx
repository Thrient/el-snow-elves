import { useState, useEffect, type FC } from "react";
import { Select, Tooltip } from "antd";
import { PictureOutlined } from "@ant-design/icons";
import type { Step } from "@/types/task";
import type { EditorCtx } from "@/types/task-editor/actions";
import { ACTIONS_WITH_TEMPLATES, ACTION_PARAMS, PARAM_META, REQUIRED_PARAMS, PARAM_DEFAULTS } from "@/types/task-editor/actions";
import BoxPickerModal from "@/pages/task-editor/components/box-picker/BoxPickerModal";
import CoordPickerModal from "@/pages/task-editor/components/coord-picker/CoordPickerModal";
import ColorPickerModal from "@/pages/task-editor/components/color-picker/ColorPickerModal";
import ParamInputRenderer from "./components/ParamInputRenderer";
import VarOpBuilder from "./components/var-op-builder/VarOpBuilder";

interface ParamsEditorProps {
  step: Step;
  ctx: EditorCtx;
  onUpdate: (field: string, value: unknown) => void;
}

const ParamsEditor: FC<ParamsEditorProps> = ({ step, ctx, onUpdate }) => {
  const [coordKey, setCoordKey] = useState<string | null>(null);
  const [boxOpen, setBoxOpen] = useState(false);
  const [colorOpen, setColorOpen] = useState(false);
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
  const isVarMode = args.length === 1 && /^\{.+\}$/.test(args[0]);

  const varItems = (category: "system" | "config" | "task") => {
    const arr = category === "system" ? ctx.builtinVars : category === "config" ? ctx.configVars : ctx.taskValueVars;
    return arr.map(v => ({ syntax: v.value, label: v.label, category }));
  };
  const allowed = step.action ? (ACTION_PARAMS[step.action] ?? []) : [];

  useEffect(() => {
    const missing = required.filter(k => params[k] === undefined);
    if (missing.length > 0) {
      const p = { ...params };
      for (const k of missing) p[k] = k === "args" ? [] : (PARAM_DEFAULTS[k] ?? "");
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

  const renderInput = (key: string) => (
    <ParamInputRenderer
      paramKey={key}
      value={params[key]}
      params={params}
      ctx={ctx}
      onUpdate={onUpdate}
      setCoordKey={setCoordKey}
      setBoxOpen={setBoxOpen}
      setColorOpen={setColorOpen}
    />
  );

  return (
    <div className="space-y-2.5">
      {showArgs && (
        <div className="rounded-xl border border-dashed bg-container"
          style={{ borderColor: "rgba(59,130,246,0.25)", background: "linear-gradient(135deg, rgba(59,130,246,0.04), #fff)" }}>
          <div className="flex items-center gap-2 px-3.5 py-2.5">
            <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
              style={{ background: "rgba(59,130,246,0.1)", color: "#3b82f6" }}>
              <PictureOutlined />
            </span>
            <span className="text-[12px] font-semibold text-heading">模板图片</span>
            <Tooltip title="模板图片名列表，不含路径和 .bmp 后缀。支持 {变量} 嵌入" placement="top">
              <span className="text-[10px] text-[#c0c4cc] cursor-help hover:text-secondary">?</span>
            </Tooltip>
            <span className="text-[10px] text-muted ml-auto">输入图片名后回车添加</span>
          </div>
          <div className="px-3.5 pb-3">
            <div className="flex items-center gap-1">
              <Select mode="tags" className="flex-1" size="small"
                allowClear
                placeholder="输入图片名回车添加，如 按钮登录"
                value={args}
                options={templateOptions}
                filterOption={(input, option) => (option?.label as string ?? "").toLowerCase().includes(input.toLowerCase())}
                onChange={(v) => {
                  if (isVarMode && (v as string[]).length > args.length) return;
                  onUpdate("params", { ...params, args: v });
                }} />
              <VarOpBuilder
                key={`${ctx.taskName}-${ctx.version}-${ctx.refreshKey}`}
                context="params"
                valueTypes={ctx.valueTypes}
                variables={[...varItems("system"), ...varItems("config"), ...varItems("task")]}
                onInsert={(expr) => onUpdate("params", { ...params, args: [expr] })} />
            </div>
          </div>
        </div>
      )}

      {other.map(key => {
        const meta = PARAM_META[key];
        if (key === "preprocess") {
          return <div key={key}>{renderInput(key)}</div>;
        }
        const accentColor = meta?.color ?? "#9ca3af";
        if (key === "pos" || key === "start_pos" || key === "end_pos" || key === "box" || key === "color" || key === "key" || key === "hwnd" || key === "text" || key === "prompt") {
          return (
            <div key={key} className="group rounded-xl border border-dashed bg-container transition-colors"
              style={{ borderColor: `${accentColor}4d`, background: `linear-gradient(135deg, ${accentColor}0a, #fff)` }}>
              <div className="flex items-center justify-between px-3.5 py-2">
                <Tooltip title={meta?.tip || meta?.desc} placement="left">
                  <div className="flex items-center gap-1.5 cursor-help">
                    <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0" style={{ background: `${accentColor}18`, color: accentColor, fontSize: "13px" }}>
                      {meta?.icon}
                    </span>
                    <span className="text-[12px] text-body select-none">{meta?.label ?? key}</span>
                  </div>
                </Tooltip>
                <button onClick={() => { const p = { ...params }; delete p[key]; onUpdate("params", p); }}
                  className="text-[#c0c4cc] hover:text-[#ff4d4f] opacity-0 group-hover:opacity-100 transition-all text-xs shrink-0 border-0 bg-transparent cursor-pointer">×</button>
              </div>
              <div className="px-3.5 pb-2.5">
                {renderInput(key)}
              </div>
            </div>
          );
        }
        return (
          <div key={key} className="group rounded-xl border border-dashed bg-container transition-colors"
            style={{ borderColor: `${accentColor}4d`, background: `linear-gradient(135deg, ${accentColor}0a, #fff)` }}>
            <div className="flex items-center justify-between px-3.5 py-2">
              <Tooltip title={meta?.tip || meta?.desc} placement="left">
                <div className="flex items-center gap-1.5 cursor-help min-w-0">
                  <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0" style={{ background: `${accentColor}18`, color: accentColor, fontSize: "13px" }}>
                    {meta?.icon}
                  </span>
                  <span className="text-[12px] text-body select-none truncate">{meta?.label ?? key}</span>
                  {meta?.range && (
                    <span className="text-[10px] text-[#c0c4cc] font-mono shrink-0 hidden sm:inline">{meta.range}</span>
                  )}
                </div>
              </Tooltip>
              <div className="flex items-center gap-1.5 shrink-0">
                {renderInput(key)}
                <button onClick={() => { const p = { ...params }; delete p[key]; onUpdate("params", p); }}
                  className="text-[#c0c4cc] hover:text-[#ff4d4f] opacity-0 group-hover:opacity-100 transition-all text-xs border-0 bg-transparent cursor-pointer">×</button>
              </div>
            </div>
          </div>
        );
      })}

      {canAdd.length > 0 && (
        <div className="rounded-xl border border-dashed bg-container"
          style={{ borderColor: "rgba(148,163,184,0.3)", background: "linear-gradient(135deg, rgba(148,163,184,0.03), #fff)" }}>
          <div className="flex items-center gap-2 px-3.5 py-2">
            <span className="text-[11px] font-medium text-muted shrink-0">添加参数</span>
            <span className="h-px flex-1" style={{ background: "linear-gradient(to right, #e5e7eb, transparent)" }} />
          </div>
          <div className="px-3.5 pb-3 flex flex-wrap gap-1.5">
          {canAdd.map(k => {
            const meta = PARAM_META[k];
            const accent = meta?.color ?? "#9ca3af";
            return (
              <Tooltip key={k} title={meta?.desc}>
                <button onClick={() => onUpdate("params", { ...params, [k]: PARAM_DEFAULTS[k] ?? "" })}
                  className="inline-flex items-center gap-1.5 text-[11px] px-2.5 py-1.5 rounded-lg border border-dashed border-[#dde0e6] text-secondary bg-container hover:text-[#1677ff] hover:border-[#1677ff] hover:shadow-sm transition-all cursor-pointer border-0 bg-transparent"
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
      {ctx.hwnd && <CoordPickerModal open={coordKey !== null} hwnd={ctx.hwnd}
        onClose={() => setCoordKey(null)}
        onPick={(x, y) => { if (coordKey) onUpdate("params", { ...params, [coordKey]: [x, y] }); setCoordKey(null); }} />}
      {ctx.hwnd && <BoxPickerModal open={boxOpen} hwnd={ctx.hwnd}
        onClose={() => setBoxOpen(false)}
        onPick={(x1, y1, x2, y2) => onUpdate("params", { ...params, box: [x1, y1, x2, y2] })} />}
      {ctx.hwnd && <ColorPickerModal open={colorOpen} hwnd={ctx.hwnd}
        onClose={() => setColorOpen(false)}
        onPick={(r, g, b) => onUpdate("params", { ...params, color: [r, g, b] })} />}
    </div>
  );
};

export default ParamsEditor;
