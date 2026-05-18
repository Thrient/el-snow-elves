import { type FC, useEffect, useState } from "react";
import { Cron } from "croner";
import {
  ClearOutlined,
  ClockCircleOutlined,
  CloseOutlined,
  DeleteOutlined,
  DesktopOutlined,
  LockOutlined,
  MinusCircleOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  StopOutlined,
  UnlockOutlined,
} from "@ant-design/icons";
import { Button, Select, Slider, Space, Switch, Tag, Empty } from "antd";
import type { Task } from "@/types/task.ts";
import { useCharacterStore } from "@/store/character.ts";
import HwndPreviewModal from "@/components/hwnd-preview-modal/HwndPreviewModal.tsx";
import { useUserStore, type PlanEntry } from "@/store/user-store.ts";
import { useTaskStore } from "@/store/task-store.ts";
import { PLAN_TEMPLATES } from "@/types/plan.ts";
import type { PlanBase } from "@/types/plan.ts";
import cronstrue from "cronstrue";
import "cronstrue/locales/zh_CN";
import TaskConfigModal from "@/components/task-config-modal/TaskConfigModal.tsx";
import PlanModal from "@/pages/plans/PlanModal.tsx";

const DOT_COLORS = ["#1677ff", "#52c41a", "#fa8c16", "#722ed1", "#13c2c2"];

