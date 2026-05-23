import { useState, useEffect, type FC } from "react";
import { AutoComplete, Input, InputNumber, Select, Tooltip } from "antd";
import { PictureOutlined } from "@ant-design/icons";
import type { Step } from "@/types/task";
import type { EditorCtx } from "./constants";
import { ACTIONS_WITH_TEMPLATES, ACTION_PARAMS, PARAM_META, REQUIRED_PARAMS } from "./constants";
import ColorInput from "./ColorInput";
import PosInput from "./PosInput";
import BoxInput from "./BoxInput";
import BoxPickerModal from "@/components/box-picker/BoxPickerModal";
import PreprocessEditor from "./PreprocessEditor";
import KeyInput from "@/components/settings-field/components/KeyInput";
import CoordPickerModal from "@/components/coord-picker/CoordPickerModal";
import ColorPickerModal from "@/components/color-picker/ColorPickerModal";
import VarOpBuilder from "@/components/var-op-builder/VarOpBuilder";

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
  const allowed = step.action ? (ACTION_PARAMS[step.action] ?? []) : [];

  useEffect(() => {
    const missing = required.filter(k => params[k] === undefined);
    if (missing.length > 0) {
      const p = { ...params };
      for (const k of missing) p[k] = k === "args" ? [] : "";
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

  const varItems = (ctx: EditorCtx, category: "system" | "config" | "task") => {
    const arr = category === "system" ? ctx.builtinVars : category === "config" ? ctx.configVars : ctx.taskValueVars;
    return arr.map(v => ({ syntax: v.value, label: v.label, category }));
  };

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
    if (key === "pos" || key === "start_pos" || key === "end_pos") {
      return <PosInput params={params} onUpdate={onUpdate} hwnd={ctx.hwnd} onCoordOpen={() => setCoordKey(key)} paramKey={key} />;
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
            valueTypes={ctx.valueTypes}
            variables={[...varItems(ctx, "system"), ...varItems(ctx, "config"), ...varItems(ctx, "task")]}
            onInsert={(expr) => onUpdate("params", { ...params, text: (value as string ?? "") + expr })}
          />
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
    if (key === "threshold") {
      if (typeof value !== "number" && value != null) {
        const raw = String(value ?? "");
        return (
          <Input size="small" className="font-mono text-[12px]" style={{ width: 80 }}
            value={raw}
            onChange={(e) => onUpdate("params", { ...params, threshold: e.target.value })}
            placeholder="0.85" />
        );
      }
      return (
        <InputNumber size="small" className="font-mono text-[12px]" style={{ width: 80 }}
          min={0} max={1} step={0.01}
          value={typeof value === "number" ? value : null}
          onChange={(v) => onUpdate("params", { ...params, threshold: v })}
          placeholder="0.85" />
      );
    }
    if (key === "seconds") {
      return (
        <InputNumber size="small" className="font-mono text-[12px]" style={{ width: 80 }}
          min={0} step={0.1}
          value={typeof value === "number" ? value : null}
          onChange={(v) => onUpdate("params", { ...params, seconds: v === 0 ? null : v })}
          placeholder="1.8" />
      );
    }
    if (key === "color") {
      return <ColorInput params={params} onUpdate={onUpdate} hwnd={ctx.hwnd} onColorOpen={() => setColorOpen(true)} />;
    }
    if (key === "tolerance") {
      if (typeof value !== "number" && value != null) {
        const raw = String(value ?? "");
        return (
          <Input size="small" className="font-mono text-[12px]" style={{ width: 80 }}
            value={raw}
            onChange={(e) => onUpdate("params", { ...params, tolerance: e.target.value })}
            placeholder="10" />
        );
      }
      return (
        <InputNumber size="small" className="font-mono text-[12px]" style={{ width: 80 }}
          min={0} max={255}
          value={typeof value === "number" ? value : null}
          onChange={(v) => onUpdate("params", { ...params, tolerance: v })}
          placeholder="10" />
      );
    }
    if (key === "k" || key === "count" || key === "x" || key === "y" ||
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
          valueTypes={ctx.valueTypes}
          variables={[...varItems(ctx, "system"), ...varItems(ctx, "config"), ...varItems(ctx, "task")]}
          onInsert={(expr) => {
            let newVal = (typeof value === "string" ? value : JSON.stringify(value ?? "")) + expr;
            const n = Number(newVal);
            if (newVal !== "" && !isNaN(n)) newVal = String(n);
            onUpdate("params", { ...params, [key]: newVal });
          }}
        />
      </div>
    );
  };

  return (
    <div className="space-y-2.5">
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

      {other.map(key => {
        const meta = PARAM_META[key];
        if (key === "preprocess") {
          return <div key={key}>{renderParamInput(key, params[key])}</div>;
        }
        const accentColor = meta?.color ?? "#9ca3af";
        if (key === "pos" || key === "start_pos" || key === "end_pos" || key === "box" || key === "color" || key === "key" || key === "hwnd" || key === "text") {
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
