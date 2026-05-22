import { Badge, Button, Tooltip } from "antd";
import { SyncOutlined } from "@ant-design/icons";
import { useUpdateStore } from "@/store/update-store";

export default function UpdateCheckBadge() {
  const hasUpdate = useUpdateStore(s => s.hasUpdate);
  const openCheckModal = useUpdateStore(s => s.openCheckModal);

  return (
    <Tooltip title={hasUpdate ? "发现新版本" : "检查更新"}>
      <Badge dot={hasUpdate} color="#f5222d" offset={[-3, 3]}>
        <Button
          type="text"
          size="small"
          icon={<SyncOutlined />}
          onClick={openCheckModal}
          className="!text-[#6b7280] hover:!text-[#1677ff]"
        />
      </Badge>
    </Tooltip>
  );
}
