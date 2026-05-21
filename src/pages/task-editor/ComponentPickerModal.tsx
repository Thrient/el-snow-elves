import { useMemo, type FC } from "react";
import { Modal } from "antd";
import type { CellModel, VarType } from "@/types/task";
import { compatibleModels, VAR_TYPE_META } from "@/utils/type-compat";
import MiniPreview from "@/components/mini-preview/MiniPreview";

interface Props {
  open: boolean;
  varName: string;
  varValue: unknown;
  varType?: VarType;
  onSelect: (model: CellModel) => void;
  onCancel: () => void;
}

const MODEL_META: Record<string, { label: string; short: string; color: string; bg: string }> = {
  "el-input":        { label: "文本输入", short: "Aa", color: "#6366f1", bg: "#eef2ff" },
  "el-input-number": { label: "数字输入", short: "12", color: "#10b981", bg: "#ecfdf5" },
  "el-switch":       { label: "开关",     short: "⇄",  color: "#f59e0b", bg: "#fffbeb" },
  "el-select":       { label: "下拉选择", short: "☰",  color: "#8b5cf6", bg: "#f5f3ff" },
  "el-textarea":     { label: "多行文本", short: "¶",  color: "#06b6d4", bg: "#ecfeff" },
  "el-checkbox":     { label: "复选框",   short: "☑",  color: "#ef4444", bg: "#fef2f2" },
  "el-checkbox-group":{ label: "多选组",  short: "☑☑",color: "#ec4899", bg: "#fdf2f8" },
  "el-radio":        { label: "单选组",   short: "◉",  color: "#f97316", bg: "#fff7ed" },
  "el-slider":       { label: "滑块",     short: "—",  color: "#6366f1", bg: "#eef2ff" },
  "el-date-picker":  { label: "日期选择", short: "📅", color: "#14b8a6", bg: "#f0fdfa" },
  "el-color-picker": { label: "颜色选择", short: "◐",  color: "#a855f7", bg: "#faf5ff" },
  "el-input-tags":  { label: "标签输入", short: "#",  color: "#0891b2", bg: "#ecfeff" },
};

function formatPreviewValue(val: unknown): string {
  if (val === null || val === undefined || val === "") return "";
  if (typeof val === "boolean") return val ? "true" : "false";
  return String(val);
}

const ComponentPickerModal: FC<Props> = ({ open, varName, varValue, varType, onSelect, onCancel }) => {
  const models = useMemo(() => compatibleModels(varValue, varType), [varValue, varType]);
  const typeLabel = varType ? VAR_TYPE_META[varType]?.label : null;
  const previewStr = formatPreviewValue(varValue);

  const allModels = Object.keys(MODEL_META) as CellModel[];
  const incompatible = allModels.filter((m) => !models.includes(m));

  return (
    <Modal
      title={
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-100 to-indigo-200 flex items-center justify-center shadow-sm">
            <span className="text-indigo-500 text-sm font-bold">⊞</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-sm font-bold text-slate-800">选择控件类型</span>
            <div className="flex items-center gap-1.5">
              <code className="text-[11px] bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-lg font-mono font-semibold">
                {`{${varName}}`}
              </code>
              {previewStr && (
                <span className="text-[11px] text-slate-400">= &quot;{previewStr}&quot;</span>
              )}
            </div>
          </div>
        </div>
      }
      open={open}
      onCancel={onCancel}
      footer={null}
      width={680}
      destroyOnClose
      okButtonProps={{ className: "!rounded-xl" }}
      cancelButtonProps={{ className: "!rounded-xl" }}
    >
      <div className="grid grid-cols-3 gap-3 pt-2">
        {models.map((model) => {
          const meta = MODEL_META[model] ?? { label: model, short: "?", color: "#9ca3af", bg: "#f9fafb" };

          // Build a minimal Cell for MiniPreview with the variable's value
          const previewCell = {
            span: 12,
            model,
            store: varName,
            placeholder: (model === "el-input" || model === "el-textarea" || model === "el-input-tags")
              ? previewStr
              : undefined,
            text: (model === "el-switch" || model === "el-checkbox" || model === "el-radio")
              ? varName
              : undefined,
          };

          return (
            <button
              key={model}
              onClick={() => onSelect(model)}
              className="flex flex-col gap-3 p-4 rounded-2xl border-2 border-slate-100
                hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-100/50 hover:-translate-y-1 hover:bg-white
                transition-all duration-200 cursor-pointer text-left bg-white group"
            >
              <div className="flex items-center gap-2.5">
                <span
                  className="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-bold text-white shadow-sm"
                  style={{ backgroundColor: meta.color }}
                >
                  {meta.short}
                </span>
                <span className="text-xs font-semibold text-slate-700">{meta.label}</span>
                <span className="w-4 h-4 rounded-md bg-slate-50 text-[8px] text-slate-300 flex items-center justify-center ml-auto opacity-0 group-hover:opacity-100 transition-opacity">→</span>
              </div>
              <div className="rounded-xl border border-slate-100 bg-gradient-to-br from-slate-50 to-white px-3.5 py-2.5 min-h-[42px] flex items-center shadow-sm">
                <MiniPreview cell={previewCell} />
              </div>
            </button>
          );
        })}
      </div>

      {incompatible.length > 0 && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <span className="text-[10px] text-slate-400 flex items-center gap-1.5">
            <span className="inline-block w-1 h-1 rounded-full bg-slate-300" />
            根据变量类型{typeLabel && <strong className="text-slate-500 font-semibold">「{typeLabel}」</strong>}，已隐藏不兼容控件：{incompatible.map((m) => MODEL_META[m]?.label ?? m).join("、")}
          </span>
        </div>
      )}
    </Modal>
  );
};

export default ComponentPickerModal;
