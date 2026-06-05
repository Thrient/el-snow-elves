import { type FC } from "react";
import { Select } from "antd";
import { CloseOutlined, CheckOutlined, ArrowRightOutlined } from "@ant-design/icons";
import type { Step } from "@/types/task";

interface FlowEditorProps {
  step: Step;
  stepOpts: { value: string; label: string }[];
  stepName: string;
  onUpdate: (field: string, value: unknown) => void;
}

const FlowEditor: FC<FlowEditorProps> = ({ step, stepOpts, stepName, onUpdate }) => {
  const items = [
    { k: "success" as const, label: "成功跳转", hint: "执行成功后跳转", color: "#16a34a", icon: <CheckOutlined /> },
    { k: "failure" as const, label: "失败跳转", hint: "执行失败后跳转", color: "#dc2626", icon: <CloseOutlined /> },
    { k: "next"    as const, label: "无条件跳转", hint: "无论结果都跳转", color: "#6b7280", icon: <ArrowRightOutlined /> },
  ];
  return (
    <div className="space-y-2">
      {items.map(({ k, label, hint, color, icon }) => (
        <div key={k} className="group rounded-xl border border-dashed bg-container transition-colors"
          style={{ borderColor: `${color}4d`, background: `linear-gradient(135deg, ${color}0a, #fff)` }}>
          <div className="flex items-center gap-2 px-3.5 py-2">
            <span className="flex items-center justify-center w-5 h-5 rounded-md shrink-0 text-[13px]"
              style={{ background: `${color}18`, color }}>
              {icon}
            </span>
            <span className="text-[12px] text-body">{label}</span>
            <span className="text-[10px] text-muted">{hint}</span>
            <Select className="flex-1 min-w-0 ml-auto" size="small" allowClear showSearch
              placeholder="选择目标步骤" popupMatchSelectWidth={false}
              value={(step as any)[k] || undefined}
              options={stepOpts.filter(o => o.value !== stepName)}
              onChange={(v) => onUpdate(k, v ?? "")} />
          </div>
        </div>
      ))}
    </div>
  );
};

export default FlowEditor;
