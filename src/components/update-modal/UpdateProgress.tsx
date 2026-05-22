import { Modal, Button, Progress } from "antd";
import { CheckCircleFilled, LoadingOutlined } from "@ant-design/icons";
import { useUpdateStore } from "@/store/update-store";

export default function UpdateProgress() {
  const downloading = useUpdateStore(s => s.downloading);
  const downloadDone = useUpdateStore(s => s.downloadDone);
  const progress = useUpdateStore(s => s.progress);
  const currentFile = useUpdateStore(s => s.currentFile);
  const completedFiles = useUpdateStore(s => s.completedFiles);
  const totalFiles = useUpdateStore(s => s.totalFiles);

  if (!downloading && !downloadDone) return null;

  const handleRestart = () => {
    window.pywebview?.api.emit("API:UPDATE:APPLY");
  };

  return (
    <Modal
      open={true}
      closable={false}
      maskClosable={false}
      footer={null}
      width={420}
      centered
      title={
        <span className="text-sm font-bold">
          {downloadDone ? "更新完成" : "正在下载更新..."}
        </span>
      }
    >
      <div className="flex flex-col gap-4 pt-2">
        <Progress
          percent={progress}
          status={downloadDone ? "success" : "active"}
          strokeColor="#1677ff"
        />
        <div className="text-[12px] text-[#6b7280]">
          {completedFiles} / {totalFiles} 文件
        </div>
        {!downloadDone && (
          <div className="text-[11px] text-[#9ca3af] truncate">
            <LoadingOutlined className="mr-1" />
            {currentFile}
          </div>
        )}
        {downloadDone && (
          <div className="flex flex-col gap-3">
            <div className="text-[12px] text-[#16a34a] flex items-center gap-1">
              <CheckCircleFilled />
              所有文件下载完成，需要重启应用以应用更新
            </div>
            <Button type="primary" onClick={handleRestart}>
              立即重启
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}
