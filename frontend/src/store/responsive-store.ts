import { create } from 'zustand'

const DESIGN_WIDTH = 1335

type State = {
  zoom: number
  sync: () => void
}

function calcZoom() {
  return Math.round((window.innerWidth / DESIGN_WIDTH) * 1000) / 1000
}

export const useResponsiveStore = create<State>()((set) => ({
  zoom: 1,
  sync: () => {
    const zoom = calcZoom()
    document.documentElement.style.setProperty('--zoom', String(zoom))
    set({ zoom })
  }
}))
