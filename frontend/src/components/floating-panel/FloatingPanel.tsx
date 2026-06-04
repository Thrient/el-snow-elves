import { type FC, type MouseEvent } from "react"
import { useEffect, useRef, useState } from "react"
import { Badge, Switch, Tabs } from "antd"
import { ArrowDownOutlined, UnorderedListOutlined, InboxOutlined, ClockCircleOutlined, HolderOutlined } from "@ant-design/icons"
import { useSessionStore } from "@/store/session-store.ts"
import { useCharacterStore } from "@/store/character-store.ts"
import { useResponsiveStore } from "@/store/responsive-store.ts"
import type { Task } from "@/types/task.ts"
import { PLAN_TEMPLATES } from "@/types/plan.ts"
import type { PlanBase } from "@/types/plan.ts"
import TaskConfigModal from "@/components/task-config-modal/TaskConfigModal.tsx"
import PlanModal from "@/pages/plans/PlanModal.tsx"

const PANEL_WIDTH = 260
const BALL_SIZE = 40
const EDGE_THRESHOLD = 80
const SWIPE_THRESHOLD = 80

const cardColors = [
  "rgba(22,119,255,0.06)",
  "rgba(82,196,26,0.06)",
  "rgba(250,140,22,0.06)",
  "rgba(114,46,209,0.06)",
  "rgba(19,194,194,0.06)",
]

const cardBorderColors = [
  "rgba(22,119,255,0.12)",
  "rgba(82,196,26,0.12)",
  "rgba(250,140,22,0.12)",
  "rgba(114,46,209,0.12)",
  "rgba(19,194,194,0.12)",
]

const dotColors = ["#1677ff", "#52c41a", "#fa8c16", "#722ed1", "#13c2c2"]

