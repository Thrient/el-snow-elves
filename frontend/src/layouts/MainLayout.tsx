import { type FC, useEffect, useRef, useState } from "react";
import { useSettingsStore } from "@/store/settings-store";
import { useCharacterStore } from "@/store/character-store";
import { useUpdateStore } from "@/store/update-store";
import { waitForPywebview } from "@/utils/pywebview.ts";
import { Layout, message } from "antd";
import AppHeader from "@/components/app-header/AppHeader.tsx";
import DisclaimerModal from "@/components/disclaimer-modal/DisclaimerModal.tsx";
import UpdateModal from "@/components/update-modal/UpdateModal";
import UpdateProgress from "@/components/update-modal/UpdateProgress";
import FloatingPanel from "@/components/floating-panel/FloatingPanel.tsx";
import AppMenu from "@/components/app-menu/AppMenu.tsx";
import AppNotification from '@/components/app-notification/AppNotification';
import { Outlet } from 'react-router-dom'


const {Header, Sider, Content} = Layout


const MainLayout: FC = () => {

  const [collapsed, setCollapsed] = useState<boolean>(false)
  const checked = useRef(false)

  useEffect(() => {
    if (checked.current) return
    checked.current = true

    const init = async () => {
      await waitForPywebview()
      void useSettingsStore.getState().loadSettings()
      void useCharacterStore.getState().loadTasks()

      // Check for updates on startup
      try {
        const currentVersion = await window.pywebview?.api.emit("API:APP:VERSION") as any
        if (currentVersion) {
          useUpdateStore.getState().setCurrentVersion(String(currentVersion))
        }

        const latest = await window.pywebview?.api.emit("API:UPDATE:CHECK") as any
        if (latest?.version && currentVersion) {
          const hasUpdate = useUpdateStore.getState().checkUpdate(latest);
          if (!hasUpdate) {
            message.success("已是最新版本", 3);
          }
        }
      } catch {
        // update check failed silently
      }
    }
    init()
  }, [])

  // SSE for real-time update push from hub
  useEffect(() => {
    const es = new EventSource("https://elves.elarion.cn/api/v1/stream?client=desktop");
    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        if (d.type === "update") {
          useUpdateStore.getState().checkUpdate({
            version: d.version,
            changelog: d.changelog,
            is_mandatory: d.is_mandatory ?? false,
          });
        }
      } catch {
        // malformed SSE payload, ignore
      }
    };
    es.onerror = () => {
      // EventSource auto-reconnects
    };
    return () => es.close();
  }, [])

  return (
    <>
      <AppNotification />
      <FloatingPanel />
      <DisclaimerModal />
      <UpdateModal />
      <UpdateProgress />
      <Layout className='h-full'>
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={(value) => setCollapsed(value)}
          theme='light'
          className='!bg-container'
          width={160}
        >
          <AppMenu collapsed={collapsed}/>
        </Sider>
        <Layout>
          <Header className="!bg-container">
            <AppHeader/>
          </Header>
          <Content className="!bg-container">
            <Outlet/>
          </Content>
        </Layout>
      </Layout>
    </>
  )
}


export default MainLayout