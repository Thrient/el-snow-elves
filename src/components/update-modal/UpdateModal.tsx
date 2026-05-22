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
    closeCheckModal();

    try {
      const result = (await window.pywebview?.api.emit("API:UPDATE:DOWNLOAD", {
        current_version: useUpdateStore.getState().currentVersion,
      })) as any;

      if (!result || !Array.isArray(result)) {
        useUpdateStore.getState().finishDownload();
        return;
      }

      const firstEv = result[0];
      if (firstEv.error) {
        useUpdateStore.getState().finishDownload();
        return;
      }
      if (firstEv.up_to_date) {
        useUpdateStore.getState().clearUpdate();
        return;
      }

      const total = firstEv.total ?? result.length;
      useUpdateStore.getState().startDownload(total);
      // yield to React so the modal renders with totalFiles set
      await new Promise(r => setTimeout(r, 50));

      for (const ev of result) {
        if (ev.done) {
          useUpdateStore.getState().finishDownload();
          return;
        }
        if (ev.progress !== undefined) {
          useUpdateStore.getState().updateProgress(
            ev.current ?? "下载中...",
            ev.index ?? 0,
          );
          // yield to React between each file so progress bar animates
          await new Promise(r => setTimeout(r, 10));
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
