import { useRef, type FC } from "react";
import { useState } from "react";
import {
  PlusOutlined, EditOutlined, ProfileOutlined,
  ExportOutlined, ImportOutlined,
} from "@ant-design/icons";
import { Button, Space, Table, Tag, message } from "antd";
import TaskConfigModal from "@/components/task-config-modal/TaskConfigModal.tsx";
import type { ColumnsType } from "antd/es/table";
import type { Task } from "@/types/task.ts";
import { useUserStore } from "@/store/user-store.ts";
import { useTaskStore } from "@/store/task-store.ts";

const TAG_COLORS = ['#1677ff', '#13c2c2', '#2f54eb', '#722ed1', '#fa8c16', '#52c41a']

const TaskPage: FC = () => {
  const appendTask = useUserStore((s) => s.appendTask);
  const taskList = useTaskStore((s) => s.taskList);
  const loading = useTaskStore((s) => s.loading);
  const updateTaskValues = useTaskStore((s) => s.updateTaskValues);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [configOpen, setConfigOpen] = useState(false);
  const [configTask, setConfigTask] = useState<Task | null>(null);
  const [importing, setImporting] = useState(false);

  const handleExport = async (task: Task) => {
    try {
      const result = await window.pywebview?.api.emit("API:TASK:EXPORT", task.id);
      if (!result) return;
      if (result.error) { message.error(result.error); return; }
      if (result.cancelled) return;
      if (result.success) { message.success(`导出成功：${result.path}`); }
    } catch { message.error("导出失败"); }
  };

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          resolve(result.slice(result.indexOf(",") + 1));
        };
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(file);
      });
      const result = await window.pywebview?.api.emit("API:TASK:IMPORT", base64);
      if (result?.error) {
        message.error(result.error);
      } else if (result?.name) {
        message.success(`导入成功：${result.name} v${result.version}（${result.author}）`);
        useTaskStore.getState().loadTasks();
      } else {
        message.error("导入失败：未知错误");
      }
    } catch { message.error("导入失败"); }
    finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const openConfig = (task: Task) => {
    setConfigTask(task);
    setConfigOpen(true);
  };

  const closeConfig = () => {
    setConfigTask(null);
    setConfigOpen(false);
  };

  const handleConfigSave = (values: Record<string, unknown>) => {
    if (configTask) {
      updateTaskValues(configTask.id, values);
    }
    closeConfig();
  };

  const columns: ColumnsType<Task> = [
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
      width: 160,
      render: (name: string) => (
        <span className="font-medium text-[#1a1a2e]">{name}</span>
      ),
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      render: (v: string) => (
        <Tag className="m-0 text-[11px] bg-[#f0f2f5] text-[#8b8fa3] border-none rounded font-mono">{v}</Tag>
      ),
    },
    {
      title: '作者',
      dataIndex: 'author',
      key: 'author',
      width: 100,
      render: (author: string) => (
        <span className="text-[#6b7280] text-[13px]">{author || '—'}</span>
      ),
    },
    {
      title: '配置项',
      key: 'config',
      render: (_, record) => {
        // 只展示已布局的变量，未布局的是内置变量不对外暴露
        const layoutKeys = new Set((record.layout ?? []).flatMap((row) => row.map((c) => c.store).filter(Boolean)));
        const entries = Object.entries(record.values).filter(([k]) => layoutKeys.has(k));
        if (entries.length === 0) {
          return <span className="text-[#ccc] text-xs">暂无配置</span>;
        }
        const shown = entries.slice(0, 4);
        const rest = entries.length - shown.length;
        return (
          <Space size={[4, 4]} wrap>
            {shown.map(([key, value], i) => (
              <Tag
                key={key}
                className="h-6 leading-6 rounded text-white border-none flex items-center text-[11px] m-0 px-2"
                style={{ backgroundColor: TAG_COLORS[i % TAG_COLORS.length] }}
              >{`${key}: ${String(value)}`}</Tag>
            ))}
            {rest > 0 && (
              <Tag className="h-6 leading-6 rounded border-[#eef0f2] text-[#8b8fa3] text-[11px] m-0">
                +{rest}
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 240,
      render: (_, record) => (
        <Space size={8}>
          <Button
            size="small"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => appendTask({
              id: record.id,
              name: record.name,
              version: record.version,
              values: { ...record.values },
            })}
          >
            添加
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => openConfig(record)}
          >
            配置
          </Button>
          <Button
            size="small"
            icon={<ExportOutlined />}
            onClick={() => handleExport(record)}
          >
            导出
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div className="flex flex-col h-full bg-white rounded-lg mx-4 mb-4 p-4 shadow-sm">
      <div className="flex items-center justify-between h-10 shrink-0 mb-1">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 rounded-full bg-[#1677ff]" />
          <span className="text-base font-semibold text-[#1a1a2e] tracking-tight">
            <ProfileOutlined className="mr-2 text-[#1677ff]" />
            任务管理
          </span>
          <span className="text-xs text-[#8b8fa3] bg-[#f5f5f7] px-2 py-0.5 rounded-full">
            {taskList.length}
          </span>
        </div>
        <Button icon={<ImportOutlined />} loading={importing} onClick={() => fileInputRef.current?.click()}>
          导入
        </Button>
      </div>

      <div className="flex-1 min-h-0">
        <Table
          columns={columns}
          dataSource={taskList}
          rowKey="id"
          size="middle"
          pagination={false}
          loading={loading}
          locale={{ emptyText: '暂无任务，请在编辑器新建' }}
          rowClassName={() => 'group'}
        />
      </div>

      <TaskConfigModal
        key={configTask?.id ?? "none"}
        open={configOpen}
        task={configTask}
        onClose={closeConfig}
        onSave={handleConfigSave}
      />

      <input
        ref={fileInputRef}
        type="file"
        accept=".zip"
        className="hidden"
        onChange={handleImportFile}
      />
    </div>
  )
}

export default TaskPage;
