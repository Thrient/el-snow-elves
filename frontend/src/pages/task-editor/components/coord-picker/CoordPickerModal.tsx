import { useState, useEffect, type FC } from "react";
import { Button, Modal, message, Spin } from "antd";
import { PushpinOutlined } from "@ant-design/icons";
import CaptureZoom, { useCaptureZoom } from "../CaptureZoom";

interface CaptureResult { base64: string; width: number; height: number; }

interface Props {
  open: boolean;
  hwnd: string;
  onClose: () => void;
  onPick: (x: number, y: number) => void;
}

/* Inner component that reads CaptureZoom context for click-to-pick */
const CaptureOverlay: FC<{
  marker: { x: number; y: number } | null;
  setMarker: (m: { x: number; y: number }) => void;
  capture: CaptureResult;
}> = ({ marker, setMarker, capture }) => {
  const { toImgCoords, tool } = useCaptureZoom();

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (tool !== "coord") return;
    const coords = toImgCoords(e.clientX, e.clientY);
    if (coords) setMarker(coords);
  };

  return (
    <div
      className={`absolute inset-0 ${tool === "coord" ? "cursor-crosshair" : ""}`}
      onClick={handleClick}
    >
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
  );
};

const CoordPickerModal: FC<Props> = ({ open, hwnd, onClose, onPick }) => {
  const [loading, setLoading] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [marker, setMarker] = useState<{ x: number; y: number } | null>(null);

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

  const handleConfirm = () => {
    if (marker) { onPick(marker.x, marker.y); onClose(); }
  };

  return (
    <Modal title="选取坐标" open={open} onCancel={onClose} centered width={780}
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
      }>
      <Spin spinning={loading}>
        {capture ? (
          <CaptureZoom
            capture={capture}
            tools={[{ key: "coord", label: "选坐标", shortcut: "P", icon: <PushpinOutlined /> }]}
          >
            <CaptureOverlay marker={marker} setMarker={setMarker} capture={capture} />
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

export default CoordPickerModal;
