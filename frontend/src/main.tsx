import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App as AntApp } from 'antd'
import 'virtual:uno.css'
import '@/index.css'
import App from '@/App.tsx'
import { useResponsiveStore } from '@/store/responsive-store'

useResponsiveStore.getState().sync()

let rafId = 0
window.addEventListener('resize', () => {
  if (rafId) return
  rafId = requestAnimationFrame(() => {
    rafId = 0
    useResponsiveStore.getState().sync()
  })
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AntApp>
      <App/>
    </AntApp>
  </StrictMode>,
)
