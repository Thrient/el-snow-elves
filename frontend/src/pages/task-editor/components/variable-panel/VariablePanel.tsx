import { useMemo, useState, type FC } from "react";
import { Button, Input, Tag, Tooltip } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { insertAtCursor } from "@/utils/insert-at-cursor";
import {
  type VariableCategory,
  type VariableItem,
  VARIABLE_CATEGORY_LABELS,
  SYSTEM_VARIABLES,
} from "@/types/variable";

interface Props {
  taskValues: Record<string, unknown>;
  configKeys: string[];
  stepNames: string[];
  setVariables: string[];
  visible: boolean;
  onToggle: () => void;
}

const VariablePanel: FC<Props> = ({
  taskValues,
  configKeys,
  stepNames,
  setVariables,
  visible,
  onToggle,
}) => {
  const [search, setSearch] = useState("");

  const allVars = useMemo<VariableItem[]>(() => {
    const items: VariableItem[] = [...SYSTEM_VARIABLES];

    for (const key of configKeys) {
      items.push({ syntax: `{CONFIG.${key}}`, label: `{CONFIG.${key}}`, category: "config" });
    }
    for (const key of Object.keys(taskValues)) {
      items.push({ syntax: `{${key}}`, label: `{${key}}`, category: "task" });
    }
    for (const name of stepNames) {
      items.push({ syntax: name, label: name, category: "step" });
    }
    for (const v of setVariables) {
      if (!(v in taskValues)) {
        items.push({ syntax: `{${v}}`, label: `{${v}}`, category: "task" });
      }
    }
    return items;
  }, [taskValues, configKeys, stepNames, setVariables]);

  const filtered = useMemo(() => {
    if (!search.trim()) return allVars;
    const q = search.toLowerCase();
    return allVars.filter(
      (v) =>
        v.syntax.toLowerCase().includes(q) ||
        v.label.toLowerCase().includes(q) ||
        VARIABLE_CATEGORY_LABELS[v.category].includes(q)
    );
  }, [allVars, search]);

  const grouped = useMemo(() => {
    const map = new Map<VariableCategory, VariableItem[]>();
    for (const item of filtered) {
      const list = map.get(item.category) ?? [];
      list.push(item);
      map.set(item.category, list);
    }
    return map;
  }, [filtered]);

  const colors: Record<VariableCategory, string> = {
    config: "blue",
    task: "green",
    system: "purple",
    step: "orange",
  };

  if (!visible) return null;

  return (
    <div className="w-56 shrink-0 border-l border-[#eef0f2] bg-[#fafbfc] flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-3 border-b border-[#eef0f2] shrink-0">
        <span className="text-xs font-semibold text-[#1a1a2e]">变量</span>
        <Button
          type="text"
          size="small"
          onClick={onToggle}
          className="!text-xs !text-[#8b8fa3]"
        >
          收起
        </Button>
      </div>
      <div className="px-3 py-2 shrink-0">
        <Input
          size="small"
          prefix={<SearchOutlined className="text-[#8b8fa3]" />}
          placeholder="搜索变量..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
        />
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-2">
        {Array.from(grouped.entries()).map(([cat, items]) => (
          <div key={cat} className="mb-3">
            <div className="text-[10px] text-[#8b8fa3] font-medium mb-1.5 uppercase tracking-wide">
              {VARIABLE_CATEGORY_LABELS[cat]}
            </div>
            <div className="flex flex-wrap gap-1.5">
              {items.map((item) => (
                <Tooltip key={item.syntax} title={item.label}>
                  <Tag
                    color={colors[cat]}
                    className="cursor-pointer m-0 text-[11px] px-2 py-0.5"
                    onClick={() => insertAtCursor(item.syntax)}
                  >
                    {item.syntax}
                  </Tag>
                </Tooltip>
              ))}
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="text-xs text-center text-[#8b8fa3] py-4">无匹配变量</div>
        )}
      </div>
    </div>
  );
};

export default VariablePanel;
