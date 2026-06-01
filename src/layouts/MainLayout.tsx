import { type FC, useEffect, useRef, useState } from "react";
import { useSettingsStore } from "@/store/settings-store";
import { useTaskStore } from "@/store/task-store";
import { useUpdateStore } from "@/store/update-store";
import { waitForPywebview } from "@/utils/pywebview.ts";
import { compareVersion } from "@/utils/version";
import { Layout } from "antd";
import AppHeader from "@/components/app-header/AppHeader.tsx";
import DisclaimerModal from "@/components/disclaimer-modal/DisclaimerModal.tsx";
import UpdateModal from "@/components/update-modal/UpdateModal";
import UpdateProgress from "@/components/update-modal/UpdateProgress";
import FloatingPanel from "@/components/floating-panel/FloatingPanel.tsx";
import AppMenu from "@/components/app-menu/AppMenu.tsx";
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
      useSettingsStore.getState().loadSettings()
      useTaskStore.getState().loadTasks()

      // Check for updates on startup
      try {
        const currentVersion = await window.pywebview?.api.emit("API:APP:VERSION") as any
        if (currentVersion) {
          useUpdateStore.getState().setCurrentVersion(String(currentVersion))
        }

        const latest = await window.pywebview?.api.emit("API:UPDATE:CHECK") as any
        if (latest && latest.version && currentVersion) {
          const cur = String(currentVersion).replace(/^v/, "")
          const lat = String(latest.version).replace(/^v/, "")
          if (compareVersion(lat, cur) > 0) {
            useUpdateStore.getState().setUpdate({
              version: latest.version,
              changelog: latest.changelog,
              is_mandatory: latest.is_mandatory ?? false,
            })
          } else {
            import("antd").then(m => m.message.success("已是最新版本", 3))
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
    const es = new EventSource("https://elves.elarion.cn/api/v1/client/stream");
    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        if (d.type === "update") {
          const current = useUpdateStore.getState().currentVersion;
          const dVer = String(d.version).replace(/^v/, "");
          const cVer = String(current).replace(/^v/, "");
          if (current && compareVersion(dVer, cVer) > 0) {
            useUpdateStore.getState().setUpdate({
              version: d.version,
              changelog: d.changelog,
              is_mandatory: d.is_mandatory ?? false,
            });
          }
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
          className='bg-white'
          width={160}
        >
          <AppMenu collapsed={collapsed}/>
        </Sider>
        <Layout>
          <Header className="bg-white">
            <AppHeader/>
          </Header>
          <Content className="bg-white">
            <Outlet/>
          </Content>
        </Layout>
      </Layout>
    </>
  )
}


export default MainLayout