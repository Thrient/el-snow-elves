import { useState, type FC } from "react";
import { Input, InputNumber, Modal, Select, Tooltip } from "antd";
import {
  InfoCircleOutlined,
  PlayCircleOutlined,
  FieldTimeOutlined,
  SyncOutlined,
  HolderOutlined,
  PlusOutlined,
  CloseOutlined,
} from "@ant-design/icons";
import type { FullTask } from "@/types/task";
import { useEditorStore } from "@/store/editor-store";

interface Props {
  open: boolean;
  task: FullTask;
  stepNames: string[];
  onClose: () => void;
}

/* ---- Loop step editor ---- */

const LoopStepEditor: FC<{
  steps: string[];
  available: string[];
  onChange: (v: string[]) => void;
}> = ({ steps, available, onChange }) => {
  const [dragIdx, setDragIdx] = useState<number | null>(null);
  const [dragOverIdx, setDragOverIdx] = useState<number | null>(null);
  const [filter, setFilter] = useState("");

  const onDragStart = (i: number) => (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = "move";
    setDragIdx(i);
  };

  const onDragOver = (i: number) => (e: React.DragEvent) => {
    e.preventDefault();
    if (dragIdx !== null && dragIdx !== i) setDragOverIdx(i);
  };

  const onDrop = (i: number) => () => {
    if (dragIdx === null || dragIdx === i) return;
    const next = [...steps];
    const [moved] = next.splice(dragIdx, 1);
    next.splice(i, 0, moved);
    onChange(next);
    setDragIdx(null);
    setDragOverIdx(null);
  };

  const remove = (i: number) => onChange(steps.filter((_, j) => j !== i));

  const availableTags = available.filter((k) => !steps.includes(k));
  const filtered = filter
    ? availableTags.filter((k) => k.toLowerCase().includes(filter.toLowerCase()))
    : availableTags;

  return (
    <div className="space-y-3">
      {/* selected list */}
      <div className="rounded-lg border border-[#e8ecf1] overflow-hidden">
        {steps.length === 0 ? (
          <div className="text-[12px] text-[#c0c4cc] text-center py-6">
            暂未添加 — 从下方可选步骤中点击添加
          </div>
        ) : (
          steps.map((step, i) => (
            <div
              key={step}
              draggable
              onDragStart={onDragStart(i)}
              onDragOver={onDragOver(i)}
              onDragEnd={() => { setDragIdx(null); setDragOverIdx(null); }}
              onDrop={onDrop(i)}
              className={`flex items-center gap-2.5 px-3 py-2 border-b border-[#eef0f2] last:border-b-0 transition-all
                ${dragIdx === i ? "opacity-30" : ""}
                ${dragOverIdx === i ? "border-t-2 border-t-[#1677ff]" : ""}
              `}
            >
              <span className="cursor-grab text-[#c8ccd4] hover:text-[#1677ff] transition-colors">
                <HolderOutlined className="text-[11px]" />
              </span>
              <span className="w-5 h-5 rounded-full bg-[#1677ff10] text-[#1677ff] text-[10px] font-semibold flex items-center justify-center shrink-0">
                {i + 1}
              </span>
              <span className="flex-1 text-[13px] text-[#1a1a2e] font-medium truncate">{step}</span>
              <button
                onClick={() => remove(i)}
                className="w-5 h-5 flex items-center justify-center rounded text-[#c0c4cc] hover:text-[#ff4d4f] hover:bg-[#fff1f0] transition-colors shrink-0"
              >
                <CloseOutlined className="text-[10px]" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* available tags */}
      {availableTags.length > 0 && (
        <>
          {availableTags.length > 6 && (
            <Input
              size="small"
              placeholder="搜索步骤…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              allowClear
              prefix={<span className="text-[#c0c4cc] text-[11px]">⌘</span>}
            />
          )}
          <div className="flex flex-wrap gap-1.5">
            {filtered.map((k) => (
              <button
                key={k}
                onClick={() => onChange([...steps, k])}
                className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full border border-dashed border-[#d0d5dd] text-[#6b7280] bg-white hover:text-[#1677ff] hover:border-[#1677ff] hover:bg-[#f0f5ff] transition-colors cursor-pointer"
              >
                <PlusOutlined className="text-[9px]" />
                {k}
              </button>
            ))}
            {filtered.length === 0 && filter && (
              <span className="text-[11px] text-[#c0c4cc]">无匹配</span>
            )}
          </div>
        </>
      )}
    </div>
  );
};

/* ---- Main ---- */

const TaskSettingsModal: FC<Props> = ({ open, task, stepNames, onClose }) => {
  const updateStart = useEditorStore((s) => s.updateStart);
  const updateMonitors = useEditorStore((s) => s.updateMonitors);

  const startOpts = [...Object.keys(task.steps), ...Object.keys(task.common)];

  return (
    <Modal
      open={open}
      onCancel={onClose}
      centered
      width={600}
      footer={null}
      title={null}
      closable={false}
      styles={{ body: { padding: 0 } }}
    >
      <div className="max-h-[calc(85vh-80px)] overflow-y-auto px-7 py-6 pr-10 thin-scrollbar">
      {/* header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#1677ff] to-[#0958d9] flex items-center justify-center shadow-[0_2px_8px_rgba(22,119,255,0.25)]">
          <InfoCircleOutlined className="text-white text-[15px]" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[16px] font-bold text-[#1a1a2e] leading-tight">任务设置</div>
          <div className="text-[11px] text-[#8b8fa3] truncate">{task.name} · v{task.version}{task.author ? ` · ${task.author}` : ""}</div>
        </div>
        <button
          onClick={onClose}
          className="w-7 h-7 flex items-center justify-center rounded-lg border-0 bg-transparent text-[#c0c4cc] hover:text-[#374151] hover:bg-[#f0f2f5] transition-colors shrink-0 cursor-pointer"
        >
          <CloseOutlined className="text-[12px]" />
        </button>
      </div>

      {/* ── Start step ── */}
      <section className="mb-5">
        <div className="flex items-center gap-2 mb-3">
          <PlayCircleOutlined className="text-[13px] text-[#16a34a]" />
          <span className="text-[13px] font-semibold text-[#1a1a2e]">起始步骤</span>
          <Tooltip title="任务运行时从该步骤开始执行">
            <InfoCircleOutlined className="text-[11px] text-[#c0c4cc] cursor-help" />
          </Tooltip>
        </div>
        <div className="bg-[#f0fdf4] rounded-xl border border-[#bbf7d0] p-4">
          <div className="text-[11px] text-[#8b8fa3] mb-2">选择任务入口步骤</div>
          <Select
            className="w-full"
            size="large"
            placeholder="选择第一个执行的步骤…"
            allowClear
            value={task.start || undefined}
            options={startOpts.map((k) => ({ value: k, label: k }))}
            onChange={(v) => updateStart(v ?? "")}
          />
          {!task.start && (
            <div className="text-[11px] text-[#e07b2c] mt-2 flex items-center gap-1">
              <InfoCircleOutlined />
              未设置起始步骤，任务将按节点顺序执行
            </div>
          )}
        </div>
      </section>

      {/* ── Monitor ── */}
      <section className="mb-5">
        <div className="flex items-center gap-2 mb-3">
          <FieldTimeOutlined className="text-[13px] text-[#722ed1]" />
          <span className="text-[13px] font-semibold text-[#1a1a2e]">监控</span>
        </div>
        <div className="bg-[#faf5ff] rounded-xl border border-[#e9d5ff] p-4 space-y-4">
          {/* interval */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <SyncOutlined className="text-[11px] text-[#722ed1]" />
              <span className="text-[12px] font-medium text-[#374151]">检测间隔</span>
              <span className="text-[11px] text-[#8b8fa3]">— 每隔指定秒数检查窗口状态</span>
            </div>
            <InputNumber
              value={task.monitors.interval ?? 1}
              min={0.1}
              max={60}
              step={0.5}
              size="middle"
              style={{ width: 140 }}
              addonAfter={<span className="text-[11px] text-[#8b8fa3]">秒</span>}
              onChange={(v) => updateMonitors({ ...task.monitors, interval: v ?? 1 })}
            />
          </div>

          {/* divider */}
          <div className="border-t border-[#e9d5ff]" />

          {/* loop steps */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <HolderOutlined className="text-[11px] text-[#722ed1]" />
              <span className="text-[12px] font-medium text-[#374151]">循环步骤</span>
              <span className="text-[11px] text-[#8b8fa3]">— 按顺序循环执行</span>
            </div>
            <LoopStepEditor
              steps={task.monitors.loop ?? []}
              available={stepNames}
              onChange={(loop) => updateMonitors({ ...task.monitors, loop })}
            />
          </div>
        </div>
      </section>

      {/* ── Description ── */}
      <section>
        <div className="flex items-center gap-2 mb-3">
          <InfoCircleOutlined className="text-[13px] text-[#8b8fa3]" />
          <span className="text-[13px] font-semibold text-[#1a1a2e]">描述</span>
          <span className="text-[11px] text-[#8b8fa3]">— 可选</span>
        </div>
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
      </section>
      </div>
    </Modal>
  );
};

export default TaskSettingsModal;