const WindowsPage: FC = () => {
  const userStore = useUserStore();
  const characterStore = useCharacterStore();
  const [modalOpen, setModalOpen] = useState(false);
  const [dragUid, setDragUid] = useState<number | null>(null);
  const [configOpen, setConfigOpen] = useState(false);
  const [configTask, setConfigTask] = useState<Task | null>(null);
  const [configUid, setConfigUid] = useState<number | null>(null);
  const [planEditOpen, setPlanEditOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<PlanEntry | null>(null);

  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const selectedCharacter = characterStore.selectedHwnd
    ? characterStore.characters.find((c) => c.hwnd === characterStore.selectedHwnd)
    : undefined;

  const closeModal = () => setModalOpen(false);
  const bind = () => setModalOpen(true);

  const openConfig = (uid: number) => {
    if (!selectedCharacter) return;
    const item = selectedCharacter.executeList.find((i) => i._uid === uid);
    if (!item) return;
    const original = useTaskStore.getState().taskList.find((t) => t.id === item.id);
    if (original) { setConfigUid(uid); setConfigTask({ ...original, values: { ...item.values } }); setConfigOpen(true); }
  };
  const closeConfig = () => { setConfigOpen(false); setConfigTask(null); setConfigUid(null); };
  const handleConfigSave = (values: Record<string, unknown>) => {
    if (configUid !== null && selectedCharacter) characterStore.updateExecuteValues(selectedCharacter.hwnd, configUid, values);
    closeConfig();
  };

  const handleDragStart = (uid: number) => (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", String(uid)); setDragUid(uid);
  };
  const handleDragEnd = () => setDragUid(null);
  const handleDragOver = (e: React.DragEvent) => { e.preventDefault(); e.dataTransfer.dropEffect = "move"; };
  const handleDrop = (targetUid: number) => (e: React.DragEvent) => {
    e.preventDefault();
    const sourceUid = Number(e.dataTransfer.getData("text/plain"));
    if (isNaN(sourceUid) || sourceUid === targetUid || !selectedCharacter) return;
    const uids = selectedCharacter.executeList.map((item) => item._uid);
    const sourceIdx = uids.indexOf(sourceUid), targetIdx = uids.indexOf(targetUid);
    if (sourceIdx === -1 || targetIdx === -1) return;
    uids.splice(sourceIdx, 1); uids.splice(targetIdx, 0, sourceUid);
    characterStore.reorderExecute(selectedCharacter.hwnd, uids); setDragUid(null);
  };

  const openPlanEdit = (plan: PlanEntry) => {
    setEditingPlan(plan);
    setPlanEditOpen(true);
  };
  const savePlanEdit = (planBase: PlanBase) => {
    if (!editingPlan) return;
    userStore.updatePlan(editingPlan._uid, planBase);
    if (selectedCharacter) {
      characterStore.setPlans(selectedCharacter.hwnd, useUserStore.getState().plans);
    }
    setPlanEditOpen(false);
    setEditingPlan(null);
  };

  const handleToggleLock = () => {
    if (!characterStore.selectedHwnd) return;
    const hwnd = characterStore.selectedHwnd;
    const isLocked = selectedCharacter?.locked ?? true;
    const action = isLocked ? "API:SCRIPT:UNLOCK" : "API:SCRIPT:LOCK";
    window.pywebview?.api.emit(action, hwnd).then(() => { characterStore.update({ hwnd, locked: !isLocked }); });
  };

  const taskCount = selectedCharacter?.executeList.length ?? 0;
  const isLocked = selectedCharacter?.locked !== false;
  const hasWindows = characterStore.characters.length > 0;
  const boxShadow = "0 0 0 1px rgba(0,0,0,.03), 0 2px 8px rgba(0,0,0,.04), 0 1px 2px rgba(0,0,0,.06)";

  return (
    <>
      <style>{`@keyframes win-pulse{0%,100%{opacity:1}50%{opacity:.5}}`}</style>
      <div className="flex flex-col h-[calc(100%-48px)] mx-4 mb-4 p-5" style={{ background:"#fdfdfc", borderRadius:12, boxShadow }}>

      {/* ── Header ── */}
      <div className="flex justify-between items-center shrink-0 mb-5">
        <div className="flex items-center gap-3">
          <div style={{ width:3, height:18, borderRadius:2, background:"#1677ff" }} />
          <span style={{ fontSize:15, fontWeight:650, color:"#1e1e24", letterSpacing:"-0.01em" }}>窗口管理</span>
          {hasWindows && (
            <span style={{ fontSize:10, color:"#9ca3af", background:"#f3f4f6", padding:"2px 8px", borderRadius:99, fontWeight:500, letterSpacing:"0.03em" }}>
              {characterStore.characters.length}
            </span>
          )}
        </div>
        <Space size="small">
          <Button size="middle" type="primary" icon={<PlusOutlined />} onClick={bind} style={{ borderRadius:8, fontWeight:500, boxShadow:"0 2px 8px rgba(22,119,255,.2)" }}>绑定窗口</Button>
          {characterStore.selectedHwnd && (
            <Button size="middle" danger icon={<MinusCircleOutlined />} onClick={() => { const hwnd = characterStore.selectedHwnd!; window.pywebview?.api.emit("API:SCRIPT:UNBIND", hwnd).then(() => characterStore.remove(hwnd)); }} style={{ borderRadius:8, fontWeight:500 }}>解绑</Button>
          )}
          <Button size="middle" icon={<DeleteOutlined />} disabled={characterStore.characters.length === 0}
            onClick={async () => {
              for (const c of characterStore.characters) {
                await window.pywebview?.api.emit("API:SCRIPT:UNBIND", c.hwnd);
                characterStore.remove(c.hwnd);
              }
            }}
            style={{ borderRadius:8, fontWeight:500, borderColor: "#fecaca", color: "#dc2626" }}>
            一键解绑
          </Button>
        </Space>
      </div>

      {/* ── Empty state ── */}
      {!selectedCharacter && (
        <div className="flex-1 flex flex-col items-center justify-center" style={{ minHeight:340, gap:20 }}>
          <div style={{ width:80, height:80, borderRadius:24, background:"linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)", display:"flex", alignItems:"center", justifyContent:"center", boxShadow:"0 4px 24px rgba(22,119,255,.08)" }}>
            <DesktopOutlined style={{ fontSize:34, color:"#1677ff" }} />
          </div>
          <div style={{ textAlign:"center" }}>
            <div style={{ fontSize:15, fontWeight:600, color:"#1e1e24", marginBottom:4 }}>{!hasWindows ? "开始管理游戏窗口" : "选择要管理的窗口"}</div>
            <div style={{ fontSize:12, color:"#9ca3af", lineHeight:1.6 }}>
              {!hasWindows ? "绑定游戏窗口后，即可管理脚本执行、窗口透明度与锁定状态" : "从下方选择已绑定的窗口，查看任务队列与执行计划"}
            </div>
          </div>
          {!hasWindows ? (
            <Button type="primary" size="middle" icon={<PlusOutlined />} onClick={bind} style={{ borderRadius:8 }}>立即绑定</Button>
          ) : (
            <Select style={{ width:300 }} placeholder="选择游戏窗口"
              value={undefined} onChange={(v) => characterStore.setSelectedHwnd(v ?? null)}>
              {characterStore.characters.map((c) => (
                <Select.Option key={c.hwnd} value={c.hwnd}>
                  <Space>
                    {c.character ? <img style={{ height:16, borderRadius:3 }} src={c.character} alt="" /> : <DesktopOutlined style={{ fontSize:12, color:"#9ca3af" }} />}
                    <Tag color={c.running ? "green" : "default"} style={{ fontSize:10, lineHeight:1, margin:0 }}>{c.running ? "运行中" : "已停止"}</Tag>
                  </Space>
                </Select.Option>
              ))}
            </Select>
          )}
        </div>
      )}

      {/* ── Dashboard ── */}
      {selectedCharacter && (
        <>
          {/* Control panel */}
          <div className="shrink-0 mb-4" style={{ background:"#f8f9fb", borderRadius:12, border:"1px solid #eef0f2", padding:"16px 20px" }}>

            {/* Row 1: select + opacity */}
            <div className="flex items-center gap-4 mb-3">
              <Select style={{ width:244 }} placeholder="选择游戏窗口"
                value={characterStore.selectedHwnd ?? undefined}
                onChange={(v) => characterStore.setSelectedHwnd(v ?? null)}
                onClear={() => characterStore.setSelectedHwnd(null)}>
                {characterStore.characters.map((c) => (
                  <Select.Option key={c.hwnd} value={c.hwnd}>
                    <Space>
                      {c.character ? <img style={{ height:16, borderRadius:3 }} src={c.character} alt="" /> : <DesktopOutlined style={{ fontSize:12, color:"#9ca3af" }} />}
                      <Tag color={c.running ? "green" : "default"} style={{ fontSize:10, lineHeight:1, margin:0 }}>{c.running ? "运行中" : "已停止"}</Tag>
                    </Space>
                  </Select.Option>
                ))}
              </Select>

              <div className="ml-auto flex items-center gap-3" style={{ minWidth:180 }}>
                <span style={{ fontSize:10, color:"#9ca3af", fontWeight:500, textTransform:"uppercase", letterSpacing:"0.06em" }}>透明度</span>
                <Slider style={{ width:96, margin:0 }} min={0} max={255}
                  value={selectedCharacter?.opacity ?? 255}
                  onChange={(v) => { characterStore.update({ hwnd: selectedCharacter.hwnd, opacity: v }); window.pywebview?.api.emit("API:SCRIPT:SET_OPACITY", selectedCharacter.hwnd, v); }}
                  styles={{ track: { background: "#1677ff" }, rail: { background: "#e5e7eb" } }} />
                <span style={{ fontSize:12, fontWeight:600, color:"#374151", fontFamily:"ui-monospace, Consolas, monospace", width:28, textAlign:"right" }}>{selectedCharacter?.opacity ?? 255}</span>
              </div>
            </div>

            {/* Row 2: actions + status */}
            <div className="flex items-center gap-2">
              <Button
                type={selectedCharacter?.running ? "default" : "primary"}
                icon={selectedCharacter?.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                style={{ borderRadius:8, fontWeight:500, ...(selectedCharacter?.running ? {} : { boxShadow:"0 2px 8px rgba(22,119,255,.2)" }) }}
                onClick={() => {
                  const hwnd = characterStore.selectedHwnd!;
                  const wasRunning = selectedCharacter?.running;
                  window.pywebview?.api.emit(wasRunning ? "API:SCRIPT:PAUSE" : "API:SCRIPT:RESUME", hwnd).then(() => {
                    const ch = useCharacterStore.getState().characters.find((c) => c.hwnd === hwnd);
                    if (ch) characterStore.update({ hwnd, running: !ch.running });
                  });
                }}
              >{selectedCharacter?.running ? "暂停" : "开始执行"}</Button>

              <Button
                icon={<StopOutlined />}
                disabled={!selectedCharacter?.running}
                onClick={async () => {
                  const hwnd = characterStore.selectedHwnd!;
                  await window.pywebview?.api.emit("API:SCRIPT:STOP", hwnd);
                  characterStore.update({ hwnd, running: false, currentTask: null });
                }}
                style={{ borderRadius:8, fontWeight:500, borderColor: "#fecaca", color: "#dc2626" }}>
                结束任务
              </Button>

              <Button
                icon={isLocked ? <LockOutlined /> : <UnlockOutlined />}
                onClick={handleToggleLock}
                style={{
                  borderRadius:8, fontWeight:500,
                  borderColor: isLocked ? "#fed7aa" : "#bbf7d0",
                  color: isLocked ? "#c2410c" : "#15803d",
                  background: isLocked ? "#fff7ed" : "#f0fdf4",
                }}
              >{isLocked ? "已锁定" : "已解锁"}</Button>

              <Button icon={<ClearOutlined />} disabled={taskCount === 0}
                onClick={() => characterStore.clearExecute(selectedCharacter.hwnd)}
                style={{ borderRadius:8, fontWeight:500 }}>
                {taskCount > 0 ? `清空队列 (${taskCount})` : "清空队列"}
              </Button>

              <div className="ml-auto flex items-center gap-2" style={{ padding:"4px 14px", borderRadius:8, background:"#fff", border:"1px solid #eef0f2" }}>
                <div style={{ width:7, height:7, borderRadius:"50%", background: selectedCharacter.currentTask ? "#52c41a" : "#d1d5db",
                  boxShadow: selectedCharacter.currentTask ? "0 0 6px rgba(82,196,26,.4)" : undefined }} />
                <span style={{ fontSize:10, color:"#9ca3af" }}>当前任务</span>
                <span style={{ fontSize:12, fontWeight:500, color:"#1e1e24", maxWidth:160 }} className="truncate">{selectedCharacter.currentTask ?? "—"}</span>
              </div>
            </div>
          </div>

          {/* Bottom panels */}
          <div className="flex-1 min-h-0 grid grid-cols-2 gap-4">
            {/* ── Tasks ── */}
            <div className="flex flex-col min-h-0" style={{ background:"#fff", borderRadius:12, border:"1px solid #eef0f2", overflow:"hidden", boxShadow:"0 1px 3px rgba(0,0,0,.03)" }}>
              <div className="shrink-0 flex items-center justify-between px-5 py-3" style={{ borderBottom:"1px solid #f3f4f6", background:"#fdfdfc" }}>
                <div className="flex items-center gap-2.5">
                  <span style={{ fontSize:13, fontWeight:600, color:"#1e1e24" }}>待执行任务</span>
                  <span style={{ fontSize:11, fontWeight:600, color:"#1677ff", background:"#eff6ff", padding:"2px 8px", borderRadius:99, fontFamily:"ui-monospace,Consolas,monospace" }}>{taskCount}</span>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4" style={{ background:"#fdfdfc" }}>
                {taskCount === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center gap-1">
                    <Empty description={<span style={{fontSize:12,color:"#b0b8c4"}}>队列为空</span>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
                    <span style={{fontSize:11,color:"#d1d5db"}}>从任务列表添加任务</span>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {selectedCharacter.executeList.map((item, idx) => (
                      <div key={item._uid} draggable
                        onDragStart={handleDragStart(item._uid)} onDragEnd={handleDragEnd}
                        onDragOver={handleDragOver} onDrop={handleDrop(item._uid)}
                        onClick={() => openConfig(item._uid)}
                        className="flex items-center justify-between gap-2 px-3.5 py-2.5 cursor-pointer transition-all duration-150 group"
                        style={{ background:"#fff", borderRadius:10, border:"1px solid #eef0f2", opacity:dragUid===item._uid?0.3:1,
                          borderLeft:"3px solid "+DOT_COLORS[idx%DOT_COLORS.length], boxShadow:"0 1px 2px rgba(0,0,0,.02)" }}
                        onMouseEnter={(e)=>{e.currentTarget.style.borderColor="#d0d4dd";e.currentTarget.style.boxShadow="0 4px 12px rgba(0,0,0,.04)"}}
                        onMouseLeave={(e)=>{e.currentTarget.style.borderColor="#eef0f2";e.currentTarget.style.boxShadow="0 1px 2px rgba(0,0,0,.02)"}}>
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span style={{fontSize:12,fontWeight:500,color:"#1e1e24"}} className="truncate">{item.name}</span>
                          <Tag style={{fontSize:9,lineHeight:1,border:"none",borderRadius:4,padding:"1px 6px",margin:0,color:"#9ca3af",background:"#f3f4f6",fontFamily:"ui-monospace,Consolas,monospace"}}>v{item.version}</Tag>
                        </div>
                        <span className="flex items-center justify-center w-6 h-6 cursor-pointer opacity-0 group-hover:opacity-100 transition-all shrink-0"
                          style={{borderRadius:6,color:"#d1d5db"}}
                          onMouseEnter={(e)=>{e.currentTarget.style.color="#ef4444";e.currentTarget.style.background="#fef2f2"}}
                          onMouseLeave={(e)=>{e.currentTarget.style.color="#d1d5db";e.currentTarget.style.background="transparent"}}
                          onClick={(e)=>{e.stopPropagation();characterStore.removeExecute(selectedCharacter.hwnd,item._uid)}}>
                          <CloseOutlined style={{fontSize:10}} />
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* ── Plans ── */}
            <div className="flex flex-col min-h-0" style={{ background:"#fff", borderRadius:12, border:"1px solid #eef0f2", overflow:"hidden", boxShadow:"0 1px 3px rgba(0,0,0,.03)" }}>
              <div className="shrink-0 flex items-center justify-between px-5 py-3" style={{ borderBottom:"1px solid #f3f4f6", background:"#fdfdfc" }}>
                <div className="flex items-center gap-2.5">
                  <span style={{ fontSize:13, fontWeight:600, color:"#1e1e24" }}>执行计划</span>
                  <span style={{ fontSize:11, color:"#9ca3af", background:"#f3f4f6", padding:"2px 8px", borderRadius:99, fontFamily:"ui-monospace,Consolas,monospace" }}>{selectedCharacter.plans.length}</span>
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-4" style={{ background:"#fdfdfc" }}>
                {!selectedCharacter.plans?.length ? (
                  <div className="h-full flex flex-col items-center justify-center gap-1">
                    <Empty description={<span style={{fontSize:12,color:"#b0b8c4"}}>暂无计划</span>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
                    <span style={{fontSize:11,color:"#d1d5db"}}>在计划页面创建定时任务</span>
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {selectedCharacter.plans.map((planBase) => {
                      const plan = planBase as PlanEntry;
                      const tmpl = PLAN_TEMPLATES.find((t) => t.id === plan.templateId);
                      const cronHuman = (()=>{try{return cronstrue.toString(plan.cron,{locale:"zh_CN"})}catch{return plan.cron}})();
                      let nextRun: Date|null = null; let secondsLeft = -1;
                      if (plan.enabled) { try { nextRun = new Cron(plan.cron).nextRun() } catch {} if (nextRun) secondsLeft = Math.max(0, Math.floor((nextRun.getTime()-now)/1000)); }
                      return (
                        <div key={`${plan._uid}`} className="transition-all duration-200 group cursor-pointer"
                          onClick={() => openPlanEdit(plan)}
                          style={{ background:"#fff", borderRadius:10, border:`1px solid ${plan.enabled?"#d0d4dd":"#eef0f2"}`, overflow:"hidden", boxShadow:plan.enabled?"0 2px 8px rgba(0,0,0,.03)":"0 1px 2px rgba(0,0,0,.01)" }}>
                          <div className="flex items-center gap-1.5 px-3.5 py-2.5">
                            <span onClick={(e) => e.stopPropagation()}>
                              <Switch size="small" checked={plan.enabled}
                                onChange={() => { userStore.togglePlan(plan._uid); characterStore.setPlans(selectedCharacter.hwnd, useUserStore.getState().plans); }} />
                            </span>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1.5 mb-0.5">
                                <span style={{fontSize:12,fontWeight:600,color:"#1e1e24"}} className="truncate">{plan.name}</span>
                                {tmpl && <Tag style={{fontSize:8,lineHeight:1,border:"none",borderRadius:4,padding:"1px 6px",margin:0,color:"#6366f1",background:"#eef2ff"}}>{tmpl.name}</Tag>}
                              </div>
                              <div className="flex items-center gap-1" style={{fontSize:10,color:"#9ca3af"}}>
                                <ClockCircleOutlined style={{fontSize:9}} />
                                <span style={{fontFamily:"ui-monospace,Consolas,monospace"}}>{plan.cron}</span>
                                <span style={{color:"#d1d5db"}}>·</span>
                                <span className="truncate">{cronHuman}</span>
                              </div>
                            </div>
                            <span onClick={(e)=>{e.stopPropagation();userStore.removePlan(plan._uid);characterStore.setPlans(selectedCharacter.hwnd,useUserStore.getState().plans)}}
                              className="flex items-center justify-center w-6 h-6 cursor-pointer opacity-0 group-hover:opacity-100 transition-all shrink-0 select-none"
                              style={{borderRadius:6,color:"#d1d5db"}}
                              onMouseEnter={(e)=>{e.currentTarget.style.color="#ef4444";e.currentTarget.style.background="#fef2f2"}}
                              onMouseLeave={(e)=>{e.currentTarget.style.color="#d1d5db";e.currentTarget.style.background="transparent"}}>
                              <DeleteOutlined style={{fontSize:12}} />
                            </span>
                          </div>
                          {plan.enabled && nextRun && (
                            <div className="px-3.5 pb-2.5">
                              {secondsLeft <= 60 ? (
                                <div className="flex items-center gap-2 px-3 py-2" style={{ background:"linear-gradient(135deg, #fffbeb, #fef3c7)", borderRadius:8, border:"1px solid #fde68a" }}>
                                  <div style={{ width:18,height:18,borderRadius:"50%",background:"#f59e0b",display:"flex",alignItems:"center",justifyContent:"center",fontSize:9,fontWeight:700,color:"#fff",animation:"win-pulse 1s infinite"}}>!</div>
                                  <span style={{fontSize:10,fontWeight:600,color:"#92400e"}}>即将执行</span>
                                  <span style={{fontSize:12,fontWeight:700,color:"#d97706",marginLeft:"auto",fontFamily:"ui-monospace,Consolas,monospace"}}>{secondsLeft}s</span>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2 px-3 py-1.5" style={{fontSize:10,color:"#9ca3af",background:"#f9fafb",borderRadius:8}}>
                                  <span>下次</span>
                                  <span style={{fontWeight:600,color:"#374151",marginLeft:"auto"}}>{nextRun.toLocaleDateString("zh-CN",{month:"short",day:"numeric"})} {nextRun.toLocaleTimeString("zh-CN",{hour:"2-digit",minute:"2-digit"})}</span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {modalOpen && (
        <HwndPreviewModal onClose={closeModal}
          onSelect={(hwnd:string)=>{window.pywebview?.api.emit("API:SCRIPT:BIND",hwnd).then(()=>{characterStore.add({character:"",hwnd,running:true,locked:true,opacity:255,currentTask:null,executeList:userStore.queue.map(t=>({id:t.id,name:t.name,version:t.version,values:t.values})),plans:userStore.plans});characterStore.setSelectedHwnd(hwnd)})}}
          onSelectAll={async(hwnds:string[])=>{const bound=new Set(characterStore.characters.map(c=>c.hwnd));for(const hwnd of hwnds){if(bound.has(hwnd))continue;await window.pywebview?.api.emit("API:SCRIPT:BIND",hwnd);characterStore.add({character:"",hwnd,running:true,locked:true,opacity:255,currentTask:null,executeList:userStore.queue.map(t=>({id:t.id,name:t.name,version:t.version,values:t.values})),plans:userStore.plans})}}}
        />
      )}

      <TaskConfigModal key={configUid??"none"} open={configOpen} task={configTask} onClose={closeConfig} onSave={handleConfigSave} />

      <PlanModal
        open={planEditOpen}
        plan={editingPlan}
        onClose={() => { setPlanEditOpen(false); setEditingPlan(null); }}
        onSave={savePlanEdit}
      />
    </div>
    </>
  );
};

export default WindowsPage;
