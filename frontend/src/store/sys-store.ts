import { create } from 'zustand'
import { persist } from 'zustand/middleware';

type State = {
  currentConfig: string | null
  setCurrentConfig: (name: string | null) => void
  disclaimerAccepted: boolean
  acceptDisclaimer: () => void
}

export const useSysStore = create<State>()(
  persist(
    (set) => ({
      currentConfig: null,
      setCurrentConfig: (name: string | null) => set({ currentConfig: name }),
      disclaimerAccepted: false,
      acceptDisclaimer: () => set({ disclaimerAccepted: true }),
    }),
    { name: "sys-store" }
  )
)
