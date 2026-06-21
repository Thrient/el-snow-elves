import type { FC } from "react";
import { InputNumber, Switch } from "antd";
import type { PreprocessConfig } from "@/pages/task-editor/PreprocessEditor";

interface Props {
  cfg: PreprocessConfig;
  onChange: (next: PreprocessConfig) => void;
}

/** Reusable preprocessing controls — switches for binarize/adaptive/invert with nested number inputs. */
const PreprocessConfigPanel: FC<Props> = ({ cfg, onChange }) => {
  const set = (k: keyof PreprocessConfig, v: unknown) => {
    const next = { ...cfg, [k]: v };
    if (v === undefined || v === false) delete next[k];
    onChange(next);
  };

  return (
    <div className="space-y-2">
      {/* Binarize */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="将灰度图转为纯黑白，0 时自动用 OTSU">二值化</span>
        <Switch size="small" checked={cfg.binarize ?? false}
          onChange={(v) => set("binarize", v || undefined)} />
      </div>
      {cfg.binarize && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted ml-4">阈值</span>
          <InputNumber size="small" min={0} max={255} step={5} className="w-72px"
            value={cfg.binarize_threshold ?? 0}
            onChange={(v) => set("binarize_threshold", v === 0 ? undefined : (v ?? undefined))} />
        </div>
      )}

      {/* Invert */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="黑变白、白变黑">反转颜色</span>
        <Switch size="small" checked={cfg.binarize_invert ?? false}
          onChange={(v) => set("binarize_invert", v || undefined)} />
      </div>

      {/* Adaptive */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="分块独立计算阈值，适合光照不均">自适应</span>
        <Switch size="small" checked={cfg.adaptive ?? false}
          onChange={(v) => set("adaptive", v || undefined)} />
      </div>
      {cfg.adaptive && (
        <>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-muted ml-4">块大小</span>
            <InputNumber size="small" min={5} max={31} step={2} className="w-72px"
              value={cfg.adaptive_block ?? 11}
              onChange={(v) => set("adaptive_block", v === 11 ? undefined : (v ?? 11))} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-muted ml-4">常数</span>
            <InputNumber size="small" min={0} max={10} className="w-72px"
              value={cfg.adaptive_c ?? 2}
              onChange={(v) => set("adaptive_c", v === 2 ? undefined : (v ?? 2))} />
          </div>
        </>
      )}

      {/* Canny 边缘 */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="边缘检测，匹配轮廓线条时更鲁棒">Canny 边缘</span>
        <Switch size="small" checked={cfg.canny ?? false}
          onChange={(v) => set("canny", v || undefined)} />
      </div>
      {cfg.canny && (
        <>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-muted ml-4">低阈值</span>
            <InputNumber size="small" min={0} max={255} step={5} className="w-72px"
              value={cfg.canny_low ?? 50}
              onChange={(v) => set("canny_low", v === 50 ? undefined : (v ?? 50))} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-muted ml-4">高阈值</span>
            <InputNumber size="small" min={0} max={255} step={5} className="w-72px"
              value={cfg.canny_high ?? 150}
              onChange={(v) => set("canny_high", v === 150 ? undefined : (v ?? 150))} />
          </div>
        </>
      )}

      {/* 膨胀 / 腐蚀 */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="加粗白色区域，连接断线">膨胀</span>
        <Switch size="small" checked={cfg.dilate ?? false}
          onChange={(v) => set("dilate", v || undefined)} />
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="减细白色区域，去除噪点">腐蚀</span>
        <Switch size="small" checked={cfg.erode ?? false}
          onChange={(v) => set("erode", v || undefined)} />
      </div>
      {(cfg.dilate || cfg.erode) && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted ml-4">核大小</span>
          <InputNumber size="small" min={1} max={7} step={2} className="w-72px"
            value={cfg.morph_size ?? 3}
            onChange={(v) => set("morph_size", v === 3 ? undefined : (v ?? 3))} />
        </div>
      )}

      {/* CLAHE */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-body cursor-help"
          title="自适应直方图均衡，改善光照不均">CLAHE</span>
        <Switch size="small" checked={cfg.clahe ?? false}
          onChange={(v) => set("clahe", v || undefined)} />
      </div>
      {cfg.clahe && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-muted ml-4">对比度限制</span>
          <InputNumber size="small" min={1} max={10} className="w-72px"
            value={cfg.clahe_clip ?? 2}
            onChange={(v) => set("clahe_clip", v === 2 ? undefined : (v ?? 2))} />
        </div>
      )}
    </div>
  );
};

export default PreprocessConfigPanel;
