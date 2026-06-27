import { type FC } from "react";
import { AutoComplete, Button, InputNumber, Tooltip } from "antd";
import { AimOutlined } from "@ant-design/icons";
import VarOpBuilder from "./components/var-op-builder/VarOpBuilder";

const isExpr = (v: unknown): boolean => typeof v === "string" && v.includes("{");

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

  const setPos = (nx: unknown, ny: unknown) => onUpdate("params", { ...params, [paramKey]: [nx, ny] });

  const varItems = (category: "system" | "config" | "task") =>
    varOptions.filter(o => {
      if (category === "system") return o.value === "{result}" || o.value === "{hwnd}" || o.value === "{ChildHwnd}";
      if (category === "config") return o.value.startsWith("{CONFIG.");
      return !o.value.startsWith("{CONFIG.") && o.value !== "{result}" && o.value !== "{hwnd}" && o.value !== "{ChildHwnd}";
    }).map(v => ({ syntax: v.value, label: v.label, category }));

  const renderOne = (val: unknown, onChange: (v: unknown) => void) => {
    if (isExpr(val)) {
      return (
        <AutoComplete
          size="small"
          className="flex-1 font-mono text-[12px]"
          value={val as string}
          onChange={(v) => {
            const n = Number(v);
            onChange(v !== "" && !isNaN(n) ? n : (v || 0));
          }}
          options={varOptions}
          placeholder="{变量}"
          openOnFocus
          filterOption={(input, option) =>
            option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
          }
        />
      );
    }
    return (
      <InputNumber size="small" variant="borderless" className="flex-1" min={0}
        value={typeof val === "number" ? val : 0}
        onChange={(v) => onChange(v ?? 0)} />
    );
  };

  return (
    <div className="flex-1 flex items-center gap-1.5">
      <span className="text-[10px] text-[#9ca3af] shrink-0">X</span>
      {renderOne(arr[0], (v) => setPos(v, arr[1]))}
      <VarOpBuilder
        context="params"
        valueTypes={valueTypes}
        variables={[...varItems("system"), ...varItems("config"), ...varItems("task")]}
        onInsert={(expr) => setPos(expr, arr[1])}
      />
      <span className="text-[10px] text-[#9ca3af] shrink-0">Y</span>
      {renderOne(arr[1], (v) => setPos(arr[0], v))}
      <VarOpBuilder
        context="params"
        valueTypes={valueTypes}
        variables={[...varItems("system"), ...varItems("config"), ...varItems("task")]}
        onInsert={(expr) => setPos(arr[0], expr)}
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
