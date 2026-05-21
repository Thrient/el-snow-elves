import { useRef, useState, useEffect, useCallback, type FC } from "react";
import type React from "react";
import {
  PlusOutlined, EditOutlined, ProfileOutlined,
  ExportOutlined, ImportOutlined, DeleteOutlined,
} from "@ant-design/icons";
import { Button, message, Modal, Space, Table, Tag, Tooltip } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { Task } from "@/types/task.ts";
import TaskConfigModal from "@/components/task-config-modal/TaskConfigModal.tsx";
import { useUserStore } from "@/store/user-store.ts";
import { useTaskStore } from "@/store/task-store.ts";

const TAG_COLORS = ['#1677ff', '#13c2c2', '#2f54eb', '#722ed1', '#fa8c16', '#52c41a']

const TaskPage: FC = () => {
  const appendTask = useUserStore((s) => s.appendTask);
  const taskList = useTaskStore((s) => s.taskList);
  const loading = useTaskStore((s) => s.loading);
  const loadTasks = useTaskStore((s) => s.loadTasks);
  const updateTaskValues = useTaskStore((s) => s.updateTaskValues);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const [configOpen, setConfigOpen] = useState(false);
  const [configTask, setConfigTask] = useState<Task | null>(null);
  const [importing, setImporting] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [tableH, setTableH] = useState(400);
  const tableWrapRef = useRef<HTMLDivElement>(null);

  const measure = useCallback(() => {
    if (tableWrapRef.current) setTableH(tableWrapRef.current.clientHeight);
  }, []);

  useEffect(() => {
    measure();
    const ro = new ResizeObserver(measure);
    if (tableWrapRef.current) ro.observe(tableWrapRef.current);
    return () => ro.disconnect();
  }, [measure]);

  // ── Export ──

  const handleExportSingle = async (task: Task) => {
    try {
      const result = await window.pywebview?.api.emit("API:TASK:EXPORT", task.id);
      if (!result) return;
      if (result.error) { message.error(result.error); return; }
      if (result.cancelled) return;
      if (result.success) { message.success(`导出成功：${result.path}`); }
    } catch { message.error("导出失败"); }
  };

  const handleExportBatch = async () => {
    const ids = selectedRowKeys.length > 0 ? selectedRowKeys : taskList.map((t) => t.id);
    if (ids.length === 0) { message.warning("没有可导出的任务"); return; }
    try {
      const result = await window.pywebview?.api.emit("API:TASK:EXPORT:BATCH", ids);
      if (!result) return;
      if (result.cancelled) return;
      if (result.saved?.length) { message.success(`已导出 ${result.saved.length} 个任务`); }
      if (result.errors?.length) { message.error(`${result.errors.length} 个导出失败`); }
    } catch { message.error("导出失败"); }
  };

  // ── Import (batch) ──

  const handleImportClick = () => fileInputRef.current?.click();

  const handleImportFiles = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    setImporting(true);
    try {
      const zipList: string[] = [];
      for (let i = 0; i < files.length; i++) {
        const b64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve((reader.result as string).split(",")[1]);
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(files[i]);
        });
        zipList.push(b64);
      }
      const results = await window.pywebview?.api.emit("API:TASK:IMPORT", zipList);
      if (Array.isArray(results)) {
        const ok = results.filter((r: Record<string, unknown>) => !r.error);
        const fail = results.filter((r: Record<string, unknown>) => r.error);
        if (ok.length) message.success(`成功导入 ${ok.length} 个任务`);
        if (fail.length) message.error(`${fail.length} 个导入失败`);
      }
      useTaskStore.getState().loadTasks();
    } catch { message.error("导入失败"); }
    finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // ── Delete ──

  const handleDeleteSingle = (task: Task) => {
    Modal.confirm({
      title: `删除「${task.name}」？`,
      content: "此操作不可恢复，任务目录和所有模板图片将被永久删除。",
      okText: "删除", okType: "danger", cancelText: "取消",
      onOk: async () => {
        await window.pywebview?.api.emit("API:TASK:DELETE", task.id);
        useTaskStore.getState().loadTasks();
        message.success("任务已删除");
      },
    });
  };

  const handleDeleteBatch = () => {
    if (selectedRowKeys.length === 0) { message.warning("请先选择要删除的任务"); return; }
    Modal.confirm({
      title: `确认删除 ${selectedRowKeys.length} 个任务？`,
      content: "此操作不可恢复，任务目录和所有模板图片将被永久删除。",
      okText: "删除", okType: "danger", cancelText: "取消",
      onOk: async () => {
        for (const id of selectedRowKeys) {
          await window.pywebview?.api.emit("API:TASK:DELETE", id);
        }
        setSelectedRowKeys([]);
        useTaskStore.getState().loadTasks();
        message.success(`已删除 ${selectedRowKeys.length} 个任务`);
      },
    });
  };

  // ── Config ──

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
      width: 160,
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="添加"><Button size="small" type="primary" icon={<PlusOutlined />}
            onClick={() => appendTask({
              id: record.id,
              name: record.name,
              version: record.version,
              values: { ...record.values },
            })} /></Tooltip>
          <Tooltip title="配置"><Button size="small" icon={<EditOutlined />} onClick={() => openConfig(record)} /></Tooltip>
          <Tooltip title="导出"><Button size="small" icon={<ExportOutlined />} onClick={() => handleExportSingle(record)} /></Tooltip>
          <Tooltip title="删除"><Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteSingle(record)} /></Tooltip>
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
        <Space size="small">
          <Tooltip title="批量导入">
            <Button icon={<ImportOutlined />} loading={importing} onClick={handleImportClick} />
          </Tooltip>
          <Tooltip title="批量导出">
            <Button icon={<ExportOutlined />} onClick={handleExportBatch} />
          </Tooltip>
          <Tooltip title="批量删除">
            <Button danger icon={<DeleteOutlined />} disabled={selectedRowKeys.length === 0} onClick={handleDeleteBatch} />
          </Tooltip>
        </Space>
      </div>

      <div ref={tableWrapRef} className="flex-1 min-h-0">
        <Table
          columns={columns}
          dataSource={taskList}
          rowKey="id"
          size="small"
          pagination={false}
          loading={loading}
          locale={{ emptyText: '暂无任务，请在编辑器新建' }}
          scroll={{ y: tableH - 2 }}
          rowClassName={() => 'task-row'}
          rowSelection={{
            selectedRowKeys,
            onChange: (keys) => setSelectedRowKeys(keys),
          }}
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
        multiple
        hidden
        onChange={handleImportFiles}
      />
    </div>
  )
}

export default TaskPage;
