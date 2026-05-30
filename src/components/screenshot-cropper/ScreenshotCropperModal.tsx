import { useState, useRef, useCallback, useEffect, type FC } from "react";
import { Button, Input, InputNumber, message, Modal, Popover, Radio, Spin } from "antd";
import { useResponsiveStore } from "@/store/responsive-store";
import {
  ScissorOutlined, LoadingOutlined, ZoomInOutlined, ZoomOutOutlined, DragOutlined, HighlightOutlined,
  ExperimentOutlined, SwapOutlined,
} from "@ant-design/icons";
import type { PreprocessConfig } from "@/pages/task-editor/PreprocessEditor";
import PreprocessConfigPanel from "@/components/preprocess-config-panel/PreprocessConfigPanel";

/* ============================================================
   Canvas-based architecture (no CSS transform):
   - Image rendered at CSS pixels: w = capture.w * zoom
   - All overlay/handles/hit-test in same canvas-pixel coords
   - Viewport overflow scrolls, scrollbar hidden
   ============================================================ */

interface Props { open: boolean; hwnd: string; taskName?: string; version?: string;
  onClose: () => void; onSaved: (filename: string) => void; }
interface CaptureResult { base64: string; width: number; height: number; }
interface CropRect { x: number; y: number; w: number; h: number; }
type Corner = "nw" | "ne" | "sw" | "se";
type DragMode = "none" | "create" | "move-crop" | `resize-${Corner}` | "pan";

const HANDLE_HIT = 22;
const HANDLE_VISUAL = 12;
const MIN_CROP = 8;
const VP_W = 720;
const VP_H = 480;
const CORNERS: { corner: Corner; cursor: string }[] = [
  { corner: "nw", cursor: "nwse-resize" },
  { corner: "ne", cursor: "nesw-resize" },
  { corner: "sw", cursor: "nesw-resize" },
  { corner: "se", cursor: "nwse-resize" },
];

// ---- Pure utilities (no component closure) ----

// Uses container's bounding rect — naturally accounts for scroll offset and
// any centering within the wrapper, so hit-test always aligns with the visual.
const clientToCanvas = (container: HTMLElement, cx: number, cy: number) => {
  const r = container.getBoundingClientRect();
  const gz = useResponsiveStore.getState().zoom;
  return { x: (cx - r.left) / gz, y: (cy - r.top) / gz };
};

const canvasToImg = (cx: number, cy: number, zoom: number) =>
  ({ x: Math.round(cx / zoom), y: Math.round(cy / zoom) });

const clampCrop = (c: CropRect, capture: CaptureResult) => {
  const x = Math.max(0, Math.min(c.x, capture.width - MIN_CROP));
  const y = Math.max(0, Math.min(c.y, capture.height - MIN_CROP));
  return { x, y, w: Math.max(MIN_CROP, Math.min(c.w, capture.width - x)), h: Math.max(MIN_CROP, Math.min(c.h, capture.height - y)) };
};

const getCornerImgPos = (crop: CropRect, corner: Corner) => {
  switch (corner) {
    case "nw": return { x: crop.x, y: crop.y };
    case "ne": return { x: crop.x + crop.w, y: crop.y };
    case "sw": return { x: crop.x, y: crop.y + crop.h };
    case "se": return { x: crop.x + crop.w, y: crop.y + crop.h };
  }
};

// Clamp hit radius so corner zones don't overlap even at tiny zoom levels
const cornerHitRadius = (crop: CropRect, zoom: number) =>
  Math.min(Math.max(HANDLE_HIT / zoom, 6), Math.min(crop.w, crop.h) * 0.4);

const hitTest = (ix: number, iy: number, crop: CropRect | null, zoom: number): DragMode => {
  if (!crop) return "create";
  const hw = cornerHitRadius(crop, zoom);
  for (const { corner } of CORNERS) {
    const pos = getCornerImgPos(crop, corner);
    if (Math.abs(ix - pos.x) <= hw && Math.abs(iy - pos.y) <= hw) return `resize-${corner}`;
  }
  if (ix > crop.x && ix < crop.x + crop.w && iy > crop.y && iy < crop.y + crop.h) return "move-crop";
  return "create";
};

