import { type FC } from "react";
import { AutoComplete, Button, Input, InputNumber, Tooltip } from "antd";
import { AimOutlined } from "@ant-design/icons";

const parsePosItem = (v: unknown): string => {
  if (typeof v === "number") return String(v);
  if (typeof v === "string") return v;
  return "0";
};

const parsePos = (v: unknown): [string, string] => {
  try {
    if (Array.isArray(v) && v.length === 2) return [parsePosItem(v[0]), parsePosItem(v[1])];
    if (typeof v === "string") {
      const arr = JSON.parse(v);
      if (Array.isArray(arr) && arr.length === 2) return [parsePosItem(arr[0]), parsePosItem(arr[1])];
    }
  } catch { /* */ }
  return ["0", "0"];
};

interface Props {
  params: Record<string, unknown>;
  onUpdate: (field: string, value: unknown) => void;
  hwnd: string;
  onCoordOpen: () => void;
  paramKey?: string;
  varOptions?: { value: string; label: string }[];
}

const isTemplate = (v: unknown): boolean => typeof v === "string" && v.includes("{");

const PosInput: FC<Props> = ({ params, onUpdate, hwnd, onCoordOpen, paramKey = "pos", varOptions = [] }) => {
  const raw = parsePos(params[paramKey]);
  const posVal = params[paramKey];
  const arr = Array.isArray(posVal) && posVal.length === 2 ? posVal : [0, 0];
  const xTemplate = isTemplate(arr[0]);
  const yTemplate = isTemplate(arr[1]);

  const setPos = (nx: unknown, ny: unknown) => onUpdate("params", { ...params, [paramKey]: [nx, ny] });

  const renderInput = (label: string, val: unknown, isExpr: boolean, onChange: (v: unknown) => void) => {
    const strVal = typeof val === "string" ? val : String(val ?? "0");
    const numVal = typeof val === "number" ? val : Number(val);

    // If value is a template string, always show text input
    if (isExpr || typeof val === "string") {
      return (
        <AutoComplete
          size="small"
          className="flex-1 font-mono text-[12px]"
          value={strVal}
          onChange={(v) => {
            const n = Number(v);
            onChange(v !== "" && !isNaN(n) ? n : (v || 0));
          }}
          options={varOptions}
          placeholder="坐标或{变量}"
          filterOption={(input, option) =>
            option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
          }
        />
      );
    }

    return (
      <InputNumber size="small" variant="borderless" className="flex-1"
        min={0}
        value={isNaN(numVal) ? 0 : numVal}
        onChange={(v) => onChange(v ?? 0)} />
    );
  };

  return (
    <div className="flex-1 flex items-center gap-1.5">
      <span className="text-[10px] text-[#9ca3af] shrink-0">X</span>
      {renderInput("X", arr[0], xTemplate, (v) => setPos(v, arr[1]))}
      <span className="text-[10px] text-[#9ca3af] shrink-0">Y</span>
      {renderInput("Y", arr[1], yTemplate, (v) => setPos(arr[0], v))}
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
