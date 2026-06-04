import { useState, useEffect, useRef, type FC } from "react";
import { Button, Modal, message, Spin } from "antd";

interface CaptureResult { base64: string; width: number; height: number; }

interface Props {
  open: boolean;
  hwnd: string;
  onClose: () => void;
  onPick: (x: number, y: number) => void;
}

const CoordPickerModal: FC<Props> = ({ open, hwnd, onClose, onPick }) => {
  const [loading, setLoading] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [marker, setMarker] = useState<{ x: number; y: number } | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!open || !hwnd) return;
    setLoading(true);
    setCapture(null);
    setMarker(null);
    window.pywebview?.api.emit("API:TEMPLATE:CAPTURE", hwnd)
      .then((r: CaptureResult | null) => { if (r) setCapture(r); })
      .catch(() => message.error("截图失败"))
      .finally(() => setLoading(false));
  }, [open, hwnd]);

  const handleClick = (e: React.MouseEvent<HTMLImageElement>) => {
    const img = imgRef.current;
    if (!img || !capture) return;
    const rect = img.getBoundingClientRect();
    const scaleX = capture.width / rect.width;
    const scaleY = capture.height / rect.height;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);
    setMarker({ x, y });
  };

  const handleConfirm = () => {
    if (marker) { onPick(marker.x, marker.y); onClose(); }
  };

  return (
    <Modal title="选取坐标" open={open} onCancel={onClose}
      footer={
        <div className="flex justify-between">
          <span className="text-[11px] text-[#9ca3af] self-center">
            {marker ? `已选: [${marker.x}, ${marker.y}]` : "点击截图选取坐标"}
          </span>
          <div className="flex gap-2">
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" disabled={!marker} onClick={handleConfirm}>确认</Button>
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
              {marker && (
                <div
                  className="absolute pointer-events-none"
                  style={{
                    left: `${(marker.x / capture.width) * 100}%`,
                    top: `${(marker.y / capture.height) * 100}%`,
                    transform: "translate(-50%, -50%)",
                  }}
                >
                  <svg width="28" height="28" viewBox="-14 -14 28 28">
                    <circle cx="0" cy="0" r="6" fill="none" stroke="#ff4d4f" strokeWidth="2" />
                    <line x1="-12" y1="0" x2="12" y2="0" stroke="#ff4d4f" strokeWidth="2" />
                    <line x1="0" y1="-12" x2="0" y2="12" stroke="#ff4d4f" strokeWidth="2" />
                  </svg>
                </div>
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

export default CoordPickerModal;
