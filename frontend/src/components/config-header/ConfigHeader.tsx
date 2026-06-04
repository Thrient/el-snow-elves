import type { FC } from "react";
import { useCallback, useEffect, useState } from "react";
import { AutoComplete, Button, message, Modal, Select, Space, Spin } from "antd";
import { DeleteOutlined, FileOutlined, DownloadOutlined, SaveOutlined } from "@ant-design/icons";
import { useSessionStore } from "@/store/session-store.ts";
import { useSysStore } from "@/store/sys-store.ts";
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
            optionRender={(option) => (
              <div className="flex items-center justify-between w-full">
                <span className="truncate">{option.label}</span>
                <DeleteOutlined
                  className="text-[#d1d5db] hover:text-[#ef4444] transition-colors shrink-0 ml-2"
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
              </div>
            )}
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