import { useState } from "react";
import { Button, Tooltip, message } from "antd";
import { SyncOutlined } from "@ant-design/icons";
import { useUpdateStore } from "@/store/update-store";

function compareVersion(a: string, b: string): number {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const na = pa[i] ?? 0;
    const nb = pb[i] ?? 0;
    if (na > nb) return 1;
    if (na < nb) return -1;
  }
  return 0;
}

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
      const currentVersion = useUpdateStore.getState().currentVersion;
      const cur = String(currentVersion).replace(/^v/, "");
      const lat = String(latest.version).replace(/^v/, "");
      if (compareVersion(lat, cur) > 0) {
        useUpdateStore.getState().setUpdate({
          version: latest.version,
          changelog: latest.changelog,
          is_mandatory: latest.is_mandatory ?? false,
        });
      } else {
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
          className="!text-[#6b7280] hover:!text-[#1677ff]"
        />
        {hasUpdate && (
          <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-[#f5222d] rounded-full ring-2 ring-white" />
        )}
      </span>
    </Tooltip>
  );
}
