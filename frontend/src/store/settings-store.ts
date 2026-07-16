import { create } from 'zustand'
import type { Cell } from '@/types/task'

export type Layout = Cell[][]

export type ThemeMode = 'auto' | 'light' | 'dark'

type State = {
  values: Record<string, unknown>
  layout: Layout
  theme: ThemeMode
}

type Actions = {
  loadSettings: () => Promise<void>
  updateValue: (key: string, value: unknown) => void
  setTheme: (t: ThemeMode) => void
}

export const useSettingsStore = create<State & Actions>()(
  (set, get) => ({
    values: {},
    layout: [],
    theme: 'auto',

    loadSettings: async () => {
      const result = await window.pywebview?.api.emit("API:SETTINGS:LOAD")
      if (result) {
        const remote = result as { values?: Record<string, unknown>; layout?: Layout }
        const vals = remote.values ?? {}
        const savedTheme = vals['app-theme'] as ThemeMode | undefined
        const theme = savedTheme && ['auto', 'light', 'dark'].includes(savedTheme) ? savedTheme : 'auto'
        set({
          values: vals,
          layout: remote.layout ?? [],
          theme,
        })
        get().setTheme(theme)
      }
    },

    updateValue: (key, value) =>
      set((state) => ({
        values: { ...state.values, [key]: value },
      })),

    setTheme: (t) => {
      const html = document.documentElement
      window.pywebview?.api.emit("API:APP:SET_THEME", { theme: t })
      const updateColorScheme = (dark: boolean) => {
        html.style.colorScheme = dark ? 'dark' : 'light'
      }
      if (t === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        html.dataset.theme = prefersDark ? 'dark' : 'light'
        updateColorScheme(prefersDark)
        const mq = window.matchMedia('(prefers-color-scheme: dark)')
        const handler = (e: MediaQueryListEvent) => {
          html.dataset.theme = e.matches ? 'dark' : 'light'
          updateColorScheme(e.matches)
        }
        mq.addEventListener('change', handler)
        ;(html as HTMLElement & { __themeListener?: { mq: MediaQueryList; handler: (e: MediaQueryListEvent) => void } }).__themeListener = { mq, handler }
      } else {
        const prev = (html as HTMLElement & { __themeListener?: { mq: MediaQueryList; handler: (e: MediaQueryListEvent) => void } }).__themeListener
        if (prev) { prev.mq.removeEventListener('change', prev.handler) }
        html.dataset.theme = t
        updateColorScheme(t === 'dark')
      }
      set((state) => ({ theme: t, values: { ...state.values, 'app-theme': t } }))
    },
  })
)

// 订阅 values 变化，debounce 2s 自动保存到 Python 端
let _saveTimer: ReturnType<typeof setTimeout> | null = null

useSettingsStore.subscribe((state: State) => {
  const { values } = state
  if (Object.keys(values).length === 0) return
  if (_saveTimer) clearTimeout(_saveTimer)
  _saveTimer = setTimeout(() => {
    window.pywebview?.api.emit("API:SETTINGS:SAVE", values)
    _saveTimer = null
  }, 2000)
})
