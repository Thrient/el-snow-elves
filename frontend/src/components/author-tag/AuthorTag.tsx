import { type FC } from "react";
import { Dropdown } from "antd";
import type { MenuProps } from "antd";

interface Props {
  currentAuthor: string;
  availableAuthors: string[];
  onChange: (author: string) => void;
}

const AuthorTag: FC<Props> = ({ currentAuthor, availableAuthors, onChange }) => {
  // 只有一个作者且是匿名 → 不显示
  if (availableAuthors.length <= 1 && currentAuthor === "匿名作者") {
    return null;
  }

  const otherAuthors = availableAuthors.filter((a) => a !== currentAuthor);
  const hasOther = otherAuthors.length > 0;

  const items: MenuProps["items"] = otherAuthors.map((a) => ({
    key: a,
    label: <span className="font-mono text-[12px]">{a === "匿名作者" ? "匿名作者" : `@${a}`}</span>,
  }));

  const display = currentAuthor === "匿名作者" ? "" : `@${currentAuthor}`;

  if (!hasOther) {
    // 没有其他作者可切 → 静态文字
    return (
      <span className="text-[10px] text-muted font-mono select-none shrink-0">
        {display}
      </span>
    );
  }

  // 有其他作者可切 → 可点击的文字，hover 变色 + 显示箭头
  return (
    <Dropdown
      menu={{ items, onClick: ({ key }) => onChange(key) }}
      trigger={["click"]}
      placement="bottomLeft"
    >
      <span
        className="inline-flex items-baseline gap-px text-[10px] text-[#1677ff]/60 font-mono cursor-pointer select-none hover:text-[#1677ff] transition-colors shrink-0 group/at"
        onClick={(e) => e.stopPropagation()}
      >
        <span>{display}</span>
        <span className="text-[6px] opacity-0 group-hover/at:opacity-100 transition-opacity leading-none translate-y-[1px]">▼</span>
      </span>
    </Dropdown>
  );
};

export default AuthorTag;
