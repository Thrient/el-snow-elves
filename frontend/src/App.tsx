import { ConfigProvider, theme } from 'antd'
import { RouterProvider } from 'react-router-dom'
import zhCN from 'antd/locale/zh_CN'
import { router } from "@/router";
import "@/store/index";
import { useSettingsStore } from '@/store/settings-store'

function App() {
  const currentTheme = useSettingsStore(s => s.theme)

  const resolvedTheme: 'light' | 'dark' =
    currentTheme === 'auto'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
      : currentTheme === 'dark' ? 'dark' : 'light'

  return (
    <ConfigProvider locale={zhCN} theme={{
      algorithm: resolvedTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    }}>
      <RouterProvider router={router}/>
    </ConfigProvider>
  )
}

export default App
