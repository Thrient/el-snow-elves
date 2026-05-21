import { type FC } from "react";
import { Button, Input, InputNumber } from "antd";
import { BgColorsOutlined } from "@ant-design/icons";

interface Props {
  params: Record<string, unknown>;
  onUpdate: (field: string, value: unknown) => void;
  hwnd: string;
  onColorOpen: () => void;
}

const ColorInput: FC<Props> = ({ params, onUpdate, hwnd, onColorOpen }) => {
  const val = params.color;

  // string → variable expression, show text input
  if (typeof val === "string") {
    return (
      <div className="flex-1 flex items-center gap-1.5">
        <Input size="small" className="font-mono text-[12px] flex-1" variant="borderless"
          value={val}
          onChange={(e) => onUpdate("params", { ...params, color: e.target.value })}
          placeholder="[255, 0, 0] 或 {my_color}" />
        {hwnd && (
          <Button type="text" size="small"
            className="!text-[#9ca3af] hover:!text-[#06b6d4] shrink-0"
            onClick={(e) => { e.stopPropagation(); onColorOpen(); }}
            icon={<BgColorsOutlined className="text-[13px]" />} />
        )}
      </div>
    );
  }

  // array → [R, G, B] number inputs
  const rgb = (Array.isArray(val) && val.length === 3) ? val.map(Number) as number[] : [0, 0, 0];
  const setColor = (i: number, v: number | null) => {
    const next = [...rgb];
    next[i] = v ?? 0;
    onUpdate("params", { ...params, color: next });
  };

  return (
    <div className="flex-1 flex items-center gap-1.5">
      {(["R", "G", "B"] as const).map((ch, i) => (
        <div key={ch} className="flex items-center gap-0.5 flex-1">
          <span className="text-[10px] text-[#9ca3af] shrink-0">{ch}</span>
          <InputNumber size="small" variant="borderless" className="flex-1" min={0} max={255}
            value={rgb[i]} onChange={(v) => setColor(i, v)} />
        </div>
      ))}
      <Button type="text" size="small" disabled={!hwnd}
        className="!text-[#9ca3af] hover:!text-[#06b6d4] shrink-0"
        onClick={(e) => { e.stopPropagation(); onColorOpen(); }}
        icon={<BgColorsOutlined className="text-[13px]" />} />
    </div>
  );
};

export default ColorInput;
