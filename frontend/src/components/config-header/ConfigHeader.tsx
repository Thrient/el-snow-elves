import type { FC } from "react";
import { useCallback, useEffect, useState } from "react";
import { AutoComplete, Button, message, Modal, Select, Space, Spin, Tooltip } from "antd";
import { DeleteOutlined, FileOutlined, DownloadOutlined, SaveOutlined, SendOutlined } from "@ant-design/icons";
import { useSessionStore } from "@/store/session-store.ts";
import { useSysStore } from "@/store/sys-store.ts";
import { useCharacterStore } from "@/store/character-store.ts";
import { callApi, waitForPywebview } from "@/utils/pywebview.ts";

const ConfigHeader: FC = () => {
  const [configFiles, setConfigFiles] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saveModalOpen, setSaveModalOpen] = useState(false)
  const [saveName, setSaveName] = useState("")
  const [loadingConfig, setLoadingConfig] = useState(false)
  const sysStore = useSysStore()
  const userStore = useSessionStore()

  const fetchConfigFiles = useCallback(async () => {
    try {
      await waitForPywebview()
      const result = await callApi<string[]>("API:SCRIPT:LOAD:CONFIG:LIST")
      setConfigFiles(result ?? [])
    } catch {
      setConfigFiles([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConfigFiles()
  }, [fetchConfigFiles])

  useEffect(() => {
    if (!loading && sysStore.currentConfig && configFiles.includes(sysStore.currentConfig)) {
      setLoadingConfig(true)
      loadConfig(sysStore.currentConfig)
    }
  }, [loading, configFiles, sysStore.currentConfig])

  const loadConfig = async (name: string) => {
    try {
      const result = await callApi<Record<string, unknown>>("API:SCRIPT:LOAD:CONFIG", name)
      if (result) {
        userStore.loadConfig(result)
        // 校验队列中的任务是否仍然存在
        const taskList = useCharacterStore.getState().taskList
        const queue = useSessionStore.getState().queue
        const missing = queue.filter((entry: any) => {
          const tn = entry.taskName || entry.name
          return tn && !taskList.find((t: any) => t.name === tn)
        })
        if (missing.length > 0) {
          const names = [...new Set(missing.map((e: any) => e.taskName || e.name))]
          message.warning(`配置中有 ${names.length} 个任务已不存在：${names.join("、")}`)
        }
      }
    } catch { /* empty */ } finally {
      setLoadingConfig(false)
    }
  }

  const handleDelete = async (name: string) => {
    try {
      await callApi("API:SCRIPT:DELETE:CONFIG", name)
      message.success(`已删除「${name}」`)
      if (sysStore.currentConfig === name) {
        sysStore.setCurrentConfig(null)
      }
      await fetchConfigFiles()
    } catch { message.error("删除失败") }
  }

  const handleApplyToWindow = async (configName: string) => {
    const charStore = useCharacterStore.getState()
    const hwnd = charStore.selectedHwnd
    if (!hwnd) return

    try {
      const result = await callApi<Record<string, any>>("API:SCRIPT:LOAD:CONFIG", configName)
      if (!result) {
        message.error("加载配置失败")
        return
      }

      const queue = (result.queue || []) as any[]
      const plans = (result.plans || []) as any[]

      if (queue.length === 0 && plans.length === 0) {
        message.warning("该配置中没有待执行任务和计划")
        return
      }

      const taskList = charStore.taskList
      const missing = queue.filter((entry: any) => {
        const tn = entry.taskName || entry.name
        return tn && !taskList.find((t: any) => t.name === tn)
      })

      if (queue.length > 0) {
        const items = queue.map((t: any) => ({
          id: t.id || "",
          name: t.taskName || t.name,
          taskName: t.taskName || t.name,
          version: t.version ?? null,
          author: t.author ?? "匿名作者",
          values: t.values ?? {},
          valueTypes: t.valueTypes,
        }))
        charStore.pushExecuteBatch(hwnd, items)
      }

      if (plans.length > 0) {
        charStore.setPlans(hwnd, plans)
      }

      const charName = charStore.characters.find(c => c.hwnd === hwnd)?.hwnd || hwnd
      const parts: string[] = []
      if (queue.length > 0) parts.push(`${queue.length} 个任务`)
      if (plans.length > 0) parts.push(`${plans.length} 个计划`)
      message.success(`已将 ${parts.join(" 和 ")} 添加到窗口 ${charName}`)

      if (missing.length > 0) {
        const names = [...new Set(missing.map((e: any) => e.taskName || e.name))]
        message.warning(`配置中有 ${names.length} 个任务已不存在：${names.join("、")}`)
      }
    } catch {
      message.error("加载配置失败")
    }
  }

  const handleSaveClick = () => {
    setSaveModalOpen(true)
  }

  const handleSaveConfirm = () => {
    if (!saveName.trim()) return
    setSaving(true)
    setSaveModalOpen(false)
    const state = useSessionStore.getState()
    const payload: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(state)) {
      if (typeof value !== "function") {
        payload[key] = value
      }
    }
    window.pywebview?.api.emit("API:SCRIPT:SAVE:CONFIG", saveName, payload).then(() => {
      setSaving(false)
    })
  }

  return (
    <>
      <Space size='middle'>
        <FileOutlined className="text-lg text-[#1677ff]"/>
        <Spin spinning={loading || loadingConfig} size="small">
          <Select
            className='w-200px'
            placeholder="配置文件"
            value={sysStore.currentConfig}
            notFoundContent={loading ? "加载中..." : "暂无配置文件"}
            onChange={(value) => {
              setLoadingConfig(true)
              sysStore.setCurrentConfig(value)
              loadConfig(value)
            }}
            options={configFiles.map((file) => ({ value: file, label: file }))}
            optionRender={(option) => {
              const selectedHwnd = useCharacterStore.getState().selectedHwnd
              return (
                <div className="flex items-center justify-between w-full">
                  <span className="truncate">{option.label}</span>
                  <span className="flex items-center shrink-0 ml-2 gap-1">
                    <Tooltip title={!selectedHwnd ? "请先在窗口页面选择一个绑定的窗口" : "应用配置到当前窗口"}>
                      <SendOutlined
                        className="transition-colors"
                        style={{
                          color: !selectedHwnd ? "#d1d5db" : "#d1d5db",
                          opacity: !selectedHwnd ? 0.3 : 1,
                          cursor: !selectedHwnd ? "not-allowed" : "pointer",
                          fontSize: 14,
                        }}
                        onMouseEnter={(e) => {
                          if (selectedHwnd) e.currentTarget.style.color = "#1677ff"
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = "#d1d5db"
                        }}
                        onClick={(e) => {
                          e.stopPropagation()
                          if (!selectedHwnd) return
                          handleApplyToWindow(option.value as string)
                        }}
                      />
                    </Tooltip>
                    <DeleteOutlined
                      className="text-[#d1d5db] hover:text-[#ef4444] transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        Modal.confirm({
                          title: `删除「${option.label}」？`,
                          content: "此操作不可恢复",
                          okText: "删除",
                          okType: "danger",
                          cancelText: "取消",
                          onOk: () => handleDelete(option.value as string),
                        })
                      }}
                    />
                  </span>
                </div>
              )
            }}
          />
        </Spin>
        <Button
          icon={<DownloadOutlined/>}
          onClick={() => {
            setLoading(true)
            fetchConfigFiles()
          }}
          loading={loading}
        >
          刷新
        </Button>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSaveClick}
          loading={saving}
        >
          保存
        </Button>
      </Space>

      <Modal
        title="保存配置"
        open={saveModalOpen}
        onOk={handleSaveConfirm}
        onCancel={() => setSaveModalOpen(false)}
        okButtonProps={{ disabled: !saveName.trim() }}
        okText="保存"
        cancelText="取消"
      >
        <div className="mt-4">
          <AutoComplete
            className="w-full"
            placeholder="输入配置文件名"
            value={saveName}
            onChange={setSaveName}
            options={configFiles.map((file) => ({ value: file }))}
          />
        </div>
      </Modal>
    </>
  )
}

export default ConfigHeader;