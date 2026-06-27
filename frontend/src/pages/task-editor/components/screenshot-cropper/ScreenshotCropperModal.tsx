import { useState, useRef, useCallback, useEffect, type FC } from "react";
import { Button, Input, InputNumber, message, Modal, Popover, Radio } from "antd";
import {
  ScissorOutlined, HighlightOutlined,
  ExperimentOutlined, SwapOutlined,
} from "@ant-design/icons";
import type { PreprocessConfig } from "@/pages/task-editor/PreprocessEditor";
import PreprocessConfigPanel from "@/pages/task-editor/components/preprocess-config-panel/PreprocessConfigPanel";
import CaptureZoom, { useCaptureZoom } from "../CaptureZoom";

/* ============================================================
   CaptureZoom-based architecture:
   - Image rendered by CaptureZoom (zoom, scroll, wheel handled)
   - Overlay / hit-test in original image pixel coords via toImgCoords
   - Pan is handled by CaptureZoom's built-in viewport drag
   - Selection tool: S key
   ============================================================ */

interface Props { open: boolean; hwnd: string; taskName?: string; version?: string; author?: string;
  onClose: () => void; onSaved: (filename: string) => void; }
interface CaptureResult { base64: string; width: number; height: number; }
interface CropRect { x: number; y: number; w: number; h: number; }
type Corner = "nw" | "ne" | "sw" | "se";
type DragMode = "none" | "create" | "move-crop" | `resize-${Corner}`;

const HANDLE_HIT = 22;
const HANDLE_VISUAL = 12;
const MIN_CROP = 8;
const CORNERS: { corner: Corner; cursor: string }[] = [
  { corner: "nw", cursor: "nwse-resize" },
  { corner: "ne", cursor: "nesw-resize" },
  { corner: "sw", cursor: "nesw-resize" },
  { corner: "se", cursor: "nwse-resize" },
];

// ---- Pure utilities (no component closure) ----

const clampCrop = (c: CropRect, capture: CaptureResult) => {
  const x = Math.max(0, Math.min(c.x, capture.width - MIN_CROP));
  const y = Math.max(0, Math.min(c.y, capture.height - MIN_CROP));
  return {
    x, y,
    w: Math.max(MIN_CROP, Math.min(c.w, capture.width - x)),
    h: Math.max(MIN_CROP, Math.min(c.h, capture.height - y)),
  };
};

const getCornerImgPos = (crop: CropRect, corner: Corner) => {
  switch (corner) {
    case "nw": return { x: crop.x, y: crop.y };
    case "ne": return { x: crop.x + crop.w, y: crop.y };
    case "sw": return { x: crop.x, y: crop.y + crop.h };
    case "se": return { x: crop.x + crop.w, y: crop.y + crop.h };
  }
};

// Clamp hit radius so corner zones don't overlap even at tiny zoom levels.
// zoom parameter here is the "real" zoom factor (displayed_px / image_px).
// toImgCoords already returns image pixels, so hit-test zoom is 1 for image-px coords.
const cornerHitRadius = () => Math.max(HANDLE_HIT, 6);

const hitTest = (ix: number, iy: number, crop: CropRect | null): DragMode => {
  if (!crop) return "create";
  const hw = cornerHitRadius();
  for (const { corner } of CORNERS) {
    const pos = getCornerImgPos(crop, corner);
    if (Math.abs(ix - pos.x) <= hw && Math.abs(iy - pos.y) <= hw) return `resize-${corner}`;
  }
  if (ix > crop.x && ix < crop.x + crop.w && iy > crop.y && iy < crop.y + crop.h) return "move-crop";
  return "create";
};

// ---- Percentage-based CropOverlay ----

