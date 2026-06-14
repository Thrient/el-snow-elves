import { useState, useEffect, type FC } from "react";
import { Button, Modal, message, Spin } from "antd";
import { HighlightOutlined } from "@ant-design/icons";
import CaptureZoom, { useCaptureZoom } from "../CaptureZoom";

interface CaptureResult { base64: string; width: number; height: number; }

interface Props {
  open: boolean;
  hwnd: string;
  onClose: () => void;
  onPick: (x1: number, y1: number, x2: number, y2: number) => void;
}

const BoxPickerModal: FC<Props> = ({ open, hwnd, onClose, onPick }) => {
  const [loading, setLoading] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [rect, setRect] = useState<{ x1: number; y1: number; x2: number; y2: number } | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [start, setStart] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (!open || !hwnd) return;
    setLoading(true);
    setCapture(null);
    setRect(null);
    setStart(null);
    setDrawing(false);
    window.pywebview?.api.emit("API:TEMPLATE:CAPTURE", hwnd)
      .then((r: CaptureResult | null) => { if (r) setCapture(r); })
      .catch(() => message.error("截图失败"))
      .finally(() => setLoading(false));
  }, [open, hwnd]);

  const handleConfirm = () => {
    if (rect) { onPick(rect.x1, rect.y1, rect.x2, rect.y2); onClose(); }
  };

  return (
    <Modal title="框选区域" open={open} onCancel={onClose} centered width={780}
      footer={
        <div className="flex justify-between">
          <span className="text-[11px] text-[#9ca3af] self-center">
            {rect ? `已选: [${rect.x1}, ${rect.y1}, ${rect.x2}, ${rect.y2}]` : "拖拽鼠标框选区域"}
          </span>
          <div className="flex gap-2">
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" disabled={!rect} onClick={handleConfirm}>确认</Button>
          </div>
        </div>
      }>
      <Spin spinning={loading}>
        {capture ? (
          <CaptureZoom capture={capture} tools={[{ key: "box", label: "框选", shortcut: "B", icon: <HighlightOutlined /> }]}>
            <BoxOverlay
              onRectChange={(r) => setRect(r)}
              onDrawingChange={setDrawing}
              onStartChange={setStart}
              drawing={drawing}
              start={start}
              rect={rect}
            />
          </CaptureZoom>
        ) : !loading ? (
          <div className="flex items-center justify-center h-[200px] text-[#9ca3af] text-sm">
            无法加载截图
          </div>
        ) : null}
      </Spin>
    </Modal>
  );
};

// Inner component so it has access to useCaptureZoom context
const BoxOverlay: FC<{
  onRectChange: (r: { x1: number; y1: number; x2: number; y2: number } | null) => void;
  onDrawingChange: (d: boolean) => void;
  onStartChange: (s: { x: number; y: number } | null) => void;
  drawing: boolean;
  start: { x: number; y: number } | null;
  rect: { x1: number; y1: number; x2: number; y2: number } | null;
}> = ({ onRectChange, onDrawingChange, onStartChange, drawing, start, rect }) => {
  const { capture, toImgCoords, tool } = useCaptureZoom();

  const handleMouseDown = (e: React.MouseEvent) => {
    if (tool !== "box") return;
    const c = toImgCoords(e.clientX, e.clientY);
    if (!c) return;
    onStartChange(c);
    onDrawingChange(true);
    onRectChange(null);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!drawing || !start) return;
    const c = toImgCoords(e.clientX, e.clientY);
    if (!c) return;
    onRectChange({
      x1: Math.min(start.x, c.x),
      y1: Math.min(start.y, c.y),
      x2: Math.max(start.x, c.x),
      y2: Math.max(start.y, c.y),
    });
  };

  const handleMouseUp = () => {
    onDrawingChange(false);
    onStartChange(null);
  };

  const rectStyle = rect
    ? { left: `${(rect.x1 / capture.width) * 100}%`, top: `${(rect.y1 / capture.height) * 100}%`, width: `${((rect.x2 - rect.x1) / capture.width) * 100}%`, height: `${((rect.y2 - rect.y1) / capture.height) * 100}%` }
    : undefined;

  return (
    <div className="absolute inset-0 cursor-crosshair"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}>
      {rect && rectStyle && (
        <div className="absolute pointer-events-none border-2 border-[#1677ff] bg-[#1677ff]/15"
          style={rectStyle} />
      )}
    </div>
  );
};

export default BoxPickerModal;
