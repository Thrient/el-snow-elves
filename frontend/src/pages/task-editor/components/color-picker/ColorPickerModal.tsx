import { useState, useEffect, useRef, type FC } from "react";
import { Button, Modal, message, Spin } from "antd";

interface CaptureResult { base64: string; width: number; height: number; }

interface Props {
  open: boolean;
  hwnd: string;
  onClose: () => void;
  onPick: (r: number, g: number, b: number) => void;
}

const ColorPickerModal: FC<Props> = ({ open, hwnd, onClose, onPick }) => {
  const [loading, setLoading] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [picked, setPicked] = useState<{ x: number; y: number; r: number; g: number; b: number } | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
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

  const getPixel = (img: HTMLImageElement, sx: number, sy: number, scaleX: number, scaleY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const px = Math.round(sx * scaleX);
    const py = Math.round(sy * scaleY);
    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(img, 0, 0);
    const [r, g, b] = ctx.getImageData(px, py, 1, 1).data;
    return { r, g, b };
  };

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const img = imgRef.current;
    if (!img || !capture) return;
    const rect = img.getBoundingClientRect();
    const scaleX = capture.width / rect.width;
    const scaleY = capture.height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);
    const pix = getPixel(img, x, y, 1, 1);
    if (pix) setPicked({ x, y, ...pix });
  };

  const handleConfirm = () => {
    if (picked) { onPick(picked.r, picked.g, picked.b); onClose(); }
  };

  const swatch = picked ? `rgb(${picked.r},${picked.g},${picked.b})` : "transparent";

  return (
    <Modal title="取色" open={open} onCancel={onClose}
      footer={
        <div className="flex justify-between">
          <div className="flex items-center gap-2">
            {picked ? (
              <>
                <span className="inline-block w-5 h-5 rounded border border-[#d0d5dd]" style={{ background: swatch }} />
                <span className="text-[11px] text-secondary font-mono">
                  [{picked.r}, {picked.g}, {picked.b}]
                </span>
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
      }
      width={Math.min((capture?.width ?? 800) + 48, 860)}>
      <Spin spinning={loading}>
        <div className="flex items-center justify-center min-h-[200px] bg-[#f0f2f5] rounded-lg overflow-hidden relative select-none">
          {capture ? (
            <div className="relative inline-block">
              <img
                ref={imgRef}
                src={capture.base64}
                className="max-w-full max-h-[65vh] block cursor-crosshair"
                onClick={handleClick}
                draggable={false}
              />
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
                    <circle cx="0" cy="0" r="6" fill={swatch} stroke="#fff" strokeWidth="2" />
                    <circle cx="0" cy="0" r="8" fill="none" stroke="#ff4d4f" strokeWidth="2" />
                  </svg>
                </div>
              )}
            </div>
          ) : !loading ? (
            <span className="text-[#9ca3af] text-sm">无法加载截图</span>
          ) : null}
        </div>
        <canvas ref={canvasRef} hidden />
      </Spin>
    </Modal>
  );
};

export default ColorPickerModal;
