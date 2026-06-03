import { type FC } from "react";
import { Button, InputNumber, Tooltip } from "antd";
import { AimOutlined } from "@ant-design/icons";

const parsePos = (v: unknown): [number, number] => {
  try {
    if (Array.isArray(v) && v.length === 2) return [Number(v[0]), Number(v[1])];
    if (typeof v === "string") {
      const arr = JSON.parse(v);
      if (Array.isArray(arr) && arr.length === 2) return [Number(arr[0]), Number(arr[1])];
    }
  } catch { /* */ }
  return [0, 0];
};

interface Props {
  params: Record<string, unknown>;
  onUpdate: (field: string, value: unknown) => void;
  hwnd: string;
  onCoordOpen: () => void;
  paramKey?: string;
}

const PosInput: FC<Props> = ({ params, onUpdate, hwnd, onCoordOpen, paramKey = "pos" }) => {
  const [x, y] = parsePos(params[paramKey]);
  const setPos = (nx: number, ny: number) => onUpdate("params", { ...params, [paramKey]: [nx, ny] });

  return (
    <div className="flex-1 flex items-center gap-1.5">
      <span className="text-[10px] text-[#9ca3af] shrink-0">X</span>
      <InputNumber size="small" variant="borderless" className="flex-1" min={0}
        value={x} onChange={(v) => setPos(v ?? 0, y)} />
      <span className="text-[10px] text-[#9ca3af] shrink-0">Y</span>
      <InputNumber size="small" variant="borderless" className="flex-1" min={0}
        value={y} onChange={(v) => setPos(x, v ?? 0)} />
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
