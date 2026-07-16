import { type FC } from "react";
import { Button, Checkbox, Tag, Tooltip, Space } from "antd";
import { PlusOutlined, EditOutlined, ExportOutlined, DeleteOutlined } from "@ant-design/icons";
import type { TaskListItem } from "@/types/task";
import VersionTag from "@/components/version-tag/VersionTag";

const TAG_COLORS = ["#1677ff", "#13c2c2", "#2f54eb", "#722ed1", "#fa8c16", "#52c41a"];

interface Props {
  task: TaskListItem;
  index: number;
  selected: boolean;
  selectedVersion: string | null;
  onToggle: (name: string) => void;
  onVersionChange: (name: string, version: string | null) => void;
  onAppend: (name: string, version: string | null) => void;
  onConfig: () => void;
  onExport: () => void;
  onDelete: () => void;
  updateInfo?: {
    name: string
    hubTaskId: number
    localVersion: string
    hubVersion: string
  }
  updating?: boolean
  onUpdate?: () => void
  onDismissUpdate?: () => void
}

function renderPills(task: TaskListItem) {
  const layoutKeys = new Set((task.layout ?? []).flatMap((row: any) => row.map((c: any) => c.store).filter(Boolean)));
  const entries = Object.entries(task.values ?? {}).filter(([k]) => layoutKeys.has(k));
  if (entries.length === 0) {
    return <span className="text-[11px] text-[#ccc] italic">暂无配置项</span>;
  }
  const shown = entries.slice(0, 3);
  const rest = entries.length - shown.length;
  return (
    <Space size={[4, 4]} wrap>
      {shown.map(([key, value], j) => (
        <Tag
          key={key}
          className="h-[22px] leading-[22px] rounded text-white border-none flex items-center text-[11px] m-0 px-2 font-mono"
          style={{ backgroundColor: TAG_COLORS[j % TAG_COLORS.length] }}
        >{`${key}: ${String(value)}`}</Tag>
      ))}
      {rest > 0 && (
        <Tag className="h-[22px] leading-[22px] rounded border-[#eef0f2] text-muted text-[11px] m-0">
          +{rest}
        </Tag>
      )}
    </Space>
  );
}

const TaskCard: FC<Props> = ({ task, index, selected, selectedVersion, onToggle, onVersionChange, onAppend, onConfig, onExport, onDelete, updateInfo, updating, onUpdate, onDismissUpdate }) => {
  const accent = TAG_COLORS[index % TAG_COLORS.length];

  return (
    <div
      className="task-card task-card-enter"
      style={{
        animationDelay: `${index * 50}ms`,
        borderTop: `3px solid ${accent}`,
        ...(selected ? {
          borderColor: accent,
          borderLeftColor: accent,
          borderRightColor: accent,
          borderBottomColor: accent,
          boxShadow: `0 0 0 1px ${accent}40, 0 4px 16px ${accent}18`,
          backgroundColor: `${accent}06`,
        } : {}),
      }}
    >
      {/* ── top row: checkbox + version ── */}
      <div className="flex items-center justify-between mb-2">
        <Checkbox checked={selected} onChange={() => onToggle(task.name)} className="scale-90 origin-left" />
        <VersionTag
          versions={task.versions}
          latest={task.latest}
          selectedVersion={selectedVersion}
          onChange={(v) => onVersionChange(task.name, v)}
        />
      </div>

      {/* ── title ── */}
      <div className="text-[15px] font-semibold text-heading mb-1 leading-tight tracking-tight">
        {(task as any).author && (task as any).author !== "匿名作者" && (
          <span className="text-[#1677ff]/70 font-medium mr-1 select-none">
            @{(task as any).author}
          </span>
        )}
        {task.name}
      </div>

      {/* ── pills ── */}
      <div className="min-h-[22px]">
        {renderPills(task)}
      </div>

      {/* ── update notification (only shown when update available, fills the gap between pills and action bar) ── */}
      {updateInfo && (
        <div className="flex items-center justify-between mt-2 mb-1 px-2.5 py-1.5 rounded text-[12px]"
          style={{ backgroundColor: '#fffbe6', border: '1px solid #ffe58f' }}>
          <span className="flex items-center gap-1.5 text-[#ad6800]">
            <span className="w-1.5 h-1.5 rounded-full inline-block flex-shrink-0" style={{ backgroundColor: '#fa8c16' }} />
            有新版本 v{updateInfo.hubVersion}（当前 v{updateInfo.localVersion}）
          </span>
          <span className="flex items-center gap-1 flex-shrink-0">
            <Button
              size="small"
              type="link"
              className="text-[12px] h-auto p-0"
              style={{ color: '#d48806' }}
              loading={updating}
              onClick={(e) => { e.stopPropagation(); onUpdate?.() }}
            >
              {updating ? '更新中…' : '更新'}
            </Button>
            <span className="text-[#d9d9d9]">|</span>
            <Button
              size="small"
              type="link"
              className="text-[12px] h-auto p-0 text-muted"
              onClick={(e) => { e.stopPropagation(); onDismissUpdate?.() }}
            >
              忽略
            </Button>
          </span>
        </div>
      )}

      {/* ── bottom action bar ── */}
      <div className="flex items-center gap-1 pt-2.5 border-t border-[#f5f5f7] mt-auto">
        <Tooltip title="添加到执行队列">
          <Button type="primary" size="small" icon={<PlusOutlined />} className="text-[12px]" onClick={() => onAppend(task.name, selectedVersion)}>
            添加
          </Button>
        </Tooltip>
        <div className="flex-1" />
        <Tooltip title="配置参数">
          <Button size="small" type="text" icon={<EditOutlined />} onClick={onConfig} />
        </Tooltip>
        <Tooltip title="导出任务">
          <Button size="small" type="text" icon={<ExportOutlined />} onClick={onExport} />
        </Tooltip>
        <Tooltip title="删除任务">
          <Button size="small" type="text" danger icon={<DeleteOutlined />} onClick={onDelete} />
        </Tooltip>
      </div>
    </div>
  );
};

export default TaskCard;