const getHoverCursor = (ix: number, iy: number, crop: CropRect | null, zoom: number) => {
  if (!crop) return "crosshair";
  const hw = cornerHitRadius(crop, zoom);
  for (const { corner, cursor } of CORNERS) {
    const pos = getCornerImgPos(crop, corner);
    if (Math.abs(ix - pos.x) <= hw && Math.abs(iy - pos.y) <= hw) return cursor;
  }
  if (ix > crop.x && ix < crop.x + crop.w && iy > crop.y && iy < crop.y + crop.h) return "move";
  return "crosshair";
};

// ---- Styles ----

const S = {
  viewport: (cursor: string) =>
    ({ width: VP_W, height: VP_H, overflow: "auto" as const, cursor, borderRadius: 8, background: "#1a1a2e", userSelect: "none" as const }),
  imgWrapper: (w: number, h: number, atMin: boolean) => {
    const centerH = atMin || w < VP_W;
    const centerV = atMin || h < VP_H;
    const s: Record<string, unknown> = { position: "relative", display: "flex",
      width: centerH ? VP_W : Math.max(w, VP_W),
      height: centerV ? VP_H : Math.max(h, VP_H) };
    if (centerV) { s.alignItems = "center"; s.minHeight = 0; s.overflowY = "hidden"; }
    if (centerH) { s.justifyContent = "center"; s.minWidth = 0; s.overflowX = "hidden"; }
    return s;
  },
  img: (w: number, h: number) =>
    ({ width: w, height: h, display: "block" as const }),
  dimOverlay: (left: number, top: number, width: number | string, height: number | string) =>
    ({ position: "absolute" as const, left, top, width, height, background: "rgba(0,0,0,0.55)", pointerEvents: "none" as const, zIndex: 5 }),
  cropBorder: (l: number, t: number, w: number, h: number) =>
    ({ position: "absolute" as const, left: l, top: t, width: w, height: h,
       outline: "2px solid #1677ff",
       boxShadow: "0 0 0 1px rgba(22,119,255,0.25), 0 0 12px rgba(22,119,255,0.15), inset 0 0 0 1px rgba(255,255,255,0.08)",
       pointerEvents: "none" as const, zIndex: 5 }),
  gridLine: (left: number, top: number, width: number, height: number) =>
    ({ position: "absolute" as const, left, top, width, height, background: "rgba(255,255,255,0.22)", pointerEvents: "none" as const, zIndex: 5 }),
  cropLabel: (l: number, t: number) =>
    ({ position: "absolute" as const, left: l, top: t, fontSize: 11, fontWeight: 500, background: "#1677ff", color: "#fff",
       padding: "2px 8px", borderRadius: 4, pointerEvents: "none" as const, zIndex: 10, whiteSpace: "nowrap" as const }),
  resizeHandle: (l: number, t: number, cursor: string) =>
    ({ position: "absolute" as const, zIndex: 10, left: l - HANDLE_VISUAL / 2, top: t - HANDLE_VISUAL / 2,
       width: HANDLE_VISUAL, height: HANDLE_VISUAL, borderRadius: 3,
       background: "#fff", border: "2px solid #1677ff",
       boxShadow: "0 1px 4px rgba(0,0,0,0.25), 0 0 0 1px rgba(22,119,255,0.2)",
       cursor }),
  hint: () =>
    ({ position: "absolute" as const, inset: 0, display: "flex", alignItems: "center", justifyContent: "center", pointerEvents: "none" as const, zIndex: 1 }),
  empty: () =>
    ({ width: VP_W, height: VP_H, display: "flex", alignItems: "center", justifyContent: "center", borderRadius: 8, background: "#fafafa", border: "1px solid #e5e7eb" }),
};

// ---- Toolbar sub-component ----

