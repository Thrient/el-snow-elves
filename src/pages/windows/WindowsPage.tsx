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
import { Button, Slider, Space, Switch, Tag, Empty } from "antd";
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

  return (
    <>
      <style>{`
        @keyframes win-pulse{0%,100%{opacity:1}50%{opacity:.5}}
        .window-row::-webkit-scrollbar{height:4px}
        .window-row::-webkit-scrollbar-track{background:transparent}
        .window-row::-webkit-scrollbar-thumb{background:#d9dce1;border-radius:2px}
        .window-row::-webkit-scrollbar-thumb:hover{background:#b0b5c0}
        .window-row{scrollbar-width:thin;scrollbar-color:#d9dce1 transparent}
        @keyframes win-card-in{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
        .win-card-enter{animation:win-card-in .3s cubic-bezier(0.16,1,0.3,1) both}
      `}</style>

      <div className="page-container">

        {/* ── Header ── */}
        <div className="page-header">
          <div className="page-header__left">
            <span className="page-header__accent" />
            <h2 className="page-header__title">窗口管理</h2>
            {hasWindows && (
              <span className="page-header__badge">
                {characterStore.characters.length} 个窗口
              </span>
            )}
          </div>
          <Space size="small">
            <Button size="middle" type="primary" icon={<PlusOutlined />} onClick={bind}
              style={{ borderRadius: 8, fontWeight: 500, boxShadow: "0 2px 8px rgba(22,119,255,.2)" }}>
              绑定窗口
            </Button>
            {characterStore.selectedHwnd && (
              <Button size="middle" danger icon={<MinusCircleOutlined />}
                onClick={() => {
                  const hwnd = characterStore.selectedHwnd!;
                  window.pywebview?.api.emit("API:SCRIPT:UNBIND", hwnd).then(() => characterStore.remove(hwnd));
                }}
                style={{ borderRadius: 8, fontWeight: 500 }}>
                解绑
              </Button>
            )}
            <Button size="middle" icon={<DeleteOutlined />} disabled={characterStore.characters.length === 0}
              onClick={async () => {
                for (const c of characterStore.characters) {
                  await window.pywebview?.api.emit("API:SCRIPT:UNBIND", c.hwnd);
                  characterStore.remove(c.hwnd);
                }
              }}
              style={{ borderRadius: 8, fontWeight: 500, borderColor: "#fecaca", color: "#dc2626" }}>
              一键解绑
            </Button>
          </Space>
        </div>

        {/* ── Empty state: no windows at all ── */}
        {!hasWindows && (
          <div className="flex-1 flex flex-col items-center justify-center" style={{ minHeight: 340, gap: 20 }}>
            <div style={{ width: 80, height: 80, borderRadius: 24, background: "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 24px rgba(22,119,255,.08)" }}>
              <DesktopOutlined style={{ fontSize: 34, color: "#1677ff" }} />
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: "#1a1a2e", marginBottom: 4 }}>开始管理游戏窗口</div>
              <div style={{ fontSize: 12, color: "#b0b5c0", lineHeight: 1.6 }}>
                绑定游戏窗口后，即可管理脚本执行、窗口透明度与锁定状态
              </div>
            </div>
            <Button type="primary" size="middle" icon={<PlusOutlined />} onClick={bind} style={{ borderRadius: 8 }}>立即绑定</Button>
          </div>
        )}

        {/* ── Window selector cards row ── */}
        {hasWindows && (
          <div className="shrink-0 mb-4">
            <div
              className="window-row flex items-center gap-2.5 overflow-x-auto pb-1.5"
              style={{ marginRight: -20, paddingRight: 20, scrollSnapType: "x mandatory" }}
              onWheel={(e) => {
                if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
                  e.currentTarget.scrollLeft += e.deltaY;
                  e.preventDefault();
                }
              }}
            >
              {characterStore.characters.map((c, i) => {
                const selected = c.hwnd === characterStore.selectedHwnd;
                const accent = DOT_COLORS[i % DOT_COLORS.length];
                return (
                  <div
                    key={c.hwnd}
                    className="window-card win-card-enter"
                    onClick={() => characterStore.setSelectedHwnd(c.hwnd)}
                    title={`HWND: ${c.hwnd}`}
                    style={{
                      animationDelay: `${i * 50}ms`,
                      borderTop: `3px solid ${accent}`,
                      padding: "10px 14px 12px",
                      minWidth: 130,
                      display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
                      ...(selected ? {
                        borderColor: accent,
                        boxShadow: `0 0 0 1px ${accent}40, 0 4px 16px ${accent}18`,
                        backgroundColor: `${accent}06`,
                      } : {}),
                    }}
                  >
                    {c.character ? (
                      <img src={c.character} alt=""
                        style={{
                          width: 120, height: 34, objectFit: "contain",
                          borderRadius: 6, background: "#f5f6f8",
                          border: "1px solid #e8eaed",
                        }} />
                    ) : (
                      <div style={{
                        width: 48, height: 34, borderRadius: 8,
                        background: `linear-gradient(135deg, ${accent}18, ${accent}0d)`,
                        border: `1px dashed ${accent}40`,
                        display: "flex", alignItems: "center", justifyContent: "center",
                      }}>
                        <DesktopOutlined style={{ fontSize: 18, color: accent }} />
                      </div>
                    )}
                    <div className="flex items-center gap-1.5">
                      <span style={{
                        width: 6, height: 6, borderRadius: "50%",
                        background: c.running ? "#52c41a" : "#d1d5db",
                        boxShadow: c.running ? "0 0 6px rgba(82,196,26,.4)" : undefined,
                        flexShrink: 0,
                      }} />
                      <span className="text-[11px] font-medium" style={{ color: c.running ? "#374151" : "#8b8fa3" }}>
                        {c.running ? "运行中" : "已停止"}
                      </span>
                    </div>
                  </div>
                );
              })}
              {/* Add window card */}
              <div
                className="window-card"
                onClick={bind}
                style={{
                  borderStyle: "dashed",
                  borderColor: "#d0d4dd",
                  background: "#fafbfc",
                  padding: "10px 20px 12px",
                  minWidth: 100,
                  display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 6,
                }}
              >
                <div style={{
                  width: 36, height: 36, borderRadius: 10,
                  background: "#eef2ff", border: "1px dashed #b0c8f0",
                  display: "flex", alignItems: "center", justifyContent: "center",
                }}>
                  <PlusOutlined style={{ fontSize: 16, color: "#1677ff" }} />
                </div>
                <span className="text-[11px] font-medium text-[#1677ff]">绑定窗口</span>
              </div>
            </div>
          </div>
        )}

        {/* ── Dashboard (selected window) ── */}
        {selectedCharacter && (
          <>
            {/* Control panel */}
            <div className="shrink-0 mb-4"
              style={{
                background: "#fff",
                borderRadius: 12,
                border: "1px solid #eef0f2",
                boxShadow: "0 1px 3px rgba(0,0,0,.03)",
                overflow: "hidden",
              }}
            >
              {/* Status bar */}
              <div className="flex items-center gap-3 px-5 py-3" style={{ borderBottom: "1px solid #f3f4f6" }}>
                <div className="flex items-center gap-2">
                  <div style={{
                    width: 7, height: 7, borderRadius: "50%",
                    background: selectedCharacter.currentTask ? "#52c41a" : "#d1d5db",
                    boxShadow: selectedCharacter.currentTask ? "0 0 6px rgba(82,196,26,.4)" : undefined,
                  }} />
                  <span className="text-[11px] text-[#8b8fa3] uppercase tracking-wider">当前任务</span>
                </div>
                <span className="text-[13px] font-medium text-[#1a1a2e] truncate">
                  {selectedCharacter.currentTask ?? "—"}
                </span>
                <div className="flex-1" />
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full"
                  style={{
                    background: isLocked ? "#fff7ed" : "#f0fdf4",
                    border: `1px solid ${isLocked ? "#fed7aa" : "#bbf7d0"}`,
                  }}>
                  {isLocked ? <LockOutlined style={{ fontSize: 10, color: "#c2410c" }} /> : <UnlockOutlined style={{ fontSize: 10, color: "#15803d" }} />}
                  <span className="text-[11px] font-medium" style={{ color: isLocked ? "#c2410c" : "#15803d" }}>
                    {isLocked ? "已锁定" : "已解锁"}
                  </span>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-3 px-5 py-4">
                <Button
                  type={selectedCharacter?.running ? "default" : "primary"}
                  icon={selectedCharacter?.running ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  style={{ borderRadius: 8, fontWeight: 500, ...(selectedCharacter?.running ? {} : { boxShadow: "0 2px 8px rgba(22,119,255,.2)" }) }}
                  onClick={() => {
                    const hwnd = characterStore.selectedHwnd!;
                    const wasRunning = selectedCharacter?.running;
                    window.pywebview?.api.emit(wasRunning ? "API:SCRIPT:PAUSE" : "API:SCRIPT:RESUME", hwnd).then(() => {
                      const ch = useCharacterStore.getState().characters.find((c) => c.hwnd === hwnd);
                      if (ch) characterStore.update({ hwnd, running: !ch.running });
                    });
                  }}
                >
                  {selectedCharacter?.running ? "暂停" : "开始执行"}
                </Button>

                <Button
                  icon={<StopOutlined />}
                  disabled={!selectedCharacter?.currentTask && taskCount === 0}
                  onClick={async () => {
                    const hwnd = characterStore.selectedHwnd!;
                    await window.pywebview?.api.emit("API:SCRIPT:STOP", hwnd);
                    characterStore.update({ hwnd, currentTask: null });
                  }}
                  style={{ borderRadius: 8, fontWeight: 500, borderColor: "#fecaca", color: "#dc2626" }}
                >
                  结束任务
                </Button>

                <Button
                  icon={isLocked ? <LockOutlined /> : <UnlockOutlined />}
                  onClick={handleToggleLock}
                  style={{
                    borderRadius: 8, fontWeight: 500,
                    borderColor: isLocked ? "#fed7aa" : "#bbf7d0",
                    color: isLocked ? "#c2410c" : "#15803d",
                    background: isLocked ? "#fff7ed" : "#f0fdf4",
                  }}
                >
                  {isLocked ? "解锁" : "锁定"}
                </Button>

                <Button icon={<ClearOutlined />} disabled={taskCount === 0}
                  onClick={() => characterStore.clearExecute(selectedCharacter.hwnd)}
                  style={{ borderRadius: 8, fontWeight: 500 }}>
                  {taskCount > 0 ? `清空队列 (${taskCount})` : "清空队列"}
                </Button>

                <div className="flex-1" />

                {/* Opacity slider */}
                <div className="flex items-center gap-3">
                  <span className="text-[10px] text-[#9ca3af] font-medium uppercase tracking-wider">透明度</span>
                  <Slider style={{ width: 96, margin: 0 }} min={0} max={255}
                    value={selectedCharacter?.opacity ?? 255}
                    onChange={(v) => { characterStore.update({ hwnd: selectedCharacter.hwnd, opacity: v }); window.pywebview?.api.emit("API:SCRIPT:SET_OPACITY", selectedCharacter.hwnd, v); }}
                    styles={{ track: { background: "#1677ff" }, rail: { background: "#e5e7eb" } }} />
                  <span className="text-[12px] font-semibold text-[#374151] font-mono w-7 text-right">
                    {selectedCharacter?.opacity ?? 255}
                  </span>
                </div>
              </div>
            </div>

            {/* Bottom panels: Task queue + Plans */}
            <div className="flex-1 min-h-0 grid grid-cols-2 gap-4">
              {/* ── Task queue ── */}
              <div className="flex flex-col min-h-0"
                style={{ background: "#fff", borderRadius: 12, border: "1px solid #eef0f2", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,.03)" }}>
                <div className="shrink-0 flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <div className="flex items-center gap-2.5">
                    <span className="text-[13px] font-semibold text-[#1a1a2e]">待执行任务</span>
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
                      {selectedCharacter.executeList.map((item, idx) => {
                        const accent = DOT_COLORS[idx % DOT_COLORS.length];
                        return (
                          <div key={item._uid} draggable
                            onDragStart={handleDragStart(item._uid)} onDragEnd={handleDragEnd}
                            onDragOver={handleDragOver} onDrop={handleDrop(item._uid)}
                            onClick={() => openConfig(item._uid)}
                            className="queue-item queue-item-enter group"
                            style={{
                              animationDelay: `${idx * 40}ms`,
                              borderLeft: `3px solid ${accent}`,
                              opacity: dragUid === item._uid ? 0.3 : 1,
                            }}
                          >
                            <div className="flex items-center justify-between gap-2 px-3.5 py-2.5">
                              <div className="flex items-center gap-2.5 min-w-0">
                                <span className="text-[12px] font-medium text-[#1a1a2e] truncate">
                                  {item.name}
                                </span>
                                <Tag style={{ fontSize: 9, lineHeight: 1, border: "none", borderRadius: 4, padding: "1px 6px", margin: 0, color: "#9ca3af", background: "#f3f4f6", fontFamily: "ui-monospace,Consolas,monospace" }}>
                                  v{item.version}
                                </Tag>
                              </div>
                              <span className="flex items-center justify-center w-6 h-6 cursor-pointer opacity-0 group-hover:opacity-100 transition-all shrink-0"
                                style={{ borderRadius: 6, color: "#d1d5db" }}
                                onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.background = "#fef2f2"; }}
                                onMouseLeave={(e) => { e.currentTarget.style.color = "#d1d5db"; e.currentTarget.style.background = "transparent"; }}
                                onClick={(e) => { e.stopPropagation(); characterStore.removeExecute(selectedCharacter.hwnd, item._uid); }}>
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

              {/* ── Plans ── */}
              <div className="flex flex-col min-h-0"
                style={{ background: "#fff", borderRadius: 12, border: "1px solid #eef0f2", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,.03)" }}>
                <div className="shrink-0 flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <div className="flex items-center gap-2.5">
                    <span className="text-[13px] font-semibold text-[#1a1a2e]">执行计划</span>
                    <span className="text-[11px] text-[#8b8fa3] bg-[#f3f4f6] px-2 py-0.5 rounded-full font-mono">
                      {selectedCharacter.plans.length}
                    </span>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto thin-scrollbar p-4">
                  {!selectedCharacter.plans?.length ? (
                    <div className="h-full flex flex-col items-center justify-center gap-2">
                      <Empty description={<span className="text-xs text-[#b0b8c4]">暂无计划</span>} image={Empty.PRESENTED_IMAGE_SIMPLE} />
                      <span className="text-[11px] text-[#d1d5db]">在计划页面创建定时任务</span>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2">
                      {selectedCharacter.plans.map((planBase, idx) => {
                        const plan = planBase as PlanEntry;
                        const tmpl = PLAN_TEMPLATES.find((t) => t.id === plan.templateId);
                        const cronHuman = (() => { try { return cronstrue.toString(plan.cron, { locale: "zh_CN" }); } catch { return plan.cron; } })();
                        let nextRun: Date | null = null; let secondsLeft = -1;
                        if (plan.enabled) { try { nextRun = new Cron(plan.cron).nextRun(); } catch { } if (nextRun) secondsLeft = Math.max(0, Math.floor((nextRun.getTime() - now) / 1000)); }
                        const accent = DOT_COLORS[idx % DOT_COLORS.length];
                        return (
                          <div key={`${plan._uid}`}
                            className="queue-item queue-item-enter group"
                            onClick={() => openPlanEdit(plan)}
                            style={{
                              animationDelay: `${idx * 50}ms`,
                              borderLeft: `3px solid ${plan.enabled ? accent : "#e5e7eb"}`,
                              boxShadow: plan.enabled ? "0 2px 8px rgba(0,0,0,.03)" : "0 1px 2px rgba(0,0,0,.01)",
                              borderColor: plan.enabled ? "#d0d4dd" : "#eef0f2",
                            }}
                          >
                            <div className="flex items-center gap-2.5 px-3.5 py-2.5">
                              <span onClick={(e) => e.stopPropagation()}>
                                <Switch size="small" checked={plan.enabled}
                                  onChange={() => { userStore.togglePlan(plan._uid); characterStore.setPlans(selectedCharacter.hwnd, useUserStore.getState().plans); }} />
                              </span>
                              <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-1.5 mb-0.5">
                                  <span className="text-[12px] font-semibold text-[#1a1a2e] truncate">{plan.name}</span>
                                  {tmpl && (
                                    <Tag style={{ fontSize: 8, lineHeight: 1, border: "none", borderRadius: 4, padding: "1px 6px", margin: 0, color: "#6366f1", background: "#eef2ff" }}>
                                      {tmpl.name}
                                    </Tag>
                                  )}
                                </div>
                                <div className="flex items-center gap-1 text-[10px] text-[#9ca3af]">
                                  <ClockCircleOutlined style={{ fontSize: 9 }} />
                                  <span className="font-mono">{plan.cron}</span>
                                  <span className="text-[#d1d5db]">·</span>
                                  <span className="truncate">{cronHuman}</span>
                                </div>
                              </div>
                              <span onClick={(e) => { e.stopPropagation(); userStore.removePlan(plan._uid); characterStore.setPlans(selectedCharacter.hwnd, useUserStore.getState().plans); }}
                                className="flex items-center justify-center w-6 h-6 cursor-pointer opacity-0 group-hover:opacity-100 transition-all shrink-0 select-none"
                                style={{ borderRadius: 6, color: "#d1d5db" }}
                                onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; e.currentTarget.style.background = "#fef2f2"; }}
                                onMouseLeave={(e) => { e.currentTarget.style.color = "#d1d5db"; e.currentTarget.style.background = "transparent"; }}>
                                <DeleteOutlined style={{ fontSize: 12 }} />
                              </span>
                            </div>
                            {plan.enabled && nextRun && (
                              <div className="px-3.5 pb-2.5">
                                {secondsLeft <= 60 ? (
                                  <div className="flex items-center gap-2 px-3 py-2"
                                    style={{ background: "linear-gradient(135deg, #fffbeb, #fef3c7)", borderRadius: 8, border: "1px solid #fde68a" }}>
                                    <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#f59e0b", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: "#fff", animation: "win-pulse 1s infinite" }}>!</div>
                                    <span className="text-[10px] font-semibold text-[#92400e]">即将执行</span>
                                    <span className="text-xs font-bold text-[#d97706] ml-auto font-mono">{secondsLeft}s</span>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-2 px-3 py-1.5 text-[10px] text-[#9ca3af] bg-[#f9fafb] rounded-lg">
                                    <span>下次</span>
                                    <span className="font-semibold text-[#374151] ml-auto">
                                      {nextRun.toLocaleDateString("zh-CN", { month: "short", day: "numeric" })} {nextRun.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}
                                    </span>
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

        {/* ── No window selected (but windows exist) ── */}
        {!selectedCharacter && hasWindows && (
          <div className="flex-1 flex flex-col items-center justify-center" style={{ minHeight: 200, gap: 16 }}>
            <div style={{ width: 64, height: 64, borderRadius: 20, background: "#f5f7fa", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <DesktopOutlined style={{ fontSize: 26, color: "#c8cdd5" }} />
            </div>
            <div style={{ textAlign: "center" }}>
              <div className="text-[14px] font-medium text-[#6b7280] mb-1">选择要管理的窗口</div>
              <div className="text-[12px] text-[#b0b5c0]">点击上方窗口卡片，查看任务队列与执行计划</div>
            </div>
          </div>
        )}

      </div>

      {modalOpen && (
        <HwndPreviewModal onClose={closeModal}
          onSelect={(hwnd: string) => { window.pywebview?.api.emit("API:SCRIPT:BIND", hwnd).then(() => { characterStore.add({ character: "", hwnd, running: true, locked: true, opacity: 255, currentTask: null, executeList: userStore.queue.map(t => ({ id: t.id, name: t.name, version: t.version, values: t.values })), plans: userStore.plans }); characterStore.setSelectedHwnd(hwnd); }); }}
          onSelectAll={async (hwnds: string[]) => { const bound = new Set(characterStore.characters.map(c => c.hwnd)); for (const hwnd of hwnds) { if (bound.has(hwnd)) continue; await window.pywebview?.api.emit("API:SCRIPT:BIND", hwnd); characterStore.add({ character: "", hwnd, running: true, locked: true, opacity: 255, currentTask: null, executeList: userStore.queue.map(t => ({ id: t.id, name: t.name, version: t.version, values: t.values })), plans: userStore.plans }); } }}
        />
      )}

      <TaskConfigModal key={configUid ?? "none"} open={configOpen} task={configTask} onClose={closeConfig} onSave={handleConfigSave} />

      <PlanModal
        open={planEditOpen}
        plan={editingPlan}
        onClose={() => { setPlanEditOpen(false); setEditingPlan(null); }}
        onSave={savePlanEdit}
      />
    </>
  );
};

export default WindowsPage;
