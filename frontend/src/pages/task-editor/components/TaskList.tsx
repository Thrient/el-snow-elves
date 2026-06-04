import { useState, useMemo, type FC } from "react";
import { Button, Input, Modal } from "antd";
import { PlusOutlined, CodeOutlined, FolderOpenOutlined, PlayCircleOutlined } from "@ant-design/icons";
import type { FullTask } from "@/types/task-editor";

interface TaskListProps {
  taskList: FullTask[];
  onOpenTask: (task: FullTask) => void;
  onCreateTask: (name: string, version: string, author: string, description: string) => Promise<void>;
}

const TaskList: FC<TaskListProps> = ({ taskList, onOpenTask, onCreateTask }) => {
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newVersion, setNewVersion] = useState("1.0.0");
  const [newAuthor, setNewAuthor] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const filtered = useMemo(
    () => taskList.filter((t) => t.name.toLowerCase().includes(search.toLowerCase())),
    [taskList, search],
  );

  const handleCreate = async () => {
    if (!newName.trim() || !newVersion.trim()) return;
    await onCreateTask(newName.trim(), newVersion.trim(), newAuthor.trim(), newDesc.trim());
    setCreateOpen(false); setNewName(""); setNewVersion("1.0.0"); setNewAuthor(""); setNewDesc("");
  };

  return (
    <div className="page-container !p-0 overflow-hidden">
      <div className="page-header">
        <div className="page-header__left">
          <span className="page-header__accent" />
          <h2 className="page-header__title">任务编辑</h2>
        </div>
        <Button icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建任务</Button>
      </div>
      <div className="flex-1 overflow-y-auto flex justify-center pt-8 pb-4 thin-scrollbar">
        <div className="w-full max-w-lg px-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-2xl bg-[#f0f2f5] flex items-center justify-center mx-auto mb-3">
              <FolderOpenOutlined className="text-2xl text-[#a0aec0]" /></div>
            <h2 className="text-base font-bold text-[#1a1a2e] mb-1">选择或创建任务</h2>
            <p className="text-xs text-[#8b8fa3]">打开已有任务开始编辑，或创建一个新任务</p>
          </div>
          <Input size="large" prefix={<span className="text-[#a0aec0]">🔍</span>}
            placeholder="搜索任务..." value={search} allowClear
            onChange={(e) => setSearch(e.target.value)} className="mb-4" />
          <div className="flex flex-col gap-1 pb-4">
            {filtered.map((t) => (
              <div key={t.id} onClick={() => onOpenTask(t)}
                className="flex items-center gap-4 px-5 py-4 rounded-xl cursor-pointer
                  transition-all hover:scale-[1.01] hover:shadow-card-hover">
                <div className="w-10 h-10 rounded-xl bg-[#f0f2f5] flex items-center justify-center shrink-0">
                  <CodeOutlined className="text-sm text-[#6b7280]" /></div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-[14px] font-semibold text-[#1a1a2e]">{t.name}</span>
                    {t.start && <PlayCircleOutlined className="text-[11px] text-[#52c41a]" />}</div>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-[#9ca3af]">v{t.version}</span>
                    {t.author && <span className="text-xs text-[#9ca3af]">{t.author}</span>}
                    <span className="text-xs text-[#9ca3af]">{Object.keys(t.steps ?? {}).length} 步骤</span></div>
                </div>
                <span className="text-[20px] text-[#d0d5dd]">→</span>
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="text-center py-8 text-sm text-[#9ca3af]">
                {taskList.length === 0 ? "暂无任务，点击「新建任务」开始" : "无匹配结果"}</div>)}
          </div>
        </div>
      </div>
      <Modal title="新建任务" open={createOpen} onOk={handleCreate} onCancel={() => setCreateOpen(false)}
        okText="创建" cancelText="取消">
        <div className="flex flex-col gap-4 pt-3">
          <div className="flex items-center gap-3"><span className="text-sm w-14 shrink-0">名称 *</span>
            <Input placeholder="任务名称" value={newName} onChange={(e) => setNewName(e.target.value)} /></div>
          <div className="flex items-center gap-3"><span className="text-sm w-14 shrink-0">版本 *</span>
            <Input placeholder="1.0.0" value={newVersion} onChange={(e) => setNewVersion(e.target.value)} /></div>
          <div className="flex items-center gap-3"><span className="text-sm w-14 shrink-0">作者</span>
            <Input placeholder="作者" value={newAuthor} onChange={(e) => setNewAuthor(e.target.value)} /></div>
          <div className="flex items-start gap-3"><span className="text-sm w-14 shrink-0 pt-1">描述</span>
            <Input.TextArea placeholder="任务描述" value={newDesc} rows={3} onChange={(e) => setNewDesc(e.target.value)} /></div>
        </div>
      </Modal>
    </div>
  );
};

export default TaskList;
