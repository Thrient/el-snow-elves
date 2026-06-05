import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Cell } from '@/types/task'

export type Layout = Cell[][]

export type ThemeMode = 'auto' | 'light' | 'dark'

type State = {
  values: Record<string, unknown>
  layout: Layout
  loaded: boolean
  theme: ThemeMode
}

type Actions = {
  loadSettings: () => Promise<void>
  updateValue: (key: string, value: unknown) => void
  setTheme: (t: ThemeMode) => void
}

export const useSettingsStore = create<State & Actions>()(
  persist(
    (set, get) => ({
      values: {},
      layout: [],
      loaded: false,
      theme: (localStorage.getItem('app-theme') as ThemeMode) || 'auto',

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

      setTheme: (t) => {
        const html = document.documentElement
        if (t === 'auto') {
          const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
          html.dataset.theme = prefersDark ? 'dark' : 'light'
          // Listen for changes
          const mq = window.matchMedia('(prefers-color-scheme: dark)')
          const handler = (e: MediaQueryListEvent) => {
            html.dataset.theme = e.matches ? 'dark' : 'light'
          }
          mq.addEventListener('change', handler)
          // Store listener ref for cleanup
          ;(html as any).__themeListener = { mq, handler }
        } else {
          // Remove auto listener if exists
          const prev = (html as any).__themeListener
          if (prev) { prev.mq.removeEventListener('change', prev.handler) }
          html.dataset.theme = t
        }
        localStorage.setItem('app-theme', t)
        set({ theme: t })
      },
    }),
    {
      name: "settings-store",
      partialize: (state) => ({ values: state.values }),
      version: 3,
      migrate: () => ({ values: {}, layout: [], loaded: false }),
    }
  )
)
