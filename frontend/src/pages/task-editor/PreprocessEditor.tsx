import type { FC } from "react";
import { BulbOutlined } from "@ant-design/icons";
import PreprocessConfigPanel from "@/components/preprocess-config-panel/PreprocessConfigPanel";

export interface PreprocessConfig {
  binarize?: boolean;
  binarize_threshold?: number;
  binarize_invert?: boolean;
  adaptive?: boolean;
  adaptive_block?: number;
  adaptive_c?: number;
}

interface Props {
  value: PreprocessConfig | undefined;
  onChange: (v: PreprocessConfig | undefined) => void;
  onRemove?: () => void;
}

const PreprocessEditor: FC<Props> = ({ value, onChange, onRemove }) => {
  const cfg = value ?? {};

  const update = (next: PreprocessConfig) => {
    const keys = Object.keys(next).filter(
      (k) => next[k as keyof PreprocessConfig] !== undefined && next[k as keyof PreprocessConfig] !== false,
    );
    onChange(keys.length > 0 ? next : undefined);
  };

  return (
    <div
      className="rounded-xl border border-dashed bg-white"
      style={{ borderColor: "rgba(139,92,246,0.3)", background: "linear-gradient(135deg, rgba(139,92,246,0.04), #fff)" }}
    >
      <div className="flex items-center gap-2 px-3.5 py-2.5">
        <span
          className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
          style={{ background: "rgba(139,92,246,0.12)", color: "#8b5cf6" }}
        >
          <BulbOutlined />
        </span>
        <span className="text-[12px] font-semibold text-[#1a1a2e]">图像预处理</span>
        <span className="text-[10px] text-[#8b8fa3] ml-auto">选填，不设则不处理</span>
        {onRemove && (
          <button
            onClick={onRemove}
            className="text-[#c0c4cc] hover:text-[#ff4d4f] transition-colors text-xs shrink-0 border-0 bg-transparent cursor-pointer"
          >
            ×
          </button>
        )}
      </div>
      <div className="px-3.5 pb-3 pt-2">
        <PreprocessConfigPanel cfg={cfg} onChange={update} />
      </div>
    </div>
  );
};

export default PreprocessEditor;