const CropOverlay: FC<{ crop: CropRect; capture: CaptureResult }> = ({ crop, capture }) => {
  const pctX = (v: number) => (v / capture.width * 100).toFixed(2) + "%";
  const pctY = (v: number) => (v / capture.height * 100).toFixed(2) + "%";

  const l = crop.x / capture.width * 100;
  const t = crop.y / capture.height * 100;
  const w = crop.w / capture.width * 100;
  const h = crop.h / capture.height * 100;

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 5 }}>
      {/* Dim overlays — four rectangles surrounding the crop area */}
      <div style={{
        position: "absolute", left: 0, top: 0, width: "100%", height: `${t}%`,
        background: "rgba(0,0,0,0.55)",
      }} />
      <div style={{
        position: "absolute", left: 0, top: `${t + h}%`, width: "100%",
        height: `${Math.max(0, 100 - t - h)}%`, background: "rgba(0,0,0,0.55)",
      }} />
      <div style={{
        position: "absolute", left: 0, top: `${t}%`, width: `${l}%`, height: `${h}%`,
        background: "rgba(0,0,0,0.55)",
      }} />
      <div style={{
        position: "absolute", left: `${l + w}%`, top: `${t}%`,
        width: `${Math.max(0, 100 - l - w)}%`, height: `${h}%`,
        background: "rgba(0,0,0,0.55)",
      }} />

      {/* Rule-of-thirds grid lines */}
      <div style={{
        position: "absolute", left: `${l}%`, top: `${t + h * (1 / 3)}%`,
        width: `${w}%`, height: 1, background: "rgba(255,255,255,0.22)",
      }} />
      <div style={{
        position: "absolute", left: `${l}%`, top: `${t + h * (2 / 3)}%`,
        width: `${w}%`, height: 1, background: "rgba(255,255,255,0.22)",
      }} />
      <div style={{
        position: "absolute", left: `${l + w * (1 / 3)}%`, top: `${t}%`,
        width: 1, height: `${h}%`, background: "rgba(255,255,255,0.22)",
      }} />
      <div style={{
        position: "absolute", left: `${l + w * (2 / 3)}%`, top: `${t}%`,
        width: 1, height: `${h}%`, background: "rgba(255,255,255,0.22)",
      }} />

      {/* Selection border */}
      <div style={{
        position: "absolute", left: `${l}%`, top: `${t}%`, width: `${w}%`, height: `${h}%`,
        outline: "2px solid #1677ff",
        boxShadow: "0 0 0 1px rgba(22,119,255,0.25), 0 0 12px rgba(22,119,255,0.15), inset 0 0 0 1px rgba(255,255,255,0.08)",
      }} />

      {/* Dimension label — above the selection */}
      <div style={{
        position: "absolute", left: `${l}%`, top: `calc(${t}% - 26px)`, zIndex: 10,
        fontSize: 11, fontWeight: 500, background: "#1677ff", color: "#fff",
        padding: "2px 8px", borderRadius: 4, whiteSpace: "nowrap",
      }}>
        {Math.round(crop.w)} x {Math.round(crop.h)}
      </div>

      {/* Four corner resize handles */}
      {CORNERS.map(({ corner, cursor }) => {
        const pos = getCornerImgPos(crop, corner);
        return (
          <div key={corner} style={{
            position: "absolute", zIndex: 10,
            left: `calc(${pctX(pos.x)} - ${HANDLE_VISUAL / 2}px)`,
            top: `calc(${pctY(pos.y)} - ${HANDLE_VISUAL / 2}px)`,
            width: HANDLE_VISUAL, height: HANDLE_VISUAL, borderRadius: 3,
            background: "#fff", border: "2px solid #1677ff",
            boxShadow: "0 1px 4px rgba(0,0,0,0.25), 0 0 0 1px rgba(22,119,255,0.2)",
            cursor,
          }} />
        );
      })}
    </div>
  );
};

// ---- Save confirm modal ----

const SaveModal: FC<{
  open: boolean; saving: boolean; filename: string; crop: CropRect | null;
  onFilename: (v: string) => void; onOk: () => void; onCancel: () => void;
}> = ({ open, saving, filename, crop, onFilename, onOk, onCancel }) => (
  <Modal title={<span className="text-sm font-semibold text-heading">保存模板图片</span>}
    open={open} onOk={onOk} onCancel={onCancel} centered
    okText="保存" cancelText="取消" confirmLoading={saving}
    okButtonProps={{ disabled: !filename.trim() }}
    width={400}
  >
    <div className="flex flex-col gap-4 pt-1">
      <div className="flex flex-col gap-1.5">
        <span className="text-[11px] font-medium text-secondary">文件名</span>
        <Input placeholder="输入模板图片名" value={filename}
          onChange={e => onFilename(e.target.value)}
          suffix={<span className="text-[10px] text-[#9ca3af]">.bmp</span>}
          className="!text-sm" />
      </div>
      {crop && (
        <div className="flex items-center gap-3 px-3 py-2.5 bg-[#f8f9fb] rounded-lg border border-[#eef0f2]">
          <span className="text-[11px] text-muted">选区尺寸</span>
          <span className="text-xs font-medium text-heading">{Math.round(crop.w)} x {Math.round(crop.h)} px</span>
        </div>
      )}
    </div>
  </Modal>
);

