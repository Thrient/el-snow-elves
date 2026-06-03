import { ConfigProvider } from 'antd'
import { RouterProvider } from 'react-router-dom'
import zhCN from 'antd/locale/zh_CN'
import { router } from "@/router";
import "@/store/index";

const theme = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
    colorBorder: '#eef0f2',
  },
}

function App() {
  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <RouterProvider router={router}/>
    </ConfigProvider>
  )
}

export default App
