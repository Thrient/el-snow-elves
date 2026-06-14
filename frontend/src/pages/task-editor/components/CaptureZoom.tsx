import {
  useState, useRef, useCallback, useEffect, createContext, useContext,
  type FC, type ReactNode,
} from "react";
import { Button } from "antd";
import {
  ZoomInOutlined, ZoomOutOutlined, DragOutlined,
} from "@ant-design/icons";

/* ============================================================
   CaptureZoom — wraps a screenshot image with zoom/pan controls
   Provides context for child overlays to convert screen coords
   to image pixel coordinates.

   Modes:
     - "function" (default): overlays active, consumer tools fire
     - "pan": viewport draggable, overlays pointer-events: none
   ============================================================ */

interface CaptureData {
  base64: string;
  width: number;
  height: number;
}

interface CaptureTool {
  key: string;
  label: string;
  shortcut?: string;
  icon?: React.ReactNode;
}

interface CaptureZoomContextValue {
  imgRef: React.RefObject<HTMLImageElement | null>;
  viewportRef: React.RefObject<HTMLDivElement | null>;
  zoom: number;
  capture: CaptureData;
  tool: string;
  toImgCoords: (clientX: number, clientY: number) => { x: number; y: number } | null;
}

interface Props {
  capture: CaptureData;
  tools?: CaptureTool[];
  extraToolbar?: ReactNode;
  children?: ReactNode;
}

const VP_W = 720;
const VP_H = 480;
const MAX_ZOOM = 10;
const ZOOM_STEP = 1.25;

const CaptureZoomContext = createContext<CaptureZoomContextValue | null>(null);

export const useCaptureZoom = (): CaptureZoomContextValue => {
  const ctx = useContext(CaptureZoomContext);
  if (!ctx) {
    throw new Error("useCaptureZoom must be used within a <CaptureZoom>");
  }
  return ctx;
};

