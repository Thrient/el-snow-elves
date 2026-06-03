import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Cell } from '@/types/task'

export type Layout = Cell[][]

type State = {
  values: Record<string, unknown>
  layout: Layout
  loaded: boolean
}

type Actions = {
  loadSettings: () => Promise<void>
  updateValue: (key: string, value: unknown) => void
}

export const useSettingsStore = create<State & Actions>()(
  persist(
    (set, get) => ({
      values: {},
      layout: [],
      loaded: false,

      loadSettings: async () => {
        try {
          const result = await window.pywebview?.api.emit("API:SETTINGS:LOAD")
          if (result) {
            const remote = result as { values?: Record<string, unknown>; layout?: Layout }
            const current = get().values

            // remote 作为默认值, local 的覆盖仅对 remote 中仍存在的 key 生效
            const base = { ...(remote.values ?? {}) }
            for (const key of Object.keys(current)) {
              if (key in base) {
                base[key] = current[key]
              }
            }

            set({
              values: base,
              layout: remote.layout ?? [],
              loaded: true,
            })
          } else {
            set({ loaded: true })
          }
        } catch {
          set({ loaded: true })
        }
      },

      updateValue: (key, value) =>
        set((state) => ({
          values: { ...state.values, [key]: value },
        })),
    }),
    {
      name: "settings-store",
      partialize: (state) => ({ values: state.values }),
      version: 3,
      migrate: () => ({ values: {}, layout: [], loaded: false }),
    }
  )
)
