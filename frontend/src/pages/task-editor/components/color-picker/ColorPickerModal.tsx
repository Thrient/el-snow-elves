import { useState, useEffect, useRef, type FC } from "react";
import { Button, Modal, message, Spin } from "antd";
import { BgColorsOutlined } from "@ant-design/icons";
import CaptureZoom, { useCaptureZoom } from "../CaptureZoom";

interface CaptureResult { base64: string; width: number; height: number; }

interface Props {
  open: boolean;
  hwnd: string;
  onClose: () => void;
  onPick: (r: number, g: number, b: number) => void;
}

function getPixel(img: HTMLImageElement, canvas: HTMLCanvasElement | null, sx: number, sy: number) {
  if (!canvas) return null;
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.drawImage(img, 0, 0);
  const [r, g, b] = ctx.getImageData(Math.round(sx), Math.round(sy), 1, 1).data;
  return { r, g, b };
}

const ColorPickerModal: FC<Props> = ({ open, hwnd, onClose, onPick }) => {
  const [loading, setLoading] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [picked, setPicked] = useState<{ x: number; y: number; r: number; g: number; b: number } | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!open || !hwnd) return;
    setLoading(true);
    setCapture(null);
    setPicked(null);
    window.pywebview?.api.emit("API:TEMPLATE:CAPTURE:PNG", hwnd)
      .then((r: CaptureResult | null) => { if (r) setCapture(r); })
      .catch(() => message.error("截图失败"))
      .finally(() => setLoading(false));
  }, [open, hwnd]);

  const handleConfirm = () => {
    if (picked) { onPick(picked.r, picked.g, picked.b); onClose(); }
  };

  const swatch = picked ? `rgb(${picked.r},${picked.g},${picked.b})` : "transparent";

  return (
    <Modal title="取色" open={open} onCancel={onClose} centered width={780}
      footer={
        <div className="flex justify-between">
          <div className="flex items-center gap-2">
            {picked ? (
              <>
                <span className="inline-block w-5 h-5 rounded border border-[#d0d5dd]" style={{ background: swatch }} />
                <span className="text-[11px] text-secondary font-mono">[{picked.r}, {picked.g}, {picked.b}]</span>
                <span className="text-[10px] text-[#9ca3af]">@{picked.x},{picked.y}</span>
              </>
            ) : (
              <span className="text-[11px] text-[#9ca3af]">点击截图选取颜色</span>
            )}
          </div>
          <div className="flex gap-2">
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" disabled={!picked} onClick={handleConfirm}>确认</Button>
          </div>
        </div>
      }>
      <Spin spinning={loading}>
        <canvas ref={canvasRef} hidden />
        {capture ? (
          <CaptureZoom capture={capture} tools={[{ key: "color", label: "取色", shortcut: "C", icon: <BgColorsOutlined /> }]}>
            <ColorPickerOverlay
              canvasRef={canvasRef}
              picked={picked}
              capture={capture}
              onPick={(p) => setPicked(p)}
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

const ColorPickerOverlay: FC<{
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  picked: { x: number; y: number; r: number; g: number; b: number } | null;
  capture: CaptureResult;
  onPick: (p: { x: number; y: number; r: number; g: number; b: number }) => void;
}> = ({ canvasRef, picked, capture, onPick }) => {
  const { imgRef, toImgCoords, tool } = useCaptureZoom();

  const handleClick = (e: React.MouseEvent) => {
    if (tool !== "color") return;
    const img = imgRef.current;
    if (!img) return;
    const coords = toImgCoords(e.clientX, e.clientY);
    if (!coords) return;
    const pix = getPixel(img, canvasRef.current, coords.x, coords.y);
    if (pix) onPick({ x: coords.x, y: coords.y, ...pix });
  };

  return (
    <div className="absolute inset-0 cursor-crosshair" onClick={handleClick}>
      {picked && (
        <div
          className="absolute pointer-events-none"
          style={{
            left: `${(picked.x / capture.width) * 100}%`,
            top: `${(picked.y / capture.height) * 100}%`,
            transform: "translate(-50%, -50%)",
          }}
        >
          <svg width="28" height="28" viewBox="-14 -14 28 28">
            <circle cx="0" cy="0" r="6" fill={`rgb(${picked.r},${picked.g},${picked.b})`} stroke="#fff" strokeWidth="2" />
            <circle cx="0" cy="0" r="8" fill="none" stroke="#ff4d4f" strokeWidth="2" />
          </svg>
        </div>
      )}
    </div>
  );
};

export default ColorPickerModal;