const CaptureZoom: FC<Props> = ({ capture, tools = [], extraToolbar, children }) => {
  const defaultTool = tools.length > 0 ? tools[0].key : "function";
  const [tool, setTool] = useState<string>("function");
  const [zoom, setZoom] = useState(0);
  const imgRef = useRef<HTMLImageElement | null>(null);
  const viewportRef = useRef<HTMLDivElement | null>(null);

  const minZoom = Math.min(VP_W / capture.width, 1);

  // --- Compute derived display dimensions ---
  const atMin = zoom <= minZoom + 0.001;
  const dispW = atMin ? VP_W : Math.round(capture.width * zoom);
  const dispH = atMin ? Math.round(capture.height * minZoom) : Math.round(capture.height * zoom);

  // --- Zoom ref for stable event handlers ---
  const zoomRef = useRef(zoom);
  zoomRef.current = zoom;

  // --- Sync zoom to DOM (avoids batching issues from setZoom + scroll) ---
  const syncZoom = useCallback((z: number, scrollLeft: number, scrollTop: number) => {
    const vp = viewportRef.current;
    const img = imgRef.current;
    if (!vp || !img) return;
    const atMinZ = z <= minZoom + 0.001;
    const w = atMinZ ? VP_W : Math.round(capture.width * z);
    const h = atMinZ ? Math.round(capture.height * minZoom) : Math.round(capture.height * z);
    img.style.width = `${w}px`;
    img.style.height = `${h}px`;

    const centerH = atMinZ || w < VP_W;
    const centerV = atMinZ || h < VP_H;

    const wrapper = vp.firstElementChild as HTMLElement | null;
    if (wrapper) {
      wrapper.style.width = centerH ? `${VP_W}px` : `${Math.max(w, VP_W)}px`;
      wrapper.style.height = centerV ? `${VP_H}px` : `${Math.max(h, VP_H)}px`;
      wrapper.style.alignItems = centerV ? "center" : "";
      wrapper.style.justifyContent = centerH ? "center" : "";
      wrapper.style.minHeight = centerV ? "0" : "";
      wrapper.style.minWidth = centerH ? "0" : "";
      wrapper.style.overflowY = centerV ? "hidden" : "";
      wrapper.style.overflowX = centerH ? "hidden" : "";
    }

    vp.scrollLeft = centerH ? 0 : scrollLeft;
    vp.scrollTop = centerV ? 0 : scrollTop;
    setZoom(z);
  }, [capture.width, capture.height, minZoom]);

  // --- Initial zoom: fit to viewport, auto-center vertically ---
  useEffect(() => {
    const initZ = minZoom;
    setZoom(initZ);
    requestAnimationFrame(() => {
      const vp = viewportRef.current;
      if (!vp) return;
      vp.scrollLeft = 0;
      vp.scrollTop = Math.round((capture.height * initZ - VP_H) / 2);
    });
    // We only want this on mount / capture change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [capture.base64]);

  // --- Wheel zoom with anchor (keep pixel under cursor fixed) + RAF coalesce ---
  const wheelRaf = useRef<number | null>(null);
  const wheelBaseZoom = useRef(1);
  const wheelAnchor = useRef({ cx: 0, cy: 0, clientX: 0, clientY: 0 });

  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const curZ = zoomRef.current;
      const zoomFactor = 1 - e.deltaY * 0.003;
      const newZ = Math.max(minZoom, Math.min(MAX_ZOOM, curZ * zoomFactor));
      if (newZ === curZ) return;

      zoomRef.current = newZ;

      if (wheelRaf.current === null) {
        wheelBaseZoom.current = curZ;
        const img = imgRef.current;
        if (!img) return;
        const imgRect = img.getBoundingClientRect();
        wheelAnchor.current = {
          cx: e.clientX - imgRect.left,
          cy: e.clientY - imgRect.top,
          clientX: e.clientX,
          clientY: e.clientY,
        };

        wheelRaf.current = requestAnimationFrame(() => {
          wheelRaf.current = null;
          const finalZ = zoomRef.current;
          const ratio = finalZ / wheelBaseZoom.current;
          const a = wheelAnchor.current;
          if (!vp || !imgRef.current) return;
          const vpRect = vp.getBoundingClientRect();
          const anchorSL = a.cx * ratio - (a.clientX - vpRect.left);
          const anchorST = a.cy * ratio - (a.clientY - vpRect.top);
          const centerSL = a.cx * ratio - VP_W / 2;
          const centerST = a.cy * ratio - VP_H / 2;
          // Gravitate toward center when zooming in, pure anchor when zooming out
          const t = ratio > 1 ? 0.7 : 0;
          syncZoom(
            finalZ,
            anchorSL + (centerSL - anchorSL) * t,
            anchorST + (centerST - anchorST) * t,
          );
        });
      }
    };

    vp.addEventListener("wheel", onWheel, { passive: false });
    return () => vp.removeEventListener("wheel", onWheel);
  }, [minZoom, syncZoom]);

  // --- Toolbar callbacks ---
  const handleZoomIn = () => {
    const newZ = Math.min(MAX_ZOOM, zoom * ZOOM_STEP);
    const vp = viewportRef.current;
    if (!vp) return;
    syncZoom(newZ, vp.scrollLeft + (VP_W / 2) * (newZ / zoom - 1), vp.scrollTop + (VP_H / 2) * (newZ / zoom - 1));
  };

  const handleZoomOut = () => {
    const newZ = Math.max(minZoom, zoom / ZOOM_STEP);
    const vp = viewportRef.current;
    if (!vp) return;
    syncZoom(newZ, vp.scrollLeft + (VP_W / 2) * (newZ / zoom - 1), vp.scrollTop + (VP_H / 2) * (newZ / zoom - 1));
  };

  const handleFit = () => {
    requestAnimationFrame(() => {
      const vp = viewportRef.current;
      syncZoom(minZoom, 0, vp ? Math.round((capture.height * minZoom - VP_H) / 2) : 0);
    });
  };

  // --- Keyboard shortcuts ---
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      const key = e.key.toLowerCase();
      if (key === "d") {
        setTool((prev) => (prev === "pan" ? defaultTool : "pan"));
        return;
      }
      // Any tool shortcut toggles to that tool
      const matched = tools.find((t) => t.shortcut?.toLowerCase() === key);
      if (matched) setTool(matched.key);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [defaultTool, tools]);

  // --- Pan via viewport drag ---
  const panning = useRef(false);
  const panStart = useRef({ x: 0, y: 0, sl: 0, st: 0 });

  const handleViewportMouseDown = useCallback((e: React.MouseEvent) => {
    if (tool !== "pan" || e.button !== 0) return;
    const vp = viewportRef.current;
    if (!vp) return;
    panning.current = true;
    panStart.current = { x: e.clientX, y: e.clientY, sl: vp.scrollLeft, st: vp.scrollTop };
  }, [tool]);

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!panning.current) return;
      const vp = viewportRef.current;
      if (!vp) return;
      vp.scrollLeft = panStart.current.sl - (e.clientX - panStart.current.x);
      vp.scrollTop = panStart.current.st - (e.clientY - panStart.current.y);
    };
    const onUp = () => { panning.current = false; };
    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
    return () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
  }, []);

  // --- toImgCoords: convert clientX/Y to image pixel coordinates ---
  const toImgCoords = useCallback(
    (clientX: number, clientY: number): { x: number; y: number } | null => {
      const img = imgRef.current;
      if (!img) return null;
      const rect = img.getBoundingClientRect();
      const scaleX = capture.width / rect.width;
      const scaleY = capture.height / rect.height;
      return {
        x: Math.round((clientX - rect.left) * scaleX),
        y: Math.round((clientY - rect.top) * scaleY),
      };
    },
    [capture.width, capture.height],
  );

  const contextValue: CaptureZoomContextValue = {
    imgRef,
    viewportRef,
    zoom,
    capture,
    tool,
    toImgCoords,
  };

  const centerH = atMin || dispW < VP_W;
  const centerV = atMin || dispH < VP_H;

  return (
    <CaptureZoomContext.Provider value={contextValue}>
      <div className="flex flex-col gap-2">
        {/* Unified toolbar */}
        <div className="flex items-center gap-1 bg-[#f5f5f7] rounded-lg p-1 w-fit">
          {/* Consumer tool buttons */}
          {tools.map((t) => (
            <Button
              key={t.key}
              size="small"
              type={tool === t.key ? "primary" : "text"}
              icon={t.icon}
              onClick={() => setTool(t.key)}
            >
              {t.label}
              {t.shortcut && <kbd className="ml-1 text-[10px] opacity-60">{t.shortcut}</kbd>}
            </Button>
          ))}

          {/* Pan toggle (built-in) */}
          <Button
            size="small"
            type={tool === "pan" ? "primary" : "text"}
            icon={<DragOutlined />}
            onClick={() => setTool("pan")}
          >
            拖拽 <kbd className="ml-1 text-[10px] opacity-60">D</kbd>
          </Button>

          <div className="w-px h-5 bg-[#d9d9d9] mx-1" />

          {/* Zoom controls (unchanged) */}
          <Button size="small" type="text" icon={<ZoomOutOutlined />}
            disabled={zoom <= minZoom}
            onClick={handleZoomOut} />
          <span className="text-xs text-muted px-1 min-w-[40px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <Button size="small" type="text" icon={<ZoomInOutlined />}
            disabled={zoom >= MAX_ZOOM}
            onClick={handleZoomIn} />
          <Button size="small" type="text" onClick={handleFit}>适应</Button>

          {/* Extra toolbar buttons */}
          {extraToolbar}
        </div>

        {/* Viewport */}
        <div ref={viewportRef}
          className="capture-zoom-viewport hide-scrollbar"
          style={{
            width: VP_W,
            height: VP_H,
            overflow: "auto",
            background: "#1a1a2e",
            borderRadius: 8,
            userSelect: "none",
            cursor: tool === "pan" ? "grab" : undefined,
          }}
          onMouseDown={handleViewportMouseDown}>
          <div style={{
            position: "relative",
            display: "flex",
            width: centerH ? VP_W : Math.max(dispW, VP_W),
            height: centerV ? VP_H : Math.max(dispH, VP_H),
            alignItems: centerV ? "center" : undefined,
            justifyContent: centerH ? "center" : undefined,
            overflowX: centerH ? "hidden" : undefined,
            overflowY: centerV ? "hidden" : undefined,
          }}>
            <div style={{ position: "relative", width: dispW, height: dispH }}>
              <img ref={imgRef}
                src={capture.base64}
                alt=""
                draggable={false}
                style={{ width: dispW, height: "auto", display: "block" }} />
              {/* Overlays: pointer-events none in pan mode so viewport scroll works */}
              {tool === "pan" ? (
                <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
                  {children}
                </div>
              ) : (
                children
              )}
            </div>
          </div>
        </div>
      </div>
    </CaptureZoomContext.Provider>
  );
};

export default CaptureZoom;
