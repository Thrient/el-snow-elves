import { type FC } from "react";
import { Dropdown } from "antd";
import type { MenuProps } from "antd";
import { DownOutlined } from "@ant-design/icons";

interface Props {
  versions: string[];
  latest: string;
  selectedVersion: string | null;
  onChange: (version: string | null) => void;
  /** 当前锁定版本是否在 versions 列表中不存在 */
  stale?: boolean;
}

const VersionTag: FC<Props> = ({ versions, latest, selectedVersion, onChange, stale }) => {
  const currentVersion = selectedVersion ?? latest;
  const isLatest = !selectedVersion || selectedVersion === latest;

  const selIcon = (
    <span className="text-[8px] text-[#1677ff] leading-none flex-shrink-0">●</span>
  );
  const placeholder = (
    <span className="text-[8px] leading-none flex-shrink-0 invisible">●</span>
  );

  const menuItems: MenuProps["items"] = [
    {
      key: "latest",
      icon: isLatest ? selIcon : placeholder,
      label: (
        <div className="flex items-center justify-between gap-5">
          <span className="font-mono text-[13px]">v{latest}</span>
          <span className="text-[9px] bg-[#e6f4ff] text-[#1677ff] px-1.5 py-0.5 rounded font-medium leading-none select-none">
            最新
          </span>
        </div>
      ),
    },
    ...(versions.filter((v) => v !== latest).length > 0
      ? [{ type: "divider" as const }]
      : []),
    ...versions
      .filter((v) => v !== latest)
      .map((v) => ({
        key: v,
        icon: selectedVersion === v ? selIcon : placeholder,
        label: <span className="font-mono text-[13px]">v{v}</span>,
      })),
  ];

  const handleMenuClick: MenuProps["onClick"] = ({ key }) => {
    onChange(key === "latest" ? null : key);
  };

  const baseClass =
    "inline-flex items-center gap-1 text-[10px] border-none rounded font-mono px-1.5 leading-5 cursor-pointer transition-colors";

  const normalClass = "bg-[#f0f2f5] text-muted hover:bg-[#e6e9ee] hover:text-[#555]";
  const staleClass = "bg-[#fff2f0] text-[#ff4d4f] border border-[#ffccc7] hover:bg-[#ffe7e7]";

  return (
    <Dropdown
      menu={{ items: menuItems, onClick: handleMenuClick }}
      trigger={["click"]}
      placement="bottomRight"
      overlayClassName="version-dropdown"
    >
      <button
        className={`${baseClass} ${stale ? staleClass : normalClass}`}
        onClick={(e) => e.stopPropagation()}
        title={stale ? "该版本可能已被删除，点击切换" : undefined}
      >
        {stale && <span className="text-[10px] mr-0.5">⚠️</span>}
        v{currentVersion}
        {isLatest && (
          <span className="text-[8px] bg-[#e6f4ff] text-[#1677ff] px-1 py-0 leading-tight rounded font-sans font-medium select-none">
            最新
          </span>
        )}
        <DownOutlined className="text-[8px]" />
      </button>
    </Dropdown>
  );
};

export default VersionTag;
