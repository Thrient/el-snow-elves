import { useState, useEffect, useRef, useCallback, type FC } from "react";
import { Button, Modal, message, Spin } from "antd";

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
  const imgRef = useRef<HTMLImageElement>(null);

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

  const imgCoords = useCallback((e: React.MouseEvent) => {
    const img = imgRef.current;
    if (!img || !capture) return null;
    const r = img.getBoundingClientRect();
    return {
      x: Math.round((e.clientX - r.left) * capture.width / r.width),
      y: Math.round((e.clientY - r.top) * capture.height / r.height),
    };
  }, [capture]);

  const handleMouseDown = (e: React.MouseEvent) => {
    const c = imgCoords(e);
    if (!c) return;
    setStart(c);
    setDrawing(true);
    setRect(null);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!drawing || !start) return;
    const c = imgCoords(e);
    if (!c) return;
    setRect({
      x1: Math.min(start.x, c.x),
      y1: Math.min(start.y, c.y),
      x2: Math.max(start.x, c.x),
      y2: Math.max(start.y, c.y),
    });
  };

  const handleMouseUp = () => {
    setDrawing(false);
    setStart(null);
  };

  const handleConfirm = () => {
    if (rect) { onPick(rect.x1, rect.y1, rect.x2, rect.y2); onClose(); }
  };

  const rectStyle = rect && capture
    ? { left: `${(rect.x1 / capture.width) * 100}%`, top: `${(rect.y1 / capture.height) * 100}%`, width: `${((rect.x2 - rect.x1) / capture.width) * 100}%`, height: `${((rect.y2 - rect.y1) / capture.height) * 100}%` }
    : undefined;

  return (
    <Modal title="框选区域" open={open} onCancel={onClose}
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
      }
      width={Math.min((capture?.width ?? 800) + 48, 860)}>
      <Spin spinning={loading}>
        <div className="flex items-center justify-center min-h-[200px] bg-[#f0f2f5] rounded-lg overflow-hidden select-none">
          {capture ? (
            <div className="relative inline-block cursor-crosshair"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}>
              <img ref={imgRef} src={capture.base64} className="max-w-full max-h-[65vh] block" draggable={false} />
              {rect && rectStyle && (
                <div className="absolute pointer-events-none border-2 border-[#1677ff] bg-[#1677ff]/15"
                  style={rectStyle} />
              )}
            </div>
          ) : !loading ? (
            <span className="text-[#9ca3af] text-sm">无法加载截图</span>
          ) : null}
        </div>
      </Spin>
    </Modal>
  );
};

export default BoxPickerModal;
