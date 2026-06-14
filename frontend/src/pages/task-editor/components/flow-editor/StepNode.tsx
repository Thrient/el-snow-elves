import { memo, type FC } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { StepNodeData } from "@/types/flow";
import { PlayCircleOutlined, SyncOutlined } from "@ant-design/icons";

const HANDLE_LEFT: Record<string, number> = {
  success: 0.20,
  failure: 0.50,
  next:    0.80,
};

const StepNode: FC<NodeProps & { data: StepNodeData }> = ({ data, selected }) => {
  const { stepName, action, isCommon, isStart } = data;
  const label = typeof stepName === "string" ? stepName : "";
  const borderColor = isCommon ? "#f59e0b" : selected ? "#1677ff" : "#d0d5dd";

  // Human-readable label for expression-based actions
  const actionLabel = (() => {
    if (!action) return null;
    if (action === "{True}") return "✓ 直接通过";
    if (action.startsWith("{")) return action;
    return action;
  })();

  return (
    <div
      className="relative rounded-xl border-2 px-4 pt-3 pb-1.5 min-w-[150px] max-w-[200px] shadow-sm transition-colors"
      style={{ background: selected ? "#eef2ff" : "#fff", borderColor }}
    >
      {/* Loop badge */}
      {data.isMonitorLoop && (
        <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[#722ed1] flex items-center justify-center shadow-sm">
          <SyncOutlined className="text-[8px] text-white" />
        </div>
      )}

      <Handle type="target" position={Position.Top}
        style={{ width: 9, height: 9, background: "#8b8fa3" }} />

      {/* Name row */}
      <div className="flex items-center justify-center gap-1.5 min-w-0">
        {isStart && <PlayCircleOutlined className="text-[#52c41a] text-xs shrink-0" />}
        <span className="text-[13px] font-semibold text-heading truncate" title={label}>{label}</span>
      </div>

      {/* Badge row */}
      <div className="flex justify-center mt-2 gap-1.5 mb-2">
        {action ? (
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium
            ${isCommon ? "bg-[#fff7e6] text-[#f59e0b]" : "bg-[#eef2ff] text-[#1677ff]"}`}>
            {actionLabel}
          </span>
        ) : (
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#f0f2f5] text-[#c0c4cc] font-medium">未配置</span>
        )}
        {isCommon && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#f59e0b15] text-[#f59e0b] font-medium">公共</span>
        )}
      </div>

      {/* Handle labels — spread to match handle offset positions */}
      <div className="flex justify-between px-1" style={{ paddingLeft: "8%", paddingRight: "8%" }}>
        <span className="text-[8px] text-[#52c41a] font-medium">成功</span>
        <span className="text-[8px] text-[#ff4d4f] font-medium">失败</span>
        <span className="text-[8px] text-muted font-medium">下步</span>
      </div>

      <Handle type="source" position={Position.Bottom} id="success"
        style={{ left: `${HANDLE_LEFT.success * 100}%`, width: 9, height: 9, background: "#52c41a", border: "2px solid #fff" }} />
      <Handle type="source" position={Position.Bottom} id="failure"
        style={{ left: `${HANDLE_LEFT.failure * 100}%`, width: 9, height: 9, background: "#ff4d4f", border: "2px solid #fff" }} />
      <Handle type="source" position={Position.Bottom} id="next"
        style={{ left: `${HANDLE_LEFT.next * 100}%`, width: 9, height: 9, background: "#8b8fa3", border: "2px solid #fff" }} />
    </div>
  );
};

export default memo(StepNode);
