import type { FC } from "react";
import type { Cell } from "@/types/task";

interface Props {
  cell: Cell;
}

const MiniPreview: FC<Props> = ({ cell }) => {
  const model = cell.model ?? "el-input";
  const label = cell.text;
  const ph = cell.placeholder;

  switch (model) {
    case "el-switch":
      return (
        <span className="inline-flex items-center gap-1.5">
          {label && <span className="text-[10px] font-medium text-slate-600">{label}</span>}
          <span className="inline-block w-7 h-[15px] rounded-full bg-slate-300 relative align-middle shadow-inner">
            <span className="absolute top-[2px] left-[2px] w-[11px] h-[11px] rounded-full bg-white shadow-sm transition-all" />
          </span>
        </span>
      );
    case "el-checkbox":
      return (
        <span className="inline-flex items-center gap-1.5">
          <span className="w-3.5 h-3.5 rounded-[4px] border-2 border-slate-300 bg-white shadow-sm" />
          {label && <span className="text-[10px] font-medium text-slate-600">{label}</span>}
        </span>
      );
    case "el-checkbox-group":
      return (
        <span className="inline-flex flex-col gap-[3px]">
          {label && <span className="text-[10px] font-medium text-slate-600">{label}</span>}
          {(cell.options ?? []).length > 0
            ? cell.options!.slice(0, 3).map((o, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 text-[10px] text-slate-500">
                <span className="w-3 h-3 rounded-[3px] border-2 border-slate-300 bg-white shadow-sm" />{o.label || o.value}
              </span>
            ))
            : <span className="text-[9px] text-slate-300 italic">无选项</span>
          }
        </span>
      );
    case "el-radio":
      return (
        <span className="inline-flex flex-col gap-[3px]">
          {label && <span className="text-[10px] font-medium text-slate-600">{label}</span>}
          {(cell.options ?? []).length > 0
            ? cell.options!.slice(0, 3).map((o, i) => (
              <span key={i} className="inline-flex items-center gap-1.5 text-[10px] text-slate-500">
                <span className="w-3 h-3 rounded-full border-2 border-slate-300 bg-white shadow-sm" />{o.label || o.value}
              </span>
            ))
            : <span className="text-[9px] text-slate-300 italic">无选项</span>
          }
        </span>
      );
    case "el-slider":
      return (
        <span className="inline-flex items-center gap-1.5 w-full">
          {label && <span className="text-[10px] font-medium text-slate-600 shrink-0">{label}</span>}
          <span className="flex-1 h-1.5 rounded-full bg-slate-200 relative shadow-inner">
            <span className="absolute left-[30%] top-[-4px] w-[14px] h-[14px] rounded-full bg-white border-2 border-indigo-400 shadow-md" />
          </span>
        </span>
      );
    case "el-input-number":
      return (
        <span className="inline-flex items-center gap-1.5 w-full">
          {label && <span className="text-[10px] font-medium text-slate-600 shrink-0">{label}</span>}
          <span className="flex-1 h-[22px] rounded-lg border border-slate-200 bg-white px-2.5 flex items-center gap-1 shadow-sm">
            <span className="text-[9px] text-slate-400 w-0 flex-1 truncate">{ph || "0"}</span>
            <span className="flex flex-col leading-none text-slate-300 text-[8px] scale-75">▲▼</span>
          </span>
        </span>
      );
    case "el-select":
      return (
        <span className="inline-flex items-center gap-1.5 w-full">
          {label && <span className="text-[10px] font-medium text-slate-600 shrink-0">{label}</span>}
          <span className="flex-1 h-[22px] rounded-lg border border-slate-200 bg-white px-2.5 flex items-center justify-between shadow-sm">
            <span className="text-[9px] text-slate-400">{ph || "选择..."}</span>
            <span className="text-[8px] text-slate-300 ml-1">▾</span>
          </span>
        </span>
      );
    case "el-textarea":
      return (
        <span className="inline-flex flex-col gap-[3px] w-full">
          {label && <span className="text-[10px] font-medium text-slate-600">{label}</span>}
          <span className="h-[30px] rounded-lg border border-slate-200 bg-white px-2.5 py-1 shadow-sm">
            <span className="text-[9px] text-slate-400">{ph || ""}</span>
          </span>
        </span>
      );
    case "el-date-picker":
      return (
        <span className="inline-flex items-center gap-1.5 w-full">
          {label && <span className="text-[10px] font-medium text-slate-600 shrink-0">{label}</span>}
          <span className="flex-1 h-[22px] rounded-lg border border-slate-200 bg-white px-2.5 flex items-center gap-1 shadow-sm">
            <span className="text-[10px] opacity-60">📅</span>
            <span className="text-[9px] text-slate-400">{ph || cell.format || "YYYY-MM-DD"}</span>
          </span>
        </span>
      );
    case "el-color-picker":
      return (
        <span className="inline-flex items-center gap-1.5">
          {label && <span className="text-[10px] font-medium text-slate-600">{label}</span>}
          <span className="w-[22px] h-[22px] rounded-lg border border-slate-200 shadow-sm bg-gradient-to-br from-rose-400 via-emerald-400 to-blue-400" />
        </span>
      );
    case "el-input-tags":
      return (
        <span className="inline-flex items-center gap-1.5 w-full">
          {label && <span className="text-[10px] font-medium text-slate-600 shrink-0">{label}</span>}
          <span className="flex-1 min-h-[22px] rounded-lg border border-dashed border-cyan-200 bg-cyan-50/40 px-2 py-1 flex items-center gap-1 shadow-sm">
            <span className="w-4 h-3.5 rounded-sm bg-cyan-100 border border-cyan-200 flex items-center justify-center text-[8px] text-cyan-500 font-semibold">Aa</span>
            <span className="text-[9px] text-cyan-300 italic">{ph || "标签..."}</span>
            <span className="text-[9px] text-cyan-300 ml-auto">⌨</span>
          </span>
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1.5 w-full">
          {label && <span className="text-[10px] font-medium text-slate-600 shrink-0">{label}</span>}
          <span className="flex-1 h-[22px] rounded-lg border border-slate-200 bg-white px-2.5 flex items-center shadow-sm">
            <span className="text-[9px] text-slate-400">{ph || ""}</span>
          </span>
        </span>
      );
  }
};

export default MiniPreview;