// ---- Mouse event handler (rendered inside CaptureZoom for useCaptureZoom()) ----
// Pan is handled by CaptureZoom's built-in viewport drag — no separate pan tool needed.

const MouseHandler: FC<{
  capture: CaptureResult;
  crop: CropRect | null;
  onCropChange: (c: CropRect | null) => void;
}> = ({ capture: cap, crop, onCropChange }) => {
  const { toImgCoords } = useCaptureZoom();
  const localDragStartImg = useRef({ x: 0, y: 0 });
  const localDragMode = useRef<DragMode>("none");
  const localCropSnap = useRef<CropRect | null>(null);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.button === 1 || e.button === 2) { onCropChange(null); return; }
    if (e.button !== 0) return;

    const img = toImgCoords(e.clientX, e.clientY);
    if (!img) return;
    localDragStartImg.current = img;

    localDragMode.current = hitTest(img.x, img.y, crop);
    localCropSnap.current = crop ? { ...crop } : null;
  }, [toImgCoords, onCropChange, crop]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (localDragMode.current === "none") return;

    const curImg = toImgCoords(e.clientX, e.clientY);
    if (!curImg) return;
    const sImg = localDragStartImg.current;
    const snap = localCropSnap.current;

    if (localDragMode.current === "create") {
      const x = Math.min(sImg.x, curImg.x);
      const y = Math.min(sImg.y, curImg.y);
      const w = Math.abs(curImg.x - sImg.x);
      const h = Math.abs(curImg.y - sImg.y);
      if (w >= MIN_CROP || h >= MIN_CROP) {
        onCropChange(clampCrop({ x, y, w, h }, cap));
      }
      return;
    }

    if (!snap) return;
    const dxi = curImg.x - sImg.x;
    const dyi = curImg.y - sImg.y;

    if (localDragMode.current === "move-crop") {
      onCropChange(clampCrop({ x: snap.x + dxi, y: snap.y + dyi, w: snap.w, h: snap.h }, cap));
      return;
    }

    if (localDragMode.current.startsWith("resize-")) {
      const corner = localDragMode.current.replace("resize-", "") as Corner;
      let newCrop: CropRect;
      switch (corner) {
        case "nw": newCrop = { x: snap.x + dxi, y: snap.y + dyi, w: snap.w - dxi, h: snap.h - dyi }; break;
        case "ne": newCrop = { x: snap.x, y: snap.y + dyi, w: snap.w + dxi, h: snap.h - dyi }; break;
        case "sw": newCrop = { x: snap.x + dxi, y: snap.y, w: snap.w - dxi, h: snap.h + dyi }; break;
        case "se": newCrop = { x: snap.x, y: snap.y, w: snap.w + dxi, h: snap.h + dyi }; break;
      }
      onCropChange(clampCrop(newCrop, cap));
    }
  }, [toImgCoords, cap, onCropChange, crop]);

  // Mouse-up on document
  useEffect(() => {
    const onUp = () => {
      if (localDragMode.current === "none") return;
      localDragMode.current = "none";
      localCropSnap.current = null;
    };
    document.addEventListener("mouseup", onUp);
    return () => document.removeEventListener("mouseup", onUp);
  }, []);

  return (
    <div
      className="absolute inset-0"
      style={{ zIndex: 20, cursor: "crosshair" }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onContextMenu={e => e.preventDefault()}
    />
  );
};

// ---- Main component ----