const Toolbar: FC<{
  tool: "select" | "pan"; onTool: (t: "select" | "pan") => void;
  zoom: number; minZoom: number; onZoom: (z: number) => void; onFit: () => void;
  children?: React.ReactNode;
}> = ({ tool, onTool, zoom, minZoom, onZoom, onFit, children }) => (
  <div className="flex items-center gap-1 bg-[#f5f5f7] rounded-lg p-1 w-fit">
    <Button size="small" type={tool === "select" ? "primary" : "text"} icon={<HighlightOutlined />}
      onClick={() => onTool("select")}>选区 <span className="text-[10px] opacity-50 ml-0.5">S</span></Button>
    <Button size="small" type={tool === "pan" ? "primary" : "text"} icon={<DragOutlined />}
      onClick={() => onTool("pan")}>拖拽 <span className="text-[10px] opacity-50 ml-0.5">D</span></Button>
    <div className="w-px h-5 bg-[#d9d9d9] mx-1" />
    <Button size="small" type="text" icon={<ZoomOutOutlined />}
      disabled={zoom <= minZoom}
      onClick={() => onZoom(Math.max(minZoom, zoom / 1.25))} />
    <span className="text-xs text-[#8b8fa3] px-1 min-w-[40px] text-center">{Math.round(zoom * 100)}%</span>
    <Button size="small" type="text" icon={<ZoomInOutlined />}
      disabled={zoom >= 4}
      onClick={() => onZoom(Math.min(4, zoom * 1.25))} />
    <Button size="small" type="text" onClick={onFit}>适应</Button>
    {children}
  </div>
);

// ---- Crop overlay sub-component ----

