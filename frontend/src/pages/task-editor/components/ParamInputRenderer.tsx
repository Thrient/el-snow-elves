import { AutoComplete, Input, InputNumber, Select } from "antd";
import type { EditorCtx } from "@/types/task-editor/actions";
import PreprocessEditor from "../PreprocessEditor";
import BoxInput from "../BoxInput";
import PosInput from "../PosInput";
import ColorInput from "../ColorInput";
import KeyInput from "@/components/settings-field/components/KeyInput";
import VarOpBuilder from "@/pages/task-editor/components/var-op-builder/VarOpBuilder";

interface ParamInputRendererProps {
  paramKey: string;
  value: unknown;
  params: Record<string, unknown>;
  ctx: EditorCtx;
  onUpdate: (field: string, value: unknown) => void;
  setCoordKey: (key: string | null) => void;
  setBoxOpen: (open: boolean) => void;
  setColorOpen: (open: boolean) => void;
}

const varItems = (ctx: EditorCtx, category: "system" | "config" | "task") => {
  const arr = category === "system" ? ctx.builtinVars : category === "config" ? ctx.configVars : ctx.taskValueVars;
  return arr.map(v => ({ syntax: v.value, label: v.label, category }));
};

const ParamInputRenderer: React.FC<ParamInputRendererProps> = ({
  paramKey: key,
  value,
  params,
  ctx,
  onUpdate,
  setCoordKey,
  setBoxOpen,
  setColorOpen,
}) => {
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
    return <PosInput params={params} onUpdate={onUpdate} hwnd={ctx.hwnd} onCoordOpen={() => setCoordKey(key)} paramKey={key}
      varOptions={[...ctx.builtinVars, ...ctx.configVars, ...ctx.taskValueVars]} />;
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
      <Select size="small" className="w-150px"allowClear
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
        className="w-160px"
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
  if (key === "method") {
    return (
      <Select size="small" className="w-120px"
        value={(value as string) || "ccoeff"}
        options={[
          { value: "ccoeff", label: "ccoeff — 模板" },
          { value: "sift", label: "sift — 特征点" },
        ]}
        onChange={(v) => onUpdate("params", { ...params, method: v })} />
    );
  }
  if (key === "threshold") {
    if (typeof value !== "number" && value != null) {
      const raw = String(value ?? "");
      return (
        <Input size="small" className="font-mono text-[12px] w-80px"
          value={raw}
          onChange={(e) => onUpdate("params", { ...params, threshold: e.target.value })}
          placeholder="0.85" />
      );
    }
    return (
      <InputNumber size="small" className="font-mono text-[12px] w-80px"
        min={0} max={1} step={0.01}
        value={typeof value === "number" ? value : null}
        onChange={(v) => onUpdate("params", { ...params, threshold: v })}
        placeholder="0.85" />
    );
  }
  if (key === "seconds") {
    return (
      <InputNumber size="small" className="font-mono text-[12px] w-80px"
        min={0} step={100}
        value={typeof value === "number" ? value : 0}
        onChange={(v) => onUpdate("params", { ...params, seconds: v === 0 ? null : v })}
        placeholder="1800" />
    );
  }
  if (key === "color") {
    return <ColorInput params={params} onUpdate={onUpdate} hwnd={ctx.hwnd} onColorOpen={() => setColorOpen(true)} />;
  }
  if (key === "tolerance") {
    if (typeof value !== "number" && value != null) {
      const raw = String(value ?? "");
      return (
        <Input size="small" className="font-mono text-[12px] w-80px"
          value={raw}
          onChange={(e) => onUpdate("params", { ...params, tolerance: e.target.value })}
          placeholder="10" />
      );
    }
    return (
      <InputNumber size="small" className="font-mono text-[12px] w-80px"
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
      <Input size="small" className="font-mono text-[12px] w-80px"
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
  if (key === "prompt") {
    return (
      <div className="flex flex-col gap-1 w-full">
        <Input.TextArea
          size="small"
          className="font-mono text-[12px]"
          rows={4}
          value={(value as string) ?? ""}
          onChange={(e) => onUpdate("params", { ...params, prompt: e.target.value })}
          placeholder="告诉 AI 如何分析这张截图，要求返回 JSON 格式"
        />
        <VarOpBuilder
          context="params"
          valueTypes={ctx.valueTypes}
          variables={[...varItems(ctx, "system"), ...varItems(ctx, "config"), ...varItems(ctx, "task")]}
          onInsert={(expr) => {
            const prev = (value as string) ?? "";
            onUpdate("params", { ...params, prompt: prev + expr });
          }}
        />
      </div>
    );
  }
  if (key === "description") {
    return (
      <div className="flex flex-col gap-1 w-full">
        <Input.TextArea
          size="small"
          className="font-mono text-[12px]"
          rows={3}
          value={(value as string) ?? ""}
          onChange={(e) => onUpdate("params", { ...params, description: e.target.value })}
          placeholder="通知正文内容，支持 {变量}"
        />
        <VarOpBuilder
          context="params"
          valueTypes={ctx.valueTypes}
          variables={[...varItems(ctx, "system"), ...varItems(ctx, "config"), ...varItems(ctx, "task")]}
          onInsert={(expr) => {
            const prev = (value as string) ?? "";
            onUpdate("params", { ...params, description: prev + expr });
          }}
        />
      </div>
    );
  }
  if (key === "type") {
    return (
      <Select size="small" className="w-120px"
        value={(value as string) || "info"}
        options={[
          { value: "info", label: "info — 信息" },
          { value: "success", label: "success — 成功" },
          { value: "warning", label: "warning — 警告" },
          { value: "error", label: "error — 错误" },
        ]}
        onChange={(v) => onUpdate("params", { ...params, type: v })} />
    );
  }
  if (key === "duration") {
    return (
      <InputNumber size="small" className="font-mono text-[12px] w-80px"
        min={0} step={100}
        value={typeof value === "number" ? value : null}
        onChange={(v) => onUpdate("params", { ...params, duration: v ?? 500 })}
        placeholder="500" />
    );
  }
  const raw = typeof value === "string" ? value : JSON.stringify(value ?? "");
  return (
    <div className="flex items-center gap-1">
      <Input size="small" className="font-mono text-[12px] w-140px"
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

export default ParamInputRenderer;
