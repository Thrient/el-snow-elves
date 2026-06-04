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
        <span className="text-[11px] text-[#374151] cursor-help"
          title="将灰度图转为纯黑白，0 时自动用 OTSU">二值化</span>
        <Switch size="small" checked={cfg.binarize ?? false}
          onChange={(v) => set("binarize", v || undefined)} />
      </div>
      {cfg.binarize && (
        <div className="flex items-center justify-between">
          <span className="text-[10px] text-[#8b8fa3] ml-4">阈值</span>
          <InputNumber size="small" min={0} max={255} step={5} className="w-72px"
            value={cfg.binarize_threshold ?? 0}
            onChange={(v) => set("binarize_threshold", v === 0 ? undefined : (v ?? undefined))} />
        </div>
      )}

      {/* Invert */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-[#374151] cursor-help"
          title="黑变白、白变黑">反转颜色</span>
        <Switch size="small" checked={cfg.binarize_invert ?? false}
          onChange={(v) => set("binarize_invert", v || undefined)} />
      </div>

      {/* Adaptive */}
      <div className="flex items-center justify-between">
        <span className="text-[11px] text-[#374151] cursor-help"
          title="分块独立计算阈值，适合光照不均">自适应</span>
        <Switch size="small" checked={cfg.adaptive ?? false}
          onChange={(v) => set("adaptive", v || undefined)} />
      </div>
      {cfg.adaptive && (
        <>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#8b8fa3] ml-4">块大小</span>
            <InputNumber size="small" min={5} max={31} step={2} className="w-72px"
              value={cfg.adaptive_block ?? 11}
              onChange={(v) => set("adaptive_block", v === 11 ? undefined : (v ?? 11))} />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#8b8fa3] ml-4">常数</span>
            <InputNumber size="small" min={0} max={10} className="w-72px"
              value={cfg.adaptive_c ?? 2}
              onChange={(v) => set("adaptive_c", v === 2 ? undefined : (v ?? 2))} />
          </div>
        </>
      )}
    </div>
  );
};

export default PreprocessConfigPanel;