const CropOverlay: FC<{ crop: CropRect; zoom: number; canvasW: number; canvasH: number }> = ({ crop, zoom, canvasW, canvasH }) => {
  const cx = crop.x * zoom;
  const cy = crop.y * zoom;
  const cw = crop.w * zoom;
  const ch = crop.h * zoom;

  return (
    <div className="absolute inset-0 pointer-events-none z-5">
      {/* Dim overlays — four rectangles surrounding the crop area */}
      <div style={S.dimOverlay(0, 0, canvasW, Math.max(0, cy))} />
      <div style={S.dimOverlay(0, cy + ch, canvasW, Math.max(0, canvasH - cy - ch))} />
      <div style={S.dimOverlay(0, cy, Math.max(0, cx), ch)} />
      <div style={S.dimOverlay(cx + cw, cy, Math.max(0, canvasW - cx - cw), ch)} />

      {/* Rule-of-thirds grid */}
      <div style={S.gridLine(cx, cy + ch * (1 / 3), cw, 1)} />
      <div style={S.gridLine(cx, cy + ch * (2 / 3), cw, 1)} />
      <div style={S.gridLine(cx + cw * (1 / 3), cy, 1, ch)} />
      <div style={S.gridLine(cx + cw * (2 / 3), cy, 1, ch)} />

      {/* Selection border */}
      <div style={S.cropBorder(cx, cy, cw, ch)} />

      {/* Dimension label — above the selection */}
      <div style={S.cropLabel(cx, Math.max(0, cy - 26))}>
        {Math.round(crop.w)} × {Math.round(crop.h)}
      </div>

      {/* Four corner resize handles */}
      {CORNERS.map(({ corner, cursor }) => {
        const pos = getCornerImgPos(crop, corner);
        return (
          <div key={corner} style={S.resizeHandle(pos.x * zoom, pos.y * zoom, cursor)} />
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
  <Modal title={<span className="text-sm font-semibold text-[#1a1a2e]">保存模板图片</span>}
    open={open} onOk={onOk} onCancel={onCancel} centered
    okText="保存" cancelText="取消" confirmLoading={saving}
    okButtonProps={{ disabled: !filename.trim() }}
    width={400}
  >
    <div className="flex flex-col gap-4 pt-1">
      <div className="flex flex-col gap-1.5">
        <span className="text-[11px] font-medium text-[#6b7280]">文件名</span>
        <Input placeholder="输入模板图片名" value={filename}
          onChange={e => onFilename(e.target.value)}
          suffix={<span className="text-[10px] text-[#9ca3af]">.bmp</span>}
          className="!text-sm" />
      </div>
      {crop && (
        <div className="flex items-center gap-3 px-3 py-2.5 bg-[#f8f9fb] rounded-lg border border-[#eef0f2]">
          <span className="text-[11px] text-[#8b8fa3]">选区尺寸</span>
          <span className="text-xs font-medium text-[#1a1a2e]">{Math.round(crop.w)} × {Math.round(crop.h)} px</span>
        </div>
      )}
    </div>
  </Modal>
);

// ---- Main component ----

const ScreenshotCropperModal: FC<Props> = ({ open, hwnd, taskName, version, onClose, onSaved }) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [capture, setCapture] = useState<CaptureResult | null>(null);
  const [crop, setCrop] = useState<CropRect | null>(null);
  const [zoom, setZoom] = useState(1);
  const [filename, setFilename] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [tool, setTool] = useState<"select" | "pan">("select");
  const [hoverCursor, setHoverCursor] = useState("crosshair");
  const [preprocessCfg, setPreprocessCfg] = useState<PreprocessConfig>({});
  const [matchMethod, setMatchMethod] = useState<"ccoeff" | "sift">("ccoeff");
  const [matchThreshold, setMatchThreshold] = useState(0.85);
  const [previewImage, setPreviewImage] = useState<CaptureResult | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [preprocessOpen, setPreprocessOpen] = useState(false);

  const viewportRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null); // inner div = exact image size

  // Ref snapshots for stable event handlers — avoids re-registering listeners every render
  const captureRef = useRef(capture);
  captureRef.current = capture;
  const cropRef = useRef(crop);
  cropRef.current = crop;
  const zoomRef = useRef(zoom);
  zoomRef.current = zoom;
  const toolRef = useRef(tool);
  toolRef.current = tool;

  const dragMode = useRef<DragMode>("none");
  const dragStartClient = useRef({ x: 0, y: 0 });
  const dragStartScroll = useRef({ x: 0, y: 0 });
  const dragStartCanvas = useRef({ x: 0, y: 0 });
  const cropSnap = useRef<CropRect | null>(null);

  const imgW = capture ? Math.round(capture.width * zoom) : 0;
  const imgH = capture ? Math.round(capture.height * zoom) : 0;
  // Snap to exact viewport dimensions when at minimum zoom, so floating-point
  // rounding never leaves a 1px gutter that would let the image be dragged.
  const minZoom = capture ? Math.min(VP_W / capture.width, 1) : 1;
  const atMin = capture ? zoom <= minZoom + 0.001 : false;
  const dispW = atMin ? VP_W : imgW;
  const dispH = atMin ? Math.round(capture!.height * minZoom) : imgH;

  // --- Init ---
  useEffect(() => {
    if (!open || !hwnd) return;
    setLoading(true); setCapture(null); setCrop(null); setFilename(""); setTool("select");
    setPreprocessCfg({}); setMatchMethod("ccoeff"); setMatchThreshold(0.85); setPreviewImage(null); setShowPreview(false);
    window.pywebview?.api.emit("API:TEMPLATE:CAPTURE", hwnd)
      .then((r: CaptureResult | null) => {
        if (r) {
          setCapture(r);
          const fit = Math.min(VP_W / r.width, 1);
          setZoom(fit);
          requestAnimationFrame(() => {
            const vp = viewportRef.current; if (!vp) return;
            vp.scrollLeft = 0;
            vp.scrollTop = Math.round((r.height * fit - VP_H) / 2);
          });
        }
        setLoading(false);
      })
      .catch(() => { message.error("截图失败"); setLoading(false); });
  }, [open, hwnd]);

  // --- Apply zoom + scroll to DOM synchronously, then sync React ---
  const syncZoomToDom = useCallback((z: number, scrollLeft: number, scrollTop: number) => {
    const cap = captureRef.current;
    const vp = viewportRef.current;
    if (!cap || !vp) return;
    const minZ = Math.min(VP_W / cap.width, 1);
    const atMin = z <= minZ + 0.001;
    const w = atMin ? VP_W : Math.round(cap.width * z);
    const h = atMin ? Math.round(cap.height * minZ) : Math.round(cap.height * z);
    const img = vp.querySelector("img") as HTMLElement | null;
    if (img) { img.style.width = `${w}px`; img.style.height = `${h}px`; }
    const inner = containerRef.current;
    if (inner) { inner.style.width = `${w}px`; inner.style.height = `${h}px`; }
    const wrapper = vp.firstElementChild as HTMLElement | null;
    const needsCenterH = atMin || w < VP_W;
    const needsCenterV = atMin || h < VP_H;
    if (wrapper) {
      wrapper.style.width = needsCenterH ? `${VP_W}px` : `${Math.max(w, VP_W)}px`;
      wrapper.style.height = needsCenterV ? `${VP_H}px` : `${Math.max(h, VP_H)}px`;
      wrapper.style.alignItems = needsCenterV ? "center" : "";
      wrapper.style.justifyContent = needsCenterH ? "center" : "";
      wrapper.style.minHeight = needsCenterV ? "0" : "";
      wrapper.style.minWidth = needsCenterH ? "0" : "";
      wrapper.style.overflowY = needsCenterV ? "hidden" : "";
      wrapper.style.overflowX = needsCenterH ? "hidden" : "";
    }
    vp.scrollLeft = needsCenterH ? 0 : scrollLeft;
    vp.scrollTop = needsCenterV ? 0 : scrollTop;
    setZoom(z);
  }, []);

  const centerImage = useCallback((z: number) => {
    const cap = captureRef.current;
    if (!cap) return;
    syncZoomToDom(z, 0, Math.round((cap.height * z - VP_H) / 2));
  }, [syncZoomToDom]);

  // --- Mouse event handlers (registered once) ---
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    const cap = captureRef.current;
    if (!cap) return;
    e.preventDefault();
    if (e.button === 2) { setCrop(null); return; }
    if (e.button !== 0) return;

    dragStartClient.current = { x: e.clientX, y: e.clientY };
    const vp = viewportRef.current;
    if (vp) dragStartScroll.current = { x: vp.scrollLeft, y: vp.scrollTop };
    const cnt = containerRef.current;
    if (!cnt) return;
    dragStartCanvas.current = clientToCanvas(cnt, e.clientX, e.clientY);

    if (toolRef.current === "pan") { dragMode.current = "pan"; return; }

    const img = canvasToImg(dragStartCanvas.current.x, dragStartCanvas.current.y, zoomRef.current);
    dragMode.current = hitTest(img.x, img.y, cropRef.current, zoomRef.current);
    cropSnap.current = cropRef.current ? { ...cropRef.current } : null;
  }, []);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (dragMode.current === "none") return;
      const cap = captureRef.current;
      if (!cap) return;
      const vp = viewportRef.current;
      if (!vp) return;

      if (dragMode.current === "pan") {
        const sl = dragStartScroll.current.x - (e.clientX - dragStartClient.current.x);
        const st = dragStartScroll.current.y - (e.clientY - dragStartClient.current.y);
        vp.scrollLeft = Math.max(0, Math.min(sl, vp.scrollWidth - vp.clientWidth));
        vp.scrollTop = Math.max(0, Math.min(st, vp.scrollHeight - vp.clientHeight));
        return;
      }

      const cnt = containerRef.current;
      if (!cnt) return;
      const curCanvas = clientToCanvas(cnt, e.clientX, e.clientY);
      const sCanvas = dragStartCanvas.current;
      const z = zoomRef.current;

      if (dragMode.current === "create") {
        const x = Math.min(sCanvas.x, curCanvas.x);
        const y = Math.min(sCanvas.y, curCanvas.y);
        const w = Math.abs(curCanvas.x - sCanvas.x);
        const h = Math.abs(curCanvas.y - sCanvas.y);
        if (w >= MIN_CROP * z || h >= MIN_CROP * z) {
          const i = canvasToImg(x, y, z);
          setCrop(clampCrop({ x: i.x, y: i.y, w: w / z, h: h / z }, cap));
        }
        return;
      }

      const snap = cropSnap.current; if (!snap) return;
      const dxi = (curCanvas.x - sCanvas.x) / z;
      const dyi = (curCanvas.y - sCanvas.y) / z;

      if (dragMode.current === "move-crop") {
        setCrop(clampCrop({ x: snap.x + dxi, y: snap.y + dyi, w: snap.w, h: snap.h }, cap));
        return;
      }

      if (dragMode.current.startsWith("resize-")) {
        const corner = dragMode.current.replace("resize-", "") as Corner;
        let newCrop: CropRect;
        switch (corner) {
          case "nw": newCrop = { x: snap.x + dxi, y: snap.y + dyi, w: snap.w - dxi, h: snap.h - dyi }; break;
          case "ne": newCrop = { x: snap.x,       y: snap.y + dyi, w: snap.w + dxi, h: snap.h - dyi }; break;
          case "sw": newCrop = { x: snap.x + dxi, y: snap.y,       w: snap.w - dxi, h: snap.h + dyi }; break;
          case "se": newCrop = { x: snap.x,       y: snap.y,       w: snap.w + dxi, h: snap.h + dyi }; break;
        }
        setCrop(clampCrop(newCrop, cap));
      }
    };
    const onUp = () => { dragMode.current = "none"; cropSnap.current = null; };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    return () => { document.removeEventListener("mousemove", onMove); document.removeEventListener("mouseup", onUp); };
  }, []); // stable — all state read via refs

  // --- Keyboard shortcuts ---
  useEffect(() => {
    if (!open || confirmOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === "s" || e.key === "S") setTool("select");
      if (e.key === "d" || e.key === "D") setTool("pan");
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, confirmOpen]);

  // --- Cursor hover ---
  const handleViewportHover = useCallback((e: React.MouseEvent) => {
    if (dragMode.current !== "none" || toolRef.current === "pan") return;
    const cnt = containerRef.current; if (!cnt) return;
    const canvas = clientToCanvas(cnt, e.clientX, e.clientY);
    const img = canvasToImg(canvas.x, canvas.y, zoomRef.current);
    setHoverCursor(getHoverCursor(img.x, img.y, cropRef.current, zoomRef.current));
  }, []);

  // --- Wheel zoom ---
  // Native listener with { passive: false } — React's synthetic onWheel can't
  // reliably preventDefault across all browsers, causing unwanted scroll.
  const wheelRaf = useRef<number | null>(null);
  const wheelBaseZoom = useRef(1);
  const wheelAnchor = useRef({ cx: 0, cy: 0, clientX: 0, clientY: 0 });

  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp || !capture) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const cap = captureRef.current;
      if (!cap) return;

      const z = zoomRef.current;
      const zoomFactor = 1 - e.deltaY * 0.003;
      const minZ = Math.min(VP_W / cap.width, 1);
      const newZoom = Math.max(minZ, Math.min(4, z * zoomFactor));
      if (newZoom === z) return;

      zoomRef.current = newZoom;

      if (wheelRaf.current === null) {
        wheelBaseZoom.current = z;
        const cnt2 = containerRef.current;
        if (!cnt2) return;
        const cr = cnt2.getBoundingClientRect();
        wheelAnchor.current = {
          cx: e.clientX - cr.left,
          cy: e.clientY - cr.top,
          clientX: e.clientX,
          clientY: e.clientY,
        };
        wheelRaf.current = requestAnimationFrame(() => {
          wheelRaf.current = null;
          const finalZ = zoomRef.current;
          const ratio = finalZ / wheelBaseZoom.current;
          const a = wheelAnchor.current;
          const rect2 = vp.getBoundingClientRect();
          // Anchor scroll: keeps the point under the cursor fixed
          const anchorSL = a.cx * ratio - (a.clientX - rect2.left);
          const anchorST = a.cy * ratio - (a.clientY - rect2.top);
          // Center scroll: pulls the point toward the viewport center
          const centerSL = a.cx * ratio - VP_W / 2;
          const centerST = a.cy * ratio - VP_H / 2;
          // Gravitate toward center when zooming in, pure anchor when zooming out
          const t = ratio > 1 ? 0.7 : 0;
          syncZoomToDom(finalZ,
            anchorSL + (centerSL - anchorSL) * t,
            anchorST + (centerST - anchorST) * t);
        });
      }
    };

    vp.addEventListener("wheel", onWheel, { passive: false });
    return () => vp.removeEventListener("wheel", onWheel);
  }, [capture, syncZoomToDom]);

  // --- Preprocess test ---
  const handlePreprocessTest = async (mode: "current" | "recapture") => {
    const cropSnapshot = cropRef.current;
    if (!cropSnapshot) { message.warning("请先在截图上框选模板区域"); return; }
    if (!hwnd) { message.warning("未选择窗口"); return; }
    const cap = captureRef.current;
    if (!cap) { message.warning("请等待截图加载完成"); return; }

    setPreviewLoading(true);
    try {
      const args: Record<string, unknown> = {
        mode,
        crop: {
          x: Math.round(cropSnapshot.x), y: Math.round(cropSnapshot.y),
          w: Math.round(cropSnapshot.w), h: Math.round(cropSnapshot.h),
        },
        match_threshold: matchThreshold,
        match_method: matchMethod,
        base64: cap.base64,
        width: cap.width,
        height: cap.height,
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
          ? `找到 ${matchCount} 个匹配点（绿色≥0.95，橙色≥0.9，红色≥${matchThreshold}）`
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
    if (!crop || !filename.trim()) { if (!filename.trim()) message.warning("请输入文件名"); return; }
    setSaving(true);
    try {
      await window.pywebview?.api.emit("API:TEMPLATE:SAVE", hwnd,
        [Math.round(crop.x), Math.round(crop.y), Math.round(crop.x + crop.w), Math.round(crop.y + crop.h)],
        filename.trim(), "task", taskName, version, capture?.base64);
      message.success(`已保存: ${filename}.bmp`);
      onSaved(filename.trim());
      setConfirmOpen(false); onClose();
    } catch (e: unknown) { message.error(e instanceof Error ? e.message : "保存失败"); }
    finally { setSaving(false); }
  };

  return (
    <>
      <Modal title={<span><ScissorOutlined className="mr-2" />创建模板图片</span>}
        open={open} onCancel={onClose} centered width={780}
        footer={<div className="flex justify-between items-center">
          <span className="text-xs text-[#8b8fa3]">右键清除 · 滚轮缩放 · 拖拽画布/选区 · 四角调整大小</span>
          <div className="flex items-center gap-2">
            <Button onClick={onClose}>取消</Button>
            <Button type="primary" disabled={!crop || crop.w < MIN_CROP}
              onClick={() => setConfirmOpen(true)}>确定</Button>
          </div>
        </div>}
      >
        <Spin spinning={loading} indicator={<LoadingOutlined spin />} size="large">
          <div className="flex flex-col gap-3">
            <Toolbar tool={tool} onTool={setTool} zoom={zoom}
              minZoom={capture ? Math.min(VP_W / capture.width, 1) : 1}
              onZoom={(z: number) => {
                if (!capture) return;
                centerImage(Math.max(VP_W / capture.width, z));
              }}
              onFit={() => {
                if (!capture) return;
                centerImage(Math.min(VP_W / capture.width, 1));
              }}>
              {capture && (
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
                          <span className="text-[12px] font-semibold text-[#1a1a2e]">预处理测试</span>
                        </div>
                        <div className="text-[10px] text-[#8b8fa3] mb-2 leading-tight">
                          用框选区域作为匹配模板
                        </div>
                        <PreprocessConfigPanel cfg={preprocessCfg} onChange={setPreprocessCfg} />
                        <div className="flex items-center justify-between mt-3 pt-3 border-t border-[#f0f0f5]">
                          <span className="text-[11px] text-[#374151]">匹配阈值</span>
                          <InputNumber size="small" min={0} max={1} step={0.01}
                            className="w-72px" value={matchThreshold}
                            onChange={v => setMatchThreshold(v ?? 0.85)} />
                        </div>
                        <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#f0f0f5]">
                          <span className="text-[11px] text-[#374151]">匹配算法</span>
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
              )}
            </Toolbar>

            {capture ? (
              <div ref={viewportRef}
                className="rounded-lg select-none hide-scrollbar"
                style={S.viewport(tool === "pan" ? "grab" : hoverCursor)}
                onMouseDown={handleMouseDown} onMouseMove={handleViewportHover}
                onContextMenu={e => e.preventDefault()}>
                <div style={S.imgWrapper(dispW, dispH, atMin)}>
                  <div ref={containerRef} style={{ position: "relative", width: dispW, height: dispH }}>
                    <img src={showPreview && previewImage ? previewImage.base64 : capture.base64} alt="" draggable={false} style={S.img(dispW, dispH)} />
                    {crop && !showPreview && <CropOverlay crop={crop} zoom={zoom} canvasW={dispW} canvasH={dispH} />}
                    {!crop && !showPreview && (
                      <div style={S.hint()}>
                        <span className="text-sm text-white/60 bg-black/40 px-4 py-2 rounded-full">左键拖拽框选目标区域</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : !loading ? (
              <div style={S.empty()}>
                <span className="text-sm text-[#8b8fa3]">截图加载失败</span>
              </div>
            ) : null}
          </div>
        </Spin>
      </Modal>

      <SaveModal open={confirmOpen} saving={saving} filename={filename}
        crop={crop} onFilename={setFilename}
        onOk={handleConfirm} onCancel={() => setConfirmOpen(false)} />
    </>
  );
};

export default ScreenshotCropperModal;
