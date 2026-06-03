import type { FC } from "react";
import ConfigHeader from "@/components/config-header/ConfigHeader.tsx";
import { Badge, Button, Typography } from "antd";
import { StopOutlined, PlayCircleOutlined } from "@ant-design/icons";
import UpdateCheckBadge from "@/components/update-check/UpdateCheckBadge";

const {Text} = Typography;

const AppHeader: FC = () => {
  const running = true;

  return (
    <div className="flex">
      <div className="w-75%">
        <ConfigHeader/>
      </div>
      <div className="w-25% flex justify-end items-center gap-20px">
        <UpdateCheckBadge />
        <Badge
          count={0}
          className="min-w-71px"
          color="#52C41A"
        >
          <Text>运行中窗口</Text>
        </Badge>
        {running ? (
          <Button
            danger
            icon={<StopOutlined/>}
          >
            全部停止
          </Button>
        ) : (
          <Button
            type="primary"
            icon={<PlayCircleOutlined/>}
          >
            全部开始
          </Button>
        )}
      </div>
    </div>
  )
}

export default AppHeader