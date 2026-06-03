import { type FC } from "react";
import { Button, InputNumber, Tooltip } from "antd";
import { BorderOutlined } from "@ant-design/icons";

const parseBox = (v: unknown): [number, number, number, number] => {
  try {
    if (Array.isArray(v) && v.length === 4) return [Number(v[0]), Number(v[1]), Number(v[2]), Number(v[3])];
    if (typeof v === "string") {
      const arr = JSON.parse(v);
      if (Array.isArray(arr) && arr.length === 4) return [Number(arr[0]), Number(arr[1]), Number(arr[2]), Number(arr[3])];
    }
  } catch { /* */ }
  return [0, 0, 1335, 750];
};

interface Props {
  params: Record<string, unknown>;
  onUpdate: (field: string, value: unknown) => void;
  hwnd: string;
  onBoxOpen: () => void;
}

const BoxInput: FC<Props> = ({ params, onUpdate, hwnd, onBoxOpen }) => {
  const [x1, y1, x2, y2] = parseBox(params.box);
  const setBox = (nx1: number, ny1: number, nx2: number, ny2: number) =>
    onUpdate("params", { ...params, box: [nx1, ny1, nx2, ny2] });

  return (
    <div className="flex-1 flex items-center gap-1">
      <span className="text-[10px] text-[#9ca3af] shrink-0">X1</span>
      <InputNumber size="small" variant="borderless" className="flex-1 min-w-0" min={0}
        value={x1} onChange={(v) => setBox(v ?? 0, y1, x2, y2)} />
      <span className="text-[10px] text-[#9ca3af] shrink-0">Y1</span>
      <InputNumber size="small" variant="borderless" className="flex-1 min-w-0" min={0}
        value={y1} onChange={(v) => setBox(x1, v ?? 0, x2, y2)} />
      <span className="text-[10px] text-[#9ca3af] shrink-0">X2</span>
      <InputNumber size="small" variant="borderless" className="flex-1 min-w-0" min={0}
        value={x2} onChange={(v) => setBox(x1, y1, v ?? 0, y2)} />
      <span className="text-[10px] text-[#9ca3af] shrink-0">Y2</span>
      <InputNumber size="small" variant="borderless" className="flex-1 min-w-0" min={0}
        value={y2} onChange={(v) => setBox(x1, y1, x2, v ?? 0)} />
      <Tooltip title={hwnd ? "从截图中框选区域" : "请先在主界面选择窗口"}>
        <Button type="text" size="small" disabled={!hwnd}
          className="!text-[#9ca3af] hover:!text-[#ec4899] shrink-0"
          onClick={(e) => { e.stopPropagation(); onBoxOpen(); }}
          icon={<BorderOutlined className="text-[13px]" />} />
      </Tooltip>
    </div>
  );
};

export default BoxInput;
