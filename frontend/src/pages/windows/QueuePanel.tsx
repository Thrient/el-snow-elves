import { type FC, useState } from "react";
import { Tag, Empty } from "antd";
import { CloseOutlined } from "@ant-design/icons";
import { useCharacterStore } from "@/store/character-store";
import TaskConfigModal from "@/components/task-config-modal/TaskConfigModal";
import VersionTag from "@/components/version-tag/VersionTag";
import AuthorTag from "@/components/author-tag/AuthorTag";
import type { Task } from "@/types/task";
import { mergeValues } from "@/utils/mergeValues";

const DOT_COLORS = ["#1677ff", "#52c41a", "#fa8c16", "#722ed1", "#13c2c2"];

const QueuePanel: FC = () => {
  const characterStore = useCharacterStore();
  const selected = characterStore.characters.find((c) => c.hwnd === characterStore.selectedHwnd);
  const taskList = characterStore.taskList;
  const [dragUid, setDragUid] = useState<number | null>(null);
  const [configOpen, setConfigOpen] = useState(false);
  const [configTask, setConfigTask] = useState<Task | null>(null);
  const [configUid, setConfigUid] = useState<number | null>(null);

  if (!selected) return null;
  const taskCount = selected.executeList.length;

  const handleDragStart = (uid: number) => (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", String(uid)); setDragUid(uid);
  };
  const handleDragEnd = () => setDragUid(null);
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; };
  const handleDrop = (targetUid: number) => (e: React.DragEvent) => {
    e.preventDefault();
    const sourceUid = Number(e.dataTransfer.getData("text/plain"));
    if (isNaN(sourceUid) || sourceUid === targetUid) return;
    const uids = selected.executeList.map((item) => item._uid);
    const srcIdx = uids.indexOf(sourceUid), tgtIdx = uids.indexOf(targetUid);
    if (srcIdx === -1 || tgtIdx === -1) return;
    uids.splice(srcIdx, 1); uids.splice(tgtIdx, 0, sourceUid);
    characterStore.reorderExecute(selected.hwnd, uids); setDragUid(null);
  };

  const openConfig = (uid: number) => {
    const item = selected.executeList.find((i) => i._uid === uid);
    if (!item) return;
    const taskStore = useCharacterStore.getState();
    const taskName = (item as any).taskName || item.name;
    const itemAuthor = (item as any).author ?? "匿名作者";
    const original = taskStore.taskList.find(
      (t: any) => t.name === taskName && (t.author ?? "匿名作者") === itemAuthor
    );
    if (original) {
      setConfigUid(uid);
      setConfigTask({
        ...original,
        id: "",
        name: original.name,
        version: (item as any).version ?? original.latest,
        values: mergeValues((original as any).values ?? {}, (item as any).values ?? {}),
        valueTypes: (item as any).valueTypes,
      } as any);
      setConfigOpen(true);
    }
  };
  const closeConfig = () => { setConfigOpen(false); setConfigTask(null); setConfigUid(null); };
  const handleSave = (values: Record<string, unknown>) => {
    if (configUid !== null) characterStore.updateExecuteValues(selected.hwnd, configUid, values);
    closeConfig();
  };

  return (
    <>
      <div className="flex flex-col min-h-0 bg-container rounded-xl shadow-sm overflow-hidden">
        <div className="shrink-0 flex items-center justify-between px-4 py-3" style={{ boxShadow: "inset 0 -1px 0 #f3f4f6" }}>
          <div className="flex items-center gap-2.5">
            <span className="text-[13px] font-semibold text-heading">待执行任务</span>
            <span className="text-[11px] font-semibold text-[#1677ff] bg-[#eff6ff] px-2 py-0.5 rounded-full font-mono">
              {taskCount}
            </span>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto thin-scrollbar p-4">
          {taskCount === 0 ? (
            <div className="h-full flex flex-col items-center justify-center gap-2">
              <Empty description={<span className="text-xs text-[#b0b8c4]">队列为空</span>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
              <span className="text-[11px] text-[#d1d5db]">从任务列表添加任务到队列</span>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {selected.executeList.map((item, idx) => {
                const accent = DOT_COLORS[idx % DOT_COLORS.length];
                const taskName = (item as any).taskName || item.name;
                const pinnedVersion = (item as any).version ?? null;
                // 查找对应任务获取可用版本列表
                const taskMeta = taskList.find((t: any) => t.name === taskName);
                const versions = taskMeta?.versions ?? [];
                const latest = taskMeta?.latest ?? "?";
                // 如果锁定了一个不存在的版本，标记为 stale
                const isStale = pinnedVersion !== null && versions.length > 0 && !versions.includes(pinnedVersion);
                // 如果任务本身不存在
                const taskMissing = !taskMeta;

                return (
                  <div key={item._uid} draggable
                    onDragStart={handleDragStart(item._uid)} onDragEnd={handleDragEnd}
                    onDragOver={handleDragOver} onDrop={handleDrop(item._uid)}
                    onClick={() => openConfig(item._uid)}
                    className="queue-item queue-item-enter group"
                    style={{
                      animationDelay: `${idx * 40}ms`,
                      borderLeft: `2px solid ${taskMissing ? "#ff4d4f" : isStale ? "#fa8c16" : accent}`,
                      opacity: dragUid === item._uid ? 0.3 : 1,
                      ...(taskMissing ? { borderColor: "#ffccc7", background: "#fff2f0" } : {}),
                      ...(isStale && !taskMissing ? { borderColor: "#ffe58f", background: "#fffbe6" } : {}),
                    }}
                  >
                    <div className="flex items-center justify-between gap-2 px-3.5 py-2.5">
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <span className="flex-1 min-w-0 text-[12px] font-medium text-heading truncate">
                          {taskName}
                        </span>
                        <span className="flex-1 min-w-0 truncate" onClick={(e) => e.stopPropagation()}>
                          {(() => {
                            const itemAuthor = (item as any).author ?? "匿名作者";
                            const sameNameTasks = taskList.filter((t: any) => t.name === taskName);
                            const availableAuthors = [...new Set(sameNameTasks.map((t: any) => t.author ?? "匿名作者"))];
                            return (
                              <AuthorTag
                                currentAuthor={itemAuthor}
                                availableAuthors={availableAuthors}
                                onChange={(newAuthor) => {
                                  const newTask = sameNameTasks.find((t: any) => (t.author ?? "匿名作者") === newAuthor);
                                  if (newTask) {
                                    characterStore.updateExecuteAuthor(selected.hwnd, item._uid, newAuthor, newTask.latest, newTask.values ?? {});
                                  }
                                }}
                              />
                            );
                          })()}
                        </span>
                        <span className="flex-1 min-w-0 flex justify-end">
                          {taskMissing ? (
                            <Tag style={{ fontSize: 9, lineHeight: 1, border: "none", borderRadius: 4, padding: "1px 6px", margin: 0, color: "#ff4d4f", background: "#fff2f0", fontFamily: "ui-monospace,Consolas,monospace" }}>
                              ⚠️ 任务不存在
                            </Tag>
                          ) : (
                            <div onClick={(e) => e.stopPropagation()}>
                              <VersionTag
                                versions={versions}
                                latest={latest}
                                selectedVersion={pinnedVersion}
                                stale={isStale}
                                onChange={(v) => characterStore.updateExecuteVersion(selected.hwnd, item._uid, v)}
                              />
                            </div>
                          )}
                        </span>
                      </div>
                      <span className="flex items-center justify-center w-6 h-6 cursor-pointer opacity-0 group-hover:opacity-100 transition-all shrink-0"
                        style={{ borderRadius: 6, color: "#d1d5db" }}
                        onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.background = "#fef2f2"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.color = "#d1d5db"; e.currentTarget.style.background = "transparent"; }}
                        onClick={(e) => { e.stopPropagation(); characterStore.removeExecute(selected.hwnd, item._uid); }}>
                        <CloseOutlined style={{ fontSize: 10 }} />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
      <TaskConfigModal key={configUid ?? "none"} open={configOpen} task={configTask} onClose={closeConfig} onSave={handleSave} />
    </>
  );
};

export default QueuePanel;
