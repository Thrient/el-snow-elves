import { type FC } from "react";
import { Input, InputNumber, Select } from "antd";
import {
  PlayCircleOutlined,
  FieldTimeOutlined,
  SyncOutlined,
  FileTextOutlined,
  CloseOutlined,
} from "@ant-design/icons";
import type { FullTask } from "@/types/task";
import { useEditorStore } from "@/store/editor-store";

interface Props {
  open: boolean;
  task: FullTask;
  onClose: () => void;
}

const TaskSettingsModal: FC<Props> = ({ open, task, onClose }) => {
  if (!open) return null;

  const updateStart = useEditorStore((s) => s.updateStart);
  const updateMonitors = useEditorStore((s) => s.updateMonitors);

  const startOpts = [...Object.keys(task.steps), ...Object.keys(task.common)];

  /* ---- Row layout helper ---- */
  const Row: FC<{ icon: React.ReactNode; label: string; children: React.ReactNode }> = ({
    icon, label, children,
  }) => (
    <div className="flex items-start gap-3">
      <div className="flex items-center gap-2" style={{ width: 70, flexShrink: 0, paddingTop: 4 }}>
        <span className="text-[15px] leading-none">{icon}</span>
        <span className="text-[12px] font-medium text-muted leading-tight">{label}</span>
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-[1000] bg-black/20" onClick={onClose} />

      {/* Modal */}
      <div
        className="fixed top-1/2 left-1/2 z-[1001] bg-container rounded-2xl shadow-xl overflow-hidden"
        style={{ width: 480, transform: "translate(-50%, -50%)", maxHeight: "calc(100vh - 80px)" }}
      >
        {/* ── Header ── */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4">
          <div className="flex items-center gap-3">
            <span className="inline-block w-1 h-5 rounded-full bg-[#1677ff] shrink-0" />
            <span className="text-[15px] font-semibold text-heading">任务设置</span>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg border-0 bg-transparent text-[#c0c4cc] hover:text-body hover:bg-[#f0f2f5] transition-colors cursor-pointer shrink-0"
          >
            <CloseOutlined className="text-[12px]" />
          </button>
        </div>

        <div className="border-t border-[#f0f0f0]" />

        {/* ── Body ── */}
        <div className="px-6 py-5 space-y-5 overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
          {/* Row 1: 起始步骤 */}
          <Row
            icon={<PlayCircleOutlined className="text-[#16a34a]" />}
            label="起始步骤"
          >
            <Select
              className="w-full"
              size="middle"
              placeholder="选择第一个执行的步骤…"
              allowClear
              value={task.start || undefined}
              options={startOpts.map((k) => ({ value: k, label: k }))}
              onChange={(v) => updateStart(v ?? "")}
            />
          </Row>

          {/* Row 2: 最大时长 */}
          <Row
            icon={<FieldTimeOutlined className="text-[#ef4444]" />}
            label="最大时长"
          >
            <InputNumber
              className="w-full"
              size="middle"
              placeholder="不限制"
              min={0}
              max={86400}
              step={1}
              value={task.monitors.timeout || undefined}
              addonAfter={<span className="text-[11px] text-muted">秒</span>}
              onChange={(v) => updateMonitors({ ...task.monitors, timeout: v ?? undefined })}
            />
          </Row>

          {/* Row 3: 监控间隔 */}
          <Row
            icon={<SyncOutlined className="text-[#722ed1]" />}
            label="监控间隔"
          >
            <InputNumber
              className="w-full"
              size="middle"
              placeholder="1"
              min={0.1}
              max={60}
              step={0.5}
              value={task.monitors.interval ?? 1}
              addonAfter={<span className="text-[11px] text-muted">秒</span>}
              onChange={(v) => updateMonitors({ ...task.monitors, interval: v ?? 1 })}
            />
          </Row>

          {/* Row 4: 备注 */}
          <Row
            icon={<FileTextOutlined className="text-muted" />}
            label="备注"
          >
            <Input.TextArea
              value={task.description}
              rows={4}
              placeholder="添加任务描述，方便后续维护…"
              onChange={(e) => {
                useEditorStore.setState({
                  currentTask: { ...task, description: e.target.value },
                  isDirty: true,
                });
              }}
              className="!text-[13px]"
            />
          </Row>
        </div>
      </div>
    </>
  );
};

export default TaskSettingsModal;
