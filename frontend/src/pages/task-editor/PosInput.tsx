import { type FC } from "react";
import { AutoComplete, Button, Tooltip } from "antd";
import { AimOutlined } from "@ant-design/icons";
import VarOpBuilder from "./components/var-op-builder/VarOpBuilder";

const toStr = (v: unknown): string => {
  if (typeof v === "string") return v;
  if (typeof v === "number") return String(v);
  return "0";
};

const parsePos = (v: unknown): [string, string] => {
  try {
    if (Array.isArray(v) && v.length === 2) return [toStr(v[0]), toStr(v[1])];
    if (typeof v === "string") {
      const arr = JSON.parse(v);
      if (Array.isArray(arr) && arr.length === 2) return [toStr(arr[0]), toStr(arr[1])];
    }
  } catch { /* */ }
  return ["0", "0"];
};

const tryCoerce = (v: string): unknown => {
  if (v === "") return 0;
  const n = Number(v);
  return !isNaN(n) ? n : v;
};

interface Props {
  params: Record<string, unknown>;
  onUpdate: (field: string, value: unknown) => void;
  hwnd: string;
  onCoordOpen: () => void;
  paramKey?: string;
  varOptions?: { value: string; label: string }[];
  valueTypes?: Record<string, string>;
}

const PosInput: FC<Props> = ({ params, onUpdate, hwnd, onCoordOpen, paramKey = "pos", varOptions = [], valueTypes = {} }) => {
  const posVal = params[paramKey];
  const arr = Array.isArray(posVal) && posVal.length === 2 ? posVal : [0, 0];
  const [xStr, yStr] = parsePos(posVal);

  const setPos = (nx: unknown, ny: unknown) => onUpdate("params", { ...params, [paramKey]: [nx, ny] });

  const varItems = (category: "system" | "config" | "task") => {
    // We use the raw varOptions with labels — extract syntax from them
    return varOptions.filter(o => {
      if (category === "system") return o.value === "{result}" || o.value === "{hwnd}" || o.value === "{ChildHwnd}";
      if (category === "config") return o.value.startsWith("{CONFIG.");
      return !o.value.startsWith("{CONFIG.") && o.value !== "{result}" && o.value !== "{hwnd}" && o.value !== "{ChildHwnd}";
    }).map(v => ({ syntax: v.value, label: v.label, category }));
  };

  return (
    <div className="flex-1 flex items-center gap-1.5">
      <span className="text-[10px] text-[#9ca3af] shrink-0">X</span>
      <AutoComplete
        size="small"
        className="flex-1 font-mono text-[12px]"
        value={xStr}
        onChange={(v) => setPos(tryCoerce(v), arr[1])}
        options={varOptions}
        placeholder="x 坐标"
        openOnFocus
        filterOption={(input, option) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
        }
      />
      <VarOpBuilder
        context="params"
        valueTypes={valueTypes}
        variables={[...varItems("system"), ...varItems("config"), ...varItems("task")]}
        onInsert={(expr) => setPos(toStr(arr[0]) + expr, arr[1])}
      />
      <span className="text-[10px] text-[#9ca3af] shrink-0">Y</span>
      <AutoComplete
        size="small"
        className="flex-1 font-mono text-[12px]"
        value={yStr}
        onChange={(v) => setPos(arr[0], tryCoerce(v))}
        options={varOptions}
        placeholder="y 坐标"
        openOnFocus
        filterOption={(input, option) =>
          option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
        }
      />
      <VarOpBuilder
        context="params"
        valueTypes={valueTypes}
        variables={[...varItems("system"), ...varItems("config"), ...varItems("task")]}
        onInsert={(expr) => setPos(arr[0], toStr(arr[1]) + expr)}
      />
      <Tooltip title={hwnd ? "从截图中选取坐标" : "请先在主界面选择窗口"}>
        <Button type="text" size="small" disabled={!hwnd}
          className="!text-[#9ca3af] hover:!text-[#3b82f6] shrink-0"
          onClick={(e) => { e.stopPropagation(); onCoordOpen(); }}
          icon={<AimOutlined className="text-[13px]" />} />
      </Tooltip>
    </div>
  );
};

export default PosInput;