const ScreenshotCropperModal: FC<Props> = ({ open, hwnd, taskName, version, author, onClose, onSaved }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [crop, setCrop] = useState<CropRect | null>(null);
  const [filename, setFilename] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [preprocessCfg, setPreprocessCfg] = useState<PreprocessConfig>({});
  const [matchMethod, setMatchMethod] = useState<"ccoeff" | "sift">("ccoeff");
  const [matchThreshold, setMatchThreshold] = useState(0.85);
  const [previewImage, setPreviewImage] = useState<CaptureResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [preprocessOpen, setPreprocessOpen] = useState(false);

  // --- Init ---
  useEffect(() => {
    if (!open || !hwnd) return;
    setLoading(true);
    setCapture(null);
    setCrop(null);
    setFilename("");
    setPreprocessCfg({});
    setMatchMethod("ccoeff");
    setMatchThreshold(0.85);
    setPreviewImage(null);
    setShowPreview(false);
    window.pywebview?.api.emit("API:TEMPLATE:CAPTURE", hwnd)
      .then((r: CaptureResult | null) => {
        if (r) setCapture(r);
        setLoading(false);
      })
      .catch(() => { message.error("截图失败"); setLoading(false); });
  }, [open, hwnd]);

  // --- Keyboard shortcuts ---
  useEffect(() => {
    if (!open || confirmOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "s" || e.key === "S") { /* select tool always active — no-op */ }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, confirmOpen]);

  // --- Preprocess test ---
  const handlePreprocessTest = async (mode: "current" | "recapture") => {
    if (!crop) { message.warning("请先在截图上框选模板区域"); return; }
    if (!hwnd) { message.warning("未选择窗口"); return; }
    if (!capture) { message.warning("请等待截图加载完成"); return; }

    setPreviewLoading(true);
    try {
      const args: Record<string, unknown> = {
        mode,
        crop: {
          x: Math.round(crop.x), y: Math.round(crop.y),
          w: Math.round(crop.w), h: Math.round(crop.h),
        },
        match_threshold: matchThreshold,
        match_method: matchMethod,
        base64: capture.base64,
        width: capture.width,
        height: capture.height,
      };
      for (const [k, v] of Object.entries(preprocessCfg)) {
        if (v !== undefined) args[k] = v;
      }

      const res = await window.pywebview?.api.emit("API:PREPROCESS:APPLY", hwnd, args);
      if (res?.base64) {
        const matchCount: number = res.matches?.length ?? 0;
        setPreviewImage(res);
        setShowPreview(true);
        setPreprocessOpen(false);
        message.success(matchCount > 0
          ? `找到 ${matchCount} 个匹配点（绿色>=0.95，橙色>=0.9，红色>=${matchThreshold}）`
          : "预处理完成，未找到匹配点，点击切换对比");
      } else {
        message.error(res?.error ? `预处理失败: ${res.error}` : "后端返回无效，请检查后端日志");
      }
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : "预处理测试失败");
    } finally {
      setPreviewLoading(false);
    }
  };

  // --- Save ---
  const handleConfirm = async () => {
    if (!crop || !filename.trim()) {
      if (!filename.trim()) message.warning("请输入文件名");
      return;
    }
    setSaving(true);
    try {
      await window.pywebview?.api.emit("API:TEMPLATE:SAVE", hwnd,
        [Math.round(crop.x), Math.round(crop.y), Math.round(crop.x + crop.w), Math.round(crop.y + crop.h)],
        filename.trim(), "task", taskName, version, author ?? "匿名作者", capture?.base64);
      message.success(`已保存: ${filename}.bmp`);
      onSaved(filename.trim());
      setConfirmOpen(false);
      onClose();
    } catch (e: unknown) {
      message.error(e instanceof Error ? e.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Modal title={<span><ScissorOutlined className="mr-2" />创建模板图片</span>}
        open={open} onCancel={onClose} centered width={780}
        footer={<div className="flex justify-between items-center">
          <span className="text-xs text-muted">右键清除 | 滚轮缩放 | 拖拽画布/选区 | 四角调整大小</span>
          <div className="flex items-center gap-2">
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" disabled={!crop || crop.w < MIN_CROP}
              onClick={() => setConfirmOpen(true)}>确定</Button>
          </div>
        </div>}
      >
        {loading ? (
          <div style={{
            width: 720, height: 480, display: "flex", alignItems: "center",
            justifyContent: "center", borderRadius: 8, background: "#fafafa",
            border: "1px solid #e5e7eb",
          }}>
            <span className="text-sm text-muted">正在截图...</span>
          </div>
        ) : capture ? (
          <CaptureZoom
            capture={showPreview && previewImage ? previewImage : capture}
            tools={[{ key: "select", label: "选区", shortcut: "S", icon: <HighlightOutlined /> }]}
            extraToolbar={
              <>
                <div className="w-px h-5 bg-[#d9d9d9] mx-1" />
                <Popover
                  open={preprocessOpen}
                  onOpenChange={setPreprocessOpen}
                  trigger="click"
                  placement="bottomLeft"
                  content={
                    <div className="w-[240px]">
                      <div className="flex items-center gap-1.5 mb-3">
                        <span className="flex items-center justify-center w-4 h-4 rounded-md shrink-0 text-[11px] bg-[rgba(139,92,246,0.12)] c-[#8b5cf6]">
                          <ExperimentOutlined />
                        </span>
                        <span className="text-[12px] font-semibold text-heading">预处理测试</span>
                      </div>
                      <div className="text-[10px] text-muted mb-2 leading-tight">
                        用框选区域作为匹配模板
                      </div>
                      <PreprocessConfigPanel cfg={preprocessCfg} onChange={setPreprocessCfg} />
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-[#f0f0f5]">
                        <span className="text-[11px] text-body">匹配阈值</span>
                        <InputNumber size="small" min={0} max={1} step={0.01}
                          className="w-72px" value={matchThreshold}
                          onChange={v => setMatchThreshold(v ?? 0.85)} />
                      </div>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#f0f0f5]">
                        <span className="text-[11px] text-body">匹配算法</span>
                        <Radio.Group size="small" value={matchMethod}
                          onChange={e => setMatchMethod(e.target.value)}>
                          <Radio.Button value="ccoeff" className="text-[10px] px-2">模板</Radio.Button>
                          <Radio.Button value="sift" className="text-[10px] px-2">SIFT</Radio.Button>
                        </Radio.Group>
                      </div>
                      <div className="flex gap-2 mt-2 pt-2 border-t border-[#f0f0f5]">
                        <Button size="small" style={{ borderColor: "#8b5cf6", color: "#8b5cf6" }}
                          loading={previewLoading}
                          onClick={() => handlePreprocessTest("current")}>当前截图</Button>
                        <Button size="small" style={{ borderColor: "#8b5cf6", color: "#8b5cf6" }}
                          loading={previewLoading}
                          onClick={() => handlePreprocessTest("recapture")}>重新截图</Button>
                      </div>
                    </div>
                  }
                >
                  <Button size="small" icon={<ExperimentOutlined />}
                    className="border-[#8b5cf6] c-[#8b5cf6]">预处理测试</Button>
                </Popover>
                {previewImage && (
                  <Button size="small" type="text" icon={<SwapOutlined />}
                    className={showPreview ? "c-[#8b5cf6]" : "c-[#8b8fa3]"}
                    onClick={() => setShowPreview(!showPreview)}>
                    {showPreview ? "处理后" : "原图"}
                  </Button>
                )}
              </>
            }
          >
            {/* Crop overlay */}
            {crop && !showPreview && <CropOverlay crop={crop} capture={capture} />}

            {/* Hint text when no crop */}
            {!crop && !showPreview && (
              <div style={{
                position: "absolute", inset: 0, display: "flex", alignItems: "center",
                justifyContent: "center", pointerEvents: "none", zIndex: 1,
              }}>
                <span className="text-sm text-white/60 bg-black/40 px-4 py-2 rounded-full">
                  左键拖拽框选目标区域
                </span>
              </div>
            )}

            {/* Mouse event handler (inside CaptureZoom for useCaptureZoom()) */}
            <MouseHandler
              capture={capture}
              crop={crop}
              onCropChange={setCrop}
            />
          </CaptureZoom>
        ) : (
          <div style={{
            width: 720, height: 480, display: "flex", alignItems: "center",
            justifyContent: "center", borderRadius: 8, background: "#fafafa",
            border: "1px solid #e5e7eb",
          }}>
            <span className="text-sm text-muted">截图加载失败</span>
          </div>
        )}
      </Modal>

      <SaveModal open={confirmOpen} saving={saving} filename={filename}
        crop={crop} onFilename={setFilename}
        onOk={handleConfirm} onCancel={() => setConfirmOpen(false)} />
    </>
  );
};

export default ScreenshotCropperModal;
