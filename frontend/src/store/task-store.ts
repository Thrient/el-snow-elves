import { create } from 'zustand'
import type { Task } from "@/types/task"

type State = {
  taskList: Task[]
  loading: boolean
}

type Actions = {
  loadTasks: () => Promise<void>
  updateTaskValues: (id: string, values: Record<string, unknown>) => void
}

export const useTaskStore = create<State & Actions>((set) => ({
  taskList: [],
  loading: true,

  loadTasks: async () => {
    try {
      const result = await window.pywebview?.api.emit("API:SCRIPT:LOAD:LIST")
      set({ taskList: (result ?? []) as Task[], loading: false })
    } catch {
      set({ loading: false })
    }
  },

  updateTaskValues: (id, values) =>
    set((state) => ({
      taskList: state.taskList.map((t) =>
        t.id === id ? { ...t, values } : t
      ),
    })),
}))
