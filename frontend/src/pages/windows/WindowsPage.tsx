import { type FC, useEffect, useState } from "react";
import {
  DeleteOutlined, DesktopOutlined, MinusCircleOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { Button, Empty, Space } from "antd";
import { useCharacterStore } from "@/store/character-store.ts";
import { useSessionStore, type PlanEntry } from "@/store/session-store.ts";
import type { PlanBase } from "@/types/plan.ts";
import HwndPreviewModal from "@/components/hwnd-preview-modal/HwndPreviewModal.tsx";
import PlanModal from "@/pages/plans/PlanModal.tsx";
import PlanCard from "@/pages/plan/components/PlanCard";
import WindowSelector from "@/pages/windows/WindowSelector";
import ControlPanel from "@/pages/windows/ControlPanel";
import QueuePanel from "@/pages/windows/QueuePanel";

const DOT_COLORS = ["#1677ff", "#52c41a", "#fa8c16", "#722ed1", "#13c2c2"];

const WindowsPage: FC = () => {
  const userStore = useSessionStore();
  const characterStore = useCharacterStore();
  const [modalOpen, setModalOpen] = useState(false);
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

  const bind = () => setModalOpen(true);
  const closeModal = () => setModalOpen(false);

  const openPlanEdit = (plan: PlanEntry) => { setEditingPlan(plan); setPlanEditOpen(true); };
  const savePlanEdit = (planBase: PlanBase) => {
    if (!editingPlan) return;
    userStore.updatePlan(editingPlan._uid, planBase);
    if (selectedCharacter) {
      characterStore.setPlans(selectedCharacter.hwnd, useSessionStore.getState().plans);
    }
    setPlanEditOpen(false);
    setEditingPlan(null);
  };

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
              <span className="page-header__badge">{characterStore.characters.length} 个窗口</span>
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
                style={{ borderRadius: 8, fontWeight: 500 }}>解绑</Button>
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
          <div className="flex-1 flex flex-col items-center justify-center min-h-340px gap-5">
            <div className="w-20 h-20 rounded-3xl flex items-center justify-center shadow-[0_4px_24px_rgba(22,119,255,.08)]" style={{ background: "linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)" }}>
              <DesktopOutlined className="text-[34px] c-[#1677ff]" />
            </div>
            <div className="text-center">
              <div className="text-[15px] font-semibold c-[#1a1a2e] mb-1">开始管理游戏窗口</div>
              <div className="text-xs c-[#b0b5c0] leading-relaxed">
                绑定游戏窗口后，即可管理脚本执行、窗口透明度与锁定状态
              </div>
            </div>
            <Button type="primary" size="middle" icon={<PlusOutlined />} onClick={bind} className="rounded-lg">立即绑定</Button>
          </div>
        )}

        {/* ── Window selector cards row ── */}
        {hasWindows && <WindowSelector onBind={bind} />}

        {/* ── Dashboard (selected window) ── */}
        {selectedCharacter && (
          <>
            <ControlPanel />

            {/* Bottom panels: Task queue + Plans */}
            <div className="flex-1 min-h-0 grid grid-cols-2 gap-4">
              <QueuePanel />

              {/* ── Plans ── */}
              <div className="flex flex-col min-h-0 bg-white rounded-xl border border-solid border-[#eef0f2] overflow-hidden">
                <div className="shrink-0 flex items-center justify-between px-4 py-3" style={{ boxShadow: "inset 0 -1px 0 #f3f4f6" }}>
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
                      {selectedCharacter.plans.map((planBase, idx) => (
                        <PlanCard
                          key={`${(planBase as PlanEntry)._uid}`}
                          plan={planBase as PlanEntry}
                          idx={idx}
                          accent={DOT_COLORS[idx % DOT_COLORS.length]}
                          now={now}
                          onEdit={openPlanEdit}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </>
        )}

        {/* ── No window selected (but windows exist) ── */}
        {!selectedCharacter && hasWindows && (
          <div className="flex-1 flex flex-col items-center justify-center min-h-200px gap-4">
            <div className="w-16 h-16 rounded-[20px] bg-[#f5f7fa] flex items-center justify-center">
              <DesktopOutlined className="text-[26px] c-[#c8cdd5]" />
            </div>
            <div className="text-center">
              <div className="text-[14px] font-medium c-[#6b7280] mb-1">选择要管理的窗口</div>
              <div className="text-xs c-[#b0b5c0]">点击上方窗口卡片，查看任务队列与执行计划</div>
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