const FloatingPanel: FC = () => {
  const queue = useSessionStore((s) => s.queue)
  const plans = useSessionStore((s) => s.plans)
  const [expanded, setExpanded] = useState(false)
  const [position, setPosition] = useState({ x: 16, y: 120 })
  const posRef = useRef(position)
  const dragging = useRef(false)
  const [draggingVisual, setDraggingVisual] = useState(false)
  const offset = useRef({ x: 0, y: 0 })
  const moved = useRef(false)

  const [activeTab, setActiveTab] = useState<"queue" | "plans">("queue")

  const updatePlan = useSessionStore((s) => s.updatePlan);
  const [planModalOpen, setPlanModalOpen] = useState(false);
  const [planModalUid, setPlanModalUid] = useState<number | null>(null);
  const [planModalData, setPlanModalData] = useState<PlanBase | null>(null);

  const [configOpen, setConfigOpen] = useState(false)
  const [configTask, setConfigTask] = useState<Task | null>(null)
  const [configUid, setConfigUid] = useState<number | null>(null)

  const updateTaskValues = useSessionStore((s) => s.updateTaskValues)
  const removeTask = useSessionStore((s) => s.removeTask)
  const reorderQueue = useSessionStore((s) => s.reorderQueue)
  const removePlan = useSessionStore((s) => s.removePlan)
  const togglePlan = useSessionStore((s) => s.togglePlan)

  type SwipeTarget = { uid: number; type: "queue" | "plan" }
  const [swiping, setSwiping] = useState<SwipeTarget | null>(null)
  const [swipeX, setSwipeX] = useState(0)
  const swipeXRef = useRef(0)
  const cardDraggingRef = useRef(false)
  const swipeStartX = useRef(0)
  const swiped = useRef(false)

  // ---- Drag-to-reorder state ----
  const [dragUid, setDragUid] = useState<number | null>(null)
  const [dragOverUid, setDragOverUid] = useState<number | null>(null)

  // ---- Card swipe handlers ----
  useEffect(() => {
    const handleMouseMove = (e: globalThis.MouseEvent) => {
      if (!cardDraggingRef.current || swiping === null) return
      const dx = e.clientX / useResponsiveStore.getState().zoom - swipeStartX.current
      swiped.current = true
      const clamped = Math.max(-180, Math.min(dx, 180))
      swipeXRef.current = clamped
      setSwipeX(clamped)
    }

    const handleMouseUp = () => {
      if (!cardDraggingRef.current) return
      cardDraggingRef.current = false
      if (swiping !== null) {
        const finalX = swipeXRef.current
        if (finalX > SWIPE_THRESHOLD) {
          if (swiping.type === "queue") removeTask(swiping.uid)
          else removePlan(swiping.uid)
        } else if (finalX < -SWIPE_THRESHOLD) {
          const charStore = useCharacterStore.getState()
          if (charStore.selectedHwnd) {
            if (swiping.type === "queue") {
              const task = useSessionStore.getState().queue.find((t) => t._uid === swiping.uid)
              if (task) charStore.pushExecute(charStore.selectedHwnd, { id: task.id, name: task.name, version: task.version, values: task.values })
            } else {
              charStore.syncPlansToAllWindows(useSessionStore.getState().plans)
            }
          }
        }
      }
      setSwiping(null)
      setSwipeX(0)
      swipeXRef.current = 0
    }

    window.addEventListener("mousemove", handleMouseMove)
    window.addEventListener("mouseup", handleMouseUp)
    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }
  }, [swiping, removeTask, removePlan])

  // ---- Panel drag handlers ----
  useEffect(() => {
    const handleMouseMove = (e: globalThis.MouseEvent) => {
      if (!dragging.current) return
      moved.current = true
      const z = useResponsiveStore.getState().zoom
      const next = {
        x: e.clientX / z - offset.current.x,
        y: e.clientY / z - offset.current.y,
      }
      posRef.current = next
      setPosition(next)
    }

    const handleMouseUp = () => {
      if (!dragging.current) return
      dragging.current = false
      setDraggingVisual(false)

      setPosition((prev) => {
        const z = useResponsiveStore.getState().zoom
        const w = expanded ? PANEL_WIDTH : BALL_SIZE
        const maxX = window.innerWidth / z - w - 8
        let x = Math.max(0, Math.min(prev.x, maxX))

        if (x < EDGE_THRESHOLD) x = 0
        else if (x > maxX - EDGE_THRESHOLD) x = maxX

        const y = Math.max(0, Math.min(prev.y, window.innerHeight / z - 60))
        const snapped = { x, y }
        posRef.current = snapped
        return snapped
      })
    }

    window.addEventListener("mousemove", handleMouseMove)
    window.addEventListener("mouseup", handleMouseUp)
    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", handleMouseUp)
    }
  }, [expanded])

  // ---- Click handlers ----
  const toggle = () => {
    if (moved.current) {
      moved.current = false
      return
    }
    setExpanded((v) => !v)
  }

  const handleMouseDown = (e: MouseEvent) => {
    dragging.current = true
    setDraggingVisual(true)
    moved.current = false
    const z = useResponsiveStore.getState().zoom
    offset.current = {
      x: e.clientX / z - posRef.current.x,
      y: e.clientY / z - posRef.current.y,
    }
  }

  const handleCardMouseDown = (target: SwipeTarget, e: React.MouseEvent) => {
    cardDraggingRef.current = true
    swiped.current = false
    swipeStartX.current = e.clientX / useResponsiveStore.getState().zoom
    setSwiping(target)
  }

  // ---- Drag-to-reorder handlers (queue only) ----
  const handleDragStart = (uid: number) => (e: React.DragEvent) => {
    // 取消 swipe 状态，避免拖拽结束后鼠标移动触发左右滑动
    cardDraggingRef.current = false
    setSwiping(null)
    e.dataTransfer.effectAllowed = "move"
    e.dataTransfer.setData("text/plain", String(uid))
    setDragUid(uid)
  }

  const handleDragEnd = () => {
    // 确保拖拽结束后 swipe 状态干净
    cardDraggingRef.current = false
    setSwiping(null)
    setDragUid(null)
    setDragOverUid(null)
  }

  const handleDragOver = (uid: number) => (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = "move"
    if (dragUid !== null && dragUid !== uid) {
      setDragOverUid(uid)
    }
  }

  const handleDrop = (targetUid: number) => (e: React.DragEvent) => {
    e.preventDefault()
    const sourceUid = Number(e.dataTransfer.getData("text/plain"))
    if (isNaN(sourceUid) || sourceUid === targetUid) return

    const uids = queue.map((item) => item._uid)
    const sourceIdx = uids.indexOf(sourceUid)
    const targetIdx = uids.indexOf(targetUid)
    if (sourceIdx === -1 || targetIdx === -1) return

    uids.splice(sourceIdx, 1)
    uids.splice(targetIdx, 0, sourceUid)
    reorderQueue(uids)
    setDragUid(null)
    setDragOverUid(null)
  }

  // ---- Config modal ----
  const openConfig = (uid: number) => {
    const itemQueue = useSessionStore.getState().queue
    const item = itemQueue.find((t) => t._uid === uid)
    if (!item) return
    const taskStore = useCharacterStore.getState()
    const original = taskStore.taskList.find((t) => t.id === item.id)
    if (original) {
      setConfigTask({ ...original, values: item.values })
      setConfigUid(uid)
      setConfigOpen(true)
    }
  }

  const closeConfig = () => {
    setConfigOpen(false)
    setConfigTask(null)
    setConfigUid(null)
  }

  const handleConfigSave = (values: Record<string, unknown>) => {
    if (configUid !== null) {
      updateTaskValues(configUid, values)
    }
    closeConfig()
  }

  const swipeIndicator = (x: number) => {
    if (x > 40) return { bg: "rgba(255,77,79,0.08)", text: "删除", color: "#ff4d4f" }
    if (x < -40) return { bg: "rgba(22,119,255,0.08)", text: "添加到窗口", color: "#1677ff" }
    return null
  }

  return (
    <>
      {/* ---- Collapsed: floating ball ---- */}
      {!expanded ? (
        <div className="fixed z-[1000]" style={{ left: position.x, top: position.y }}>
          {/* Pulse ring when has items */}
          {(queue.length > 0 || plans.length > 0) && (
            <div
              className="absolute rounded-full animate-pulse"
              style={{
                left: -4, top: -4,
                width: BALL_SIZE + 8, height: BALL_SIZE + 8,
                border: "1.5px solid rgba(22,119,255,0.25)",
                animation: "pulse-ring 2.5s ease-out infinite",
              }}
            />
          )}

          <div
            className={`relative flex items-center justify-center rounded-full cursor-pointer select-none ${
              draggingVisual ? "" : "transition-all duration-300 hover:scale-110 active:scale-95"
            }`}
            style={{
              width: BALL_SIZE,
              height: BALL_SIZE,
              background: "linear-gradient(145deg, #1677ff 0%, #4096ff 100%)",
              boxShadow: [
                "0 4px 16px rgba(22,119,255,0.3)",
                "0 1px 3px rgba(22,119,255,0.15)",
                "inset 0 1px 0 rgba(255,255,255,0.25)",
              ].join(", "),
            }}
            onMouseDown={handleMouseDown}
            onClick={toggle}
          >
            <Badge
              count={queue.length + plans.length}
              size="small"
              offset={[3, -5]}
              className="shadow-[0_1px_3px_rgba(0,0,0,0.15)]"
            >
              <UnorderedListOutlined
                className="text-white text-[17px] leading-none drop-shadow-[0_1px_3px_rgba(0,0,0,0.18)]"
              />
            </Badge>
          </div>
        </div>
      ) : (
        /* ---- Expanded: queue panel ---- */
        <div
          className="fixed z-[1000] rounded-2xl shadow-2xl border select-none overflow-hidden animate-fadeIn"
          style={{
            left: position.x,
            top: position.y,
            width: PANEL_WIDTH,
            background: "rgba(255,255,255,0.92)",
            backdropFilter: "blur(20px) saturate(150%)",
            WebkitBackdropFilter: "blur(20px) saturate(150%)",
            borderColor: "rgba(0,0,0,0.06)",
          }}
        >
          {/* Header */}
          <div
            className="flex items-center justify-between px-5 py-3 cursor-move border-b"
            style={{ borderColor: "rgba(0,0,0,0.05)", background: "rgba(255,255,255,0.6)" }}
            onMouseDown={handleMouseDown}
          >
            <span className="text-[13px] font-semibold text-[#1a1a2e] tracking-tight">待执行</span>
            <span
              className="text-[11px] text-[#bbb] cursor-pointer hover:text-[#1677ff] transition-colors flex items-center gap-1"
              onClick={toggle}
            >
              <ArrowDownOutlined className="text-[10px]" />
              收起
            </span>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={(k) => setActiveTab(k as "queue" | "plans")}
            size="small"
            className="floating-tabs"
            tabBarStyle={{ padding: "0 16px", marginBottom: 0 }}
            items={[
              {
                key: "queue",
                label: (
                  <span className="flex items-center gap-1.5 text-[12px]">
                    <UnorderedListOutlined />
                    队列
                    {queue.length > 0 && (
                      <span className="text-[10px] text-white bg-[#1677ff] rounded-full px-1.5 leading-tight">{queue.length}</span>
                    )}
                  </span>
                ),
                children: (
                  <div className="max-h-[45vh] overflow-y-auto overflow-x-hidden px-3 pb-3">
                    {queue.length === 0 ? (
                      <div className="py-10 text-center">
                        <div className="text-[#e0e0e0] text-xl mb-2"><InboxOutlined /></div>
                        <p className="text-[12px] text-[#bbb] m-0">暂无任务</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-2">
                        {queue.map((item, index) => {
                          const indicator = swiping?.uid === item._uid && swiping?.type === "queue" ? swipeIndicator(swipeX) : null
                          const isDragOver = dragOverUid === item._uid
                          return (
                            <div key={item._uid} className="relative overflow-hidden rounded-xl"
                              onDragOver={handleDragOver(item._uid)}
                              onDragLeave={() => setDragOverUid(null)}
                              onDrop={handleDrop(item._uid)}
                            >
                              {indicator && (
                                <div
                                  className="absolute inset-0 rounded-xl flex items-center px-4 text-[11px] font-semibold transition-opacity duration-100"
                                  style={{
                                    backgroundColor: indicator.bg,
                                    color: indicator.color,
                                    justifyContent: swipeX > 0 ? "flex-start" : "flex-end",
                                  }}
                                >
                                  {indicator.text}
                                </div>
                              )}
                              {/* drag-over indicator */}
                              {isDragOver && (
                                <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#1677ff] rounded-full z-10" />
                              )}
                              <div
                                className="rounded-xl px-4 py-3 cursor-pointer select-none relative"
                                style={{
                                  transition: swiping?.uid === item._uid && swiping?.type === "queue" ? "none" : "transform 180ms ease, box-shadow 180ms ease",
                                  transform: swiping?.uid === item._uid && swiping?.type === "queue" ? `translateX(${swipeX}px)` : undefined,
                                  backgroundColor: cardColors[index % cardColors.length],
                                  border: `1px solid ${cardBorderColors[index % cardBorderColors.length]}`,
                                  opacity: dragUid === item._uid ? 0.4 : 1,
                                }}
                                onClick={() => {
                                  if (swiped.current) { swiped.current = false; return }
                                  openConfig(item._uid)
                                }}
                                onMouseDown={(e) => handleCardMouseDown({ uid: item._uid, type: "queue" }, e)}
                              >
                                <div className="flex items-center gap-3">
                                  <span
                                    className="flex-shrink-0 cursor-grab active:cursor-grabbing text-[#bbb] hover:text-[#1677ff] transition-colors"
                                    onMouseDown={(e) => e.stopPropagation()}
                                    draggable
                                    onDragStart={handleDragStart(item._uid)}
                                    onDragEnd={handleDragEnd}
                                  >
                                    <HolderOutlined className="text-[11px]" />
                                  </span>
                                  <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: dotColors[index % dotColors.length] }} />
                                  <span className="text-[12px] font-medium text-[#1a1a2e] truncate leading-normal">{item.name}</span>
                                </div>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                ),
              },
              {
                key: "plans",
                label: (
                  <span className="flex items-center gap-1.5 text-[12px]">
                    <ClockCircleOutlined />
                    计划
                    {plans.length > 0 && (
                      <span className="text-[10px] text-white bg-[#1677ff] rounded-full px-1.5 leading-tight">{plans.length}</span>
                    )}
                  </span>
                ),
                children: (
                  <div className="max-h-[45vh] overflow-y-auto overflow-x-hidden px-3 pb-3">
                    {plans.length === 0 ? (
                      <div className="py-10 text-center">
                        <div className="text-[#e0e0e0] text-xl mb-2"><ClockCircleOutlined /></div>
                        <p className="text-[12px] text-[#bbb] m-0">暂无计划</p>
                      </div>
                    ) : (
                      <div className="flex flex-col gap-2">
                        {plans.map((plan, index) => {
                          const tmpl = PLAN_TEMPLATES.find((t) => t.id === plan.templateId);
                          const indicator = swiping?.uid === plan._uid && swiping?.type === "plan" ? swipeIndicator(swipeX) : null;
                          return (
                            <div key={plan._uid} className="relative overflow-hidden rounded-xl">
                              {indicator && (
                                <div
                                  className="absolute inset-0 rounded-xl flex items-center px-4 text-[11px] font-semibold transition-opacity duration-100"
                                  style={{
                                    backgroundColor: indicator.bg,
                                    color: indicator.color,
                                    justifyContent: swipeX > 0 ? "flex-start" : "flex-end",
                                  }}
                                >
                                  {indicator.text}
                                </div>
                              )}
                              <div
                                className="rounded-xl px-4 py-3 select-none relative cursor-pointer"
                                style={{
                                  backgroundColor: cardColors[index % cardColors.length],
                                  border: `1px solid ${cardBorderColors[index % cardBorderColors.length]}`,
                                  opacity: plan.enabled ? 1 : 0.5,
                                  transition: swiping?.uid === plan._uid && swiping?.type === "plan" ? "none" : "transform 180ms ease, box-shadow 180ms ease",
                                  transform: swiping?.uid === plan._uid && swiping?.type === "plan" ? `translateX(${swipeX}px)` : undefined,
                                }}
                                onClick={() => {
                                  if (swiped.current) { swiped.current = false; return }
                                  setPlanModalData({ name: plan.name, templateId: plan.templateId, cron: plan.cron, enabled: plan.enabled, action: plan.action });
                                  setPlanModalUid(plan._uid);
                                  setPlanModalOpen(true);
                                }}
                                onMouseDown={(e) => handleCardMouseDown({ uid: plan._uid, type: "plan" }, e)}
                              >
                                <div className="flex items-center gap-3">
                                  <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ backgroundColor: plan.enabled ? dotColors[index % dotColors.length] : "#d9d9d9" }} />
                                  <div className="min-w-0 flex-1">
                                    <div className="text-[12px] font-medium text-[#1a1a2e] truncate">{plan.name}</div>
                                    <div className="text-[10px] text-[#8b8fa3] mt-0.5 font-mono">
                                      {plan.cron}
                                      {tmpl && <span className="ml-1 text-[#bbb]">{tmpl.name}</span>}
                                    </div>
                                  </div>
                                  <Switch
                                    size="small"
                                    checked={plan.enabled}
                                    onClick={(_, e) => e.stopPropagation()}
                                    onChange={() => {
                                      togglePlan(plan._uid);
                                      useCharacterStore.getState().syncPlansToAllWindows(useSessionStore.getState().plans);
                                    }}
                                  />
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ),
              },
            ]}
          />
        </div>
      )}

      <TaskConfigModal
        key={configUid ?? "none"}
        open={configOpen}
        task={configTask}
        onClose={closeConfig}
        onSave={handleConfigSave}
      />

      <PlanModal
        open={planModalOpen}
        plan={planModalData}
        onClose={() => {
          setPlanModalOpen(false);
          setPlanModalData(null);
          setPlanModalUid(null);
        }}
        onSave={(saved) => {
          if (planModalUid !== null) {
            updatePlan(planModalUid, saved);
            useCharacterStore.getState().syncPlansToAllWindows(useSessionStore.getState().plans);
          }
          setPlanModalOpen(false);
          setPlanModalData(null);
          setPlanModalUid(null);
        }}
      />
    </>
  )
}

export default FloatingPanel;
