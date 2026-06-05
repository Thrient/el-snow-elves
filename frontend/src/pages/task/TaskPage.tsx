import { useRef, useState, useEffect, useMemo, type FC } from "react";
import type React from "react";
import {
  ExportOutlined, ImportOutlined, DeleteOutlined,
  SearchOutlined, AppstoreAddOutlined,
} from "@ant-design/icons";
import { Button, message, Modal, Space, Tooltip, Input, Checkbox, Spin } from "antd";
import type { Task } from "@/types/task.ts";
import TaskConfigModal from "@/components/task-config-modal/TaskConfigModal.tsx";
import TaskCard from "@/pages/task/TaskCard";
import { useSessionStore } from "@/store/session-store.ts";
import { useCharacterStore } from "@/store/character-store.ts";

const TaskPage: FC = () => {
  const appendTask = useSessionStore((s) => s.appendTask);
  const taskList = useCharacterStore((s) => s.taskList);
  const loading = useCharacterStore((s) => s.taskLoading);
  const loadTasks = useCharacterStore((s) => s.loadTasks);
  const updateTaskValues = useCharacterStore((s) => s.updateTaskValues);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadTasks(); }, [loadTasks]);

  const [configOpen, setConfigOpen] = useState(false);
  const [configTask, setConfigTask] = useState<Task | null>(null);
  const [importing, setImporting] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search.trim()) return taskList;
    const q = search.toLowerCase();
    return taskList.filter((t) => t.name.toLowerCase().includes(q));
  }, [taskList, search]);

  const toggleSelect = (id: string) => {
    setSelectedRowKeys((prev) =>
      prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id]
    );
  };

  const filteredIds = useMemo(() => filtered.map((t) => t.id), [filtered]);
  const allSelected = filteredIds.length > 0 && filteredIds.every((id) => selectedRowKeys.includes(id));
  const someSelected = filteredIds.some((id) => selectedRowKeys.includes(id));

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedRowKeys((prev) => prev.filter((id) => !filteredIds.includes(String(id))));
    } else {
      setSelectedRowKeys((prev) => [...new Set([...prev, ...filteredIds])]);
    }
  };

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
      useCharacterStore.getState().loadTasks();
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
        useCharacterStore.getState().loadTasks();
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
        useCharacterStore.getState().loadTasks();
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

  return (
    <div className="page-container">
      {/* ── Header ── */}
      <div className="page-header">
        <div className="page-header__left">
          <span className="page-header__accent" />
          <h2 className="page-header__title">
            任务管理
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[28px] font-bold text-[#1677ff] leading-none tracking-tight">
            {taskList.length}
          </span>
          <span className="text-[12px] text-muted">个任务</span>
        </div>
      </div>

      {/* ── Toolbar ── */}
      <div className="flex items-center justify-between shrink-0 mb-3 gap-3">
        <Input
          prefix={<SearchOutlined className="text-[#b0b5c0]" />}
          placeholder="搜索任务名称..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          size="small"
          className="max-w-260px"
        />
        <Space size="small">
          <Checkbox
            checked={allSelected}
            indeterminate={!allSelected && someSelected}
            onChange={toggleSelectAll}
            className="text-[11px]"
          >
            全选
          </Checkbox>
          {selectedRowKeys.length > 0 && (
            <span className="text-[11px] text-muted font-medium">
              已选 {selectedRowKeys.length} 项
            </span>
          )}
          <Tooltip title="批量导入任务包 (.zip)">
            <Button size="small" icon={<ImportOutlined />} loading={importing} onClick={handleImportClick}>
              导入
            </Button>
          </Tooltip>
          <Tooltip title={selectedRowKeys.length > 0 ? `导出已选的 ${selectedRowKeys.length} 个任务` : '导出全部任务'}>
            <Button size="small" icon={<ExportOutlined />} onClick={handleExportBatch}>
              导出
            </Button>
          </Tooltip>
          <Tooltip title="批量删除选中任务">
            <Button size="small" danger icon={<DeleteOutlined />} disabled={selectedRowKeys.length === 0} onClick={handleDeleteBatch}>
              删除
            </Button>
          </Tooltip>
        </Space>
      </div>

      {/* ── Task grid ── */}
      <div className="page-content thin-scrollbar">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Spin size="default" />
          </div>
        ) : filtered.length > 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {filtered.map((task, i) => (
              <TaskCard
                key={task.id}
                task={task}
                index={i}
                selected={selectedRowKeys.includes(task.id)}
                onToggle={toggleSelect}
                onAppend={() => appendTask({ id: task.id, name: task.name, version: task.version, values: { ...task.values } })}
                onConfig={() => openConfig(task)}
                onExport={() => handleExportSingle(task)}
                onDelete={() => handleDeleteSingle(task)}
              />
            ))}
          </div>
        ) : (
          /* ── Empty state ── */
          <div className="flex flex-col items-center justify-center h-full select-none">
            <div className="w-20 h-20 rounded-full bg-[#f5f7fa] flex items-center justify-center mb-5">
              <AppstoreAddOutlined className="text-[32px] text-[#c8cdd5]" />
            </div>
            <div className="text-[14px] font-medium text-secondary mb-1">
              {search ? '没有匹配的任务' : '暂无任务'}
            </div>
            <div className="text-[12px] text-[#b0b5c0]">
              {search ? '试试其他关键词' : '前往编辑器创建你的第一个自动化任务'}
            </div>
          </div>
        )}
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
