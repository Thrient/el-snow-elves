import { useState } from "react";
import { Button, Tooltip, message } from "antd";
import { SyncOutlined } from "@ant-design/icons";
import { useUpdateStore } from "@/store/update-store";

export default function UpdateCheckBadge() {
  const hasUpdate = useUpdateStore((s) => s.hasUpdate);
  const [spinning, setSpinning] = useState(false);

  const handleCheck = async () => {
    if (spinning) return;
    setSpinning(true);
    try {
      const latest = (await window.pywebview?.api.emit("API:UPDATE:CHECK")) as any;
      if (!latest?.version) {
        setSpinning(false);
        return;
      }
      const hasUpdate = useUpdateStore.getState().checkUpdate(latest);
      if (!hasUpdate) {
        message.success("已是最新版本", 3);
      }
    } catch {
      // silent
    }
    setSpinning(false);
  };

  return (
    <Tooltip title={hasUpdate ? "发现新版本" : "检查更新"}>
      <span className="relative inline-flex">
        <Button
          type="text"
          size="small"
          icon={<SyncOutlined spin={spinning} />}
          onClick={handleCheck}
          className="!text-secondary hover:!text-[#1677ff]"
        />
        {hasUpdate && (
          <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-[#f5222d] rounded-full ring-2 ring-white" />
        )}
      </span>
    </Tooltip>
  );
}
