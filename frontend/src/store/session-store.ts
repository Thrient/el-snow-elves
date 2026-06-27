import { create } from 'zustand'
import type { PlanBase } from "@/types/plan.ts";

type QueueEntry = { taskName: string; version: string | null; author?: string; values: Record<string, unknown>; valueTypes?: Record<string, "text" | "number" | "bool" | "list">; _uid: number }
export type PlanEntry = PlanBase & { _uid: number }

let _nextTaskUid = 0
let _nextPlanUid = 0

type State = {
  queue: QueueEntry[]
  plans: PlanEntry[]
  appendTask: (task: Record<string, unknown>) => void
  removeTask: (uid: number) => void
  reorderQueue: (orderedUids: number[]) => void
  clearTaskList: () => void
  updateTaskValues: (uid: number, values: Record<string, unknown>) => void
  updateTaskVersion: (uid: number, version: string | null) => void
  updateTaskAuthor: (uid: number, author: string, version: string | null, values: Record<string, unknown>) => void
  addPlan: (plan: PlanBase) => void
  removePlan: (uid: number) => void
  updatePlan: (uid: number, plan: PlanBase) => void
  togglePlan: (uid: number) => void
  loadConfig: (payload: Record<string, unknown>) => void
}

export const useSessionStore = create<State>((set) => ({
  queue: [],
  plans: [],

  appendTask: (task) => {
    const uid = _nextTaskUid++
    set((state) => ({
      queue: [...state.queue, {
        taskName: (task as any).taskName ?? task.name ?? "",
        version: (task as any).version ?? null,
        author: (task as any).author ?? "匿名作者",
        values: { ...((task.values ?? {}) as Record<string, unknown>) },
        valueTypes: task.valueTypes ? { ...(task.valueTypes as Record<string, "text" | "number" | "bool" | "list">) } : undefined,
        _uid: uid,
      }]
    }))
  },
  removeTask: (uid: number) =>
    set((state) => ({
      queue: state.queue.filter((t) => t._uid !== uid)
    })),
  reorderQueue: (orderedUids: number[]) =>
    set((state) => {
      const byUid = new Map(state.queue.map((t) => [t._uid, t]));
      const reordered: QueueEntry[] = [];
      for (const uid of orderedUids) {
        const entry = byUid.get(uid);
        if (entry) reordered.push(entry);
      }
      for (const t of state.queue) {
        if (!orderedUids.includes(t._uid)) reordered.push(t);
      }
      return { queue: reordered };
    }),
  clearTaskList: () =>
    set(() => ({
      queue: []
    })),
  updateTaskValues: (uid: number, values: Record<string, unknown>) =>
    set((state) => ({
      queue: state.queue.map((t) =>
        t._uid === uid ? { ...t, values } : t
      )
    })),
  updateTaskVersion: (uid: number, version: string | null) =>
    set((state) => ({
      queue: state.queue.map((t) =>
        t._uid === uid ? { ...t, version } : t
      )
    })),
  updateTaskAuthor: (uid, author, version, values) =>
    set((state) => ({
      queue: state.queue.map((t) =>
        t._uid === uid ? { ...t, author, version, values } : t
      ),
    })),

  addPlan: (plan) => {
    const uid = _nextPlanUid++
    set((state) => ({ plans: [...state.plans, { ...plan, _uid: uid }] }))
  },
  removePlan: (uid) =>
    set((state) => ({ plans: state.plans.filter((p) => p._uid !== uid) })),
  updatePlan: (uid, plan) =>
    set((state) => ({
      plans: state.plans.map((p) => (p._uid === uid ? { ...plan, _uid: p._uid } : p)),
    })),
  togglePlan: (uid) =>
    set((state) => ({
      plans: state.plans.map((p) =>
        p._uid === uid ? { ...p, enabled: !p.enabled } : p
      ),
    })),

  loadConfig: (payload: Record<string, unknown>) => {
    set((state) => {
      const keys = Object.keys(state) as (keyof State)[]
      const next: Partial<State> = {}
      for (const key of keys) {
        if (typeof state[key] === "function") continue
        if (!(key in payload)) continue
        if (key === "queue") {
          const raw = Array.isArray(payload.queue) ? payload.queue : (Array.isArray((payload as any).taskList) ? (payload as any).taskList : [])
          next.queue = raw.map((t: Record<string, unknown>) => ({
            taskName: (t.taskName ?? t.name ?? "") as string,
            version: (t.version ?? null) as string | null,
            author: (t.author ?? "匿名作者") as string,
            values: (t.values ?? {}) as Record<string, unknown>,
            valueTypes: t.valueTypes as Record<string, "text" | "number" | "bool" | "list"> | undefined,
            _uid: _nextTaskUid++,
          }))
        } else if (key === "plans") {
          const raw = Array.isArray(payload.plans) ? payload.plans : []
          next.plans = raw.map((p: Record<string, unknown>) => ({
            name: p.name as string,
            templateId: p.templateId as string,
            cron: p.cron as string,
            enabled: p.enabled as boolean,
            action: p.action as PlanBase["action"],
            _uid: _nextPlanUid++,
          }))
        } else {
          ;(next as any)[key] = payload[key as string]
        }
      }
      return next
    })
  },
}))
