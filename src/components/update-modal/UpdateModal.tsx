import { Modal, Button, Space } from "antd";
import { ArrowRightOutlined } from "@ant-design/icons";
import { useUpdateStore } from "@/store/update-store";

export default function UpdateModal() {
  const latestVersion = useUpdateStore(s => s.latestVersion);
  const changelog = useUpdateStore(s => s.changelog);
  const isMandatory = useUpdateStore(s => s.isMandatory);
  const checkModalOpen = useUpdateStore(s => s.checkModalOpen);
  const closeCheckModal = useUpdateStore(s => s.closeCheckModal);

  const currentVersion = useUpdateStore(s => s.currentVersion);

  const handleUpdate = async () => {
    useUpdateStore.getState().startDownload(0);
    closeCheckModal();

    try {
      const events = (await window.pywebview?.api.emit("API:UPDATE:DOWNLOAD", {
        current_version: useUpdateStore.getState().currentVersion,
      })) as any;

      if (events && Array.isArray(events)) {
        for (const ev of events) {
          if (ev.error) {
            useUpdateStore.getState().finishDownload();
            return;
          }
          if (ev.up_to_date) {
            useUpdateStore.getState().clearUpdate();
            return;
          }
          if (ev.done) {
            useUpdateStore.getState().finishDownload();
            return;
          }
          if (ev.progress !== undefined) {
            useUpdateStore.getState().updateProgress(
              ev.current ?? "下载中...",
              ev.index ?? 0,
            );
          }
        }
      }
    } catch {
      useUpdateStore.getState().finishDownload();
    }
  };

  return (
    <Modal
      open={checkModalOpen}
      closable={!isMandatory}
      maskClosable={!isMandatory}
      footer={null}
      width={400}
      centered
      title={<span className="text-sm font-bold">发现新版本</span>}
      onCancel={isMandatory ? undefined : closeCheckModal}
    >
      <div className="flex flex-col gap-4 pt-2">
        <div className="flex items-center justify-center gap-4 py-3 bg-[#f8fafc] rounded-xl">
          <span className="text-2xl font-bold text-[#9ca3af]">{currentVersion}</span>
          <ArrowRightOutlined className="text-[#1677ff]" />
          <span className="text-2xl font-bold text-[#1677ff]">{latestVersion}</span>
        </div>
        {changelog && (
          <div className="text-[12px] text-[#6b7280] bg-[#f9fafb] rounded-lg p-3 max-h-32 overflow-y-auto whitespace-pre-line thin-scrollbar">
            {changelog}
          </div>
        )}
        <Space className="mt-2">
          <Button type="primary" onClick={handleUpdate}>立即更新</Button>
          {!isMandatory && (
            <Button onClick={closeCheckModal}>暂不更新</Button>
          )}
        </Space>
        {isMandatory && (
          <span className="text-[11px] text-[#f5222d]">
            此版本为强制更新，必须升级后方可继续使用
          </span>
        )}
      </div>
    </Modal>
  );
}
