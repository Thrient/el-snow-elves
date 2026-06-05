import { useMemo, type FC } from "react";
import { Modal } from "antd";
import type { CellModel, VarType } from "@/types/task";
import { compatibleModels } from "@/utils/type-compat";
import { VAR_TYPE_META } from "@/types/variable/system-vars";
import MiniPreview from "@/pages/task-editor/components/mini-preview/MiniPreview";
import { MODEL_META } from "@/types/task-editor/field-config";

interface Props {
  open: boolean;
  varName: string;
  varValue: unknown;
  varType?: VarType;
  onSelect: (model: CellModel) => void;
  onCancel: () => void;
}

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
                hover:border-indigo-300 hover:shadow-lg hover:shadow-indigo-100/50 hover:-translate-y-1 hover:bg-container
                transition-all duration-200 cursor-pointer text-left bg-container group"
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
