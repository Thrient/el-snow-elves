import { useState, useMemo, type FC } from "react";
import { Input, Popover } from "antd";
import { SearchOutlined } from "@ant-design/icons";

type VarOp = "get" | "inc" | "dec" | "default" | "sub" | "len" | "split";

interface OpBtn {
  key: VarOp;
  label: string;
  syntax: (bareName: string) => string;
  hint: string;
}

const ALL_OPS: OpBtn[] = [
  { key: "get",     label: "取值",    syntax: (n) => `{${n}}`,        hint: "直接取变量值" },
  { key: "default", label: "默认",    syntax: (n) => `{${n}:}`,       hint: "变量不存在时用默认值" },
  { key: "inc",     label: "++",      syntax: (n) => `{${n}}++`,      hint: "自增 1（用于 set）" },
  { key: "dec",     label: "--",      syntax: (n) => `{${n}}--`,      hint: "自减 1（用于 set）" },
  { key: "len",     label: "长度",    syntax: (n) => `len(${n})`,     hint: "列表元素个数" },
  { key: "sub",     label: "[0]",     syntax: (n) => `{${n}}[0]`,     hint: "取列表下标元素" },
  { key: "split",   label: "split",  syntax: (n) => `split({${n}}, '#')`, hint: "按分隔符拆分为列表" },
];

interface VarItem {
  syntax: string;
  label: string;
  category: "config" | "task" | "system" | "step";
}

interface Props {
  variables: VarItem[];
  onInsert: (expr: string) => void;
  children?: React.ReactNode;
  placeholder?: string;
  context?: "set" | "when" | "args" | "params";
}

const CAT_LABELS: Record<string, string> = {
  config: "全局设置",
  task: "任务变量",
  system: "系统",
  step: "步骤名",
};

const CAT_COLORS: Record<string, string> = {
  system: "#8b5cf6",
  config: "#3b82f6",
  task: "#10b981",
  step: "#f59e0b",
};

// Top ops per context, rest shown on expand
const TOP_COUNT = 3;
const CONTEXT_ORDER: Record<string, VarOp[]> = {
  set:    ["inc", "dec", "get", "default", "len", "sub", "split"],
  when:   ["len", "get", "sub", "split", "inc", "dec", "default"],
  args:   ["get", "default", "len", "sub", "split", "inc", "dec"],
  params: ["get", "default", "sub", "split", "len", "inc", "dec"],
};

const VariablePicker: FC<Props> = ({ variables, onInsert, children, placeholder, context }) => {
  const [search, setSearch] = useState("");
  const [recentVar, setRecentVar] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const orderedOps = useMemo(() => {
    if (!context) return ALL_OPS;
    const order = CONTEXT_ORDER[context] ?? ALL_OPS.map((o) => o.key);
    const byKey = new Map(ALL_OPS.map((o) => [o.key, o]));
    return order.map((k) => byKey.get(k)!).filter(Boolean);
  }, [context]);

  const topOps = useMemo(() => orderedOps.slice(0, TOP_COUNT), [orderedOps]);
  const moreOps = useMemo(() => orderedOps.slice(TOP_COUNT), [orderedOps]);

  const filtered = useMemo(() => {
    if (!search.trim()) return variables;
    const q = search.toLowerCase();
    return variables.filter(
      (v) => v.syntax.toLowerCase().includes(q) || v.label.toLowerCase().includes(q),
    );
  }, [variables, search]);

  const grouped = useMemo(() => {
    const map = new Map<string, VarItem[]>();
    for (const item of filtered) {
      const list = map.get(item.category) ?? [];
      list.push(item);
      map.set(item.category, list);
    }
    return map;
  }, [filtered]);

  const handlePick = (bareName: string, op: VarOp) => {
    const opDef = ALL_OPS.find((o) => o.key === op);
    if (!opDef) return;
    setRecentVar(bareName);
    onInsert(opDef.syntax(bareName));
  };

  const toggleExpand = (key: string) => {
    setExpandedRows((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };

  const content = (
    <div className="w-340px max-h-420px flex flex-col">
      {/* Search */}
      <div className="pb-2.5 shrink-0">
        <Input
          size="small"
          prefix={<SearchOutlined className="c-[#b8afa6]" />}
          placeholder={placeholder ?? "搜索变量…"}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          className="rounded-[10px]"
        />
      </div>

      {/* Variable list */}
      <div className="flex-1 overflow-y-auto">
        {Array.from(grouped.entries()).map(([cat, items]) => {
          const dot = CAT_COLORS[cat] ?? "#9ca3af";
          return (
            <div key={cat} style={{ marginBottom: 12 }}>
              <div className="text-[10px] font-semibold c-[#9ca3af] tracking-[0.04em] mb-1.5 px-1 flex items-center gap-1.5">
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: dot, flexShrink: 0 }} />
                {CAT_LABELS[cat] ?? cat}
              </div>
              <div className="flex flex-col gap-[3px]">
                {items.map((item) => {
                  const bare = item.syntax.replace(/^\{|\}$/g, "");
                  const isRecent = recentVar === bare;
                  const isExpanded = expandedRows.has(item.syntax);

                  return (
                    <div
                      key={item.syntax}
                      onDoubleClick={() => handlePick(bare, orderedOps[0].key)}
                      className={`flex items-center gap-1.5 py-[5px] px-2 rounded-[10px] cursor-default transition-colors duration-150 ${isRecent ? "bg-[#fef3ef]" : "bg-transparent"}`}
                      onMouseEnter={(e) => { if (!isRecent) e.currentTarget.style.background = "#f5f4f0"; }}
                      onMouseLeave={(e) => { if (!isRecent) e.currentTarget.style.background = "transparent"; }}
                    >
                      {/* Variable name */}
                      <code
                        className="text-xs font-semibold c-[#3d3630] min-w-0 truncate"
                        title={item.label}
                      >
                        {item.syntax}
                      </code>

                      {isRecent && (
                        <span style={{ fontSize: 9, color: "#d4513b", fontWeight: 400, flexShrink: 0 }}>上次</span>
                      )}

                      {/* Spacer */}
                      <div style={{ flex: 1 }} />

                      {/* Top operation buttons */}
                      <div style={{ display: "flex", gap: 3, flexShrink: 0 }}>
                        {topOps.map((op) => (
                          <button
                            key={op.key}
                            onClick={(e) => { e.stopPropagation(); handlePick(bare, op.key); }}
                            title={op.hint}
                            style={{
                              fontSize: 10,
                              fontWeight: 500,
                              padding: "1px 7px",
                              borderRadius: 5,
                              border: "none",
                              background: "transparent",
                              color: "#9ca3af",
                              cursor: "pointer",
                              whiteSpace: "nowrap",
                              outline: "none",
                              transition: "all 0.12s",
                            }}
                            onMouseEnter={(e) => { e.currentTarget.style.background = "#eef2ff"; e.currentTarget.style.color = "#6366f1"; }}
                            onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#9ca3af"; }}
                          >
                            {op.label}
                          </button>
                        ))}

                        {/* More ops toggle */}
                        {moreOps.length > 0 && (
                          <button
                            onClick={(e) => { e.stopPropagation(); toggleExpand(item.syntax); }}
                            title="更多操作"
                            style={{
                              fontSize: 10,
                              fontWeight: 500,
                              padding: "1px 6px",
                              borderRadius: 5,
                              border: "none",
                              background: isExpanded ? "#eef2ff" : "transparent",
                              color: isExpanded ? "#6366f1" : "#c4bbb2",
                              cursor: "pointer",
                              outline: "none",
                              transition: "all 0.12s",
                            }}
                            onMouseEnter={(e) => { if (!isExpanded) { e.currentTarget.style.background = "#f5f4f0"; e.currentTarget.style.color = "#8b8fa3"; } }}
                            onMouseLeave={(e) => { if (!isExpanded) { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#c4bbb2"; } }}
                          >
                            ···
                          </button>
                        )}
                      </div>

                      {/* Expanded more ops row */}
                      {isExpanded && (
                        <div className="mt-1 pt-1 border-t border-solid border-[#f0ede8] w-full">
                          <div className="flex gap-[3px]">
                            {moreOps.map((op) => (
                              <button
                                key={op.key}
                                onClick={(e) => { e.stopPropagation(); handlePick(bare, op.key); }}
                                title={op.hint}
                                style={{
                                  fontSize: 10,
                                  fontWeight: 500,
                                  padding: "1px 7px",
                                  borderRadius: 5,
                                  border: "none",
                                  background: "transparent",
                                  color: "#9ca3af",
                                  cursor: "pointer",
                                  whiteSpace: "nowrap",
                                  outline: "none",
                                  transition: "all 0.12s",
                                }}
                                onMouseEnter={(e) => { e.currentTarget.style.background = "#eef2ff"; e.currentTarget.style.color = "#6366f1"; }}
                                onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; e.currentTarget.style.color = "#9ca3af"; }}
                              >
                                {op.label}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
        {filtered.length === 0 && (
          <div className="text-center p-6 text-xs c-[#c4bbb2]">
            无匹配变量
          </div>
        )}
      </div>
    </div>
  );

  return (
    <Popover
      trigger="click"
      placement="bottomLeft"
      content={content}
      overlayStyle={{ maxWidth: 380 }}
    >
      {children ?? (
        <span className="inline-flex items-center justify-center w-5 h-5 rounded text-[#9ca3af] hover:text-[#d4513b] hover:bg-[#fef3ef] transition-colors cursor-pointer select-none text-[11px] font-semibold">
          fx
        </span>
      )}
    </Popover>
  );
};

export { ALL_OPS };
export type { VarItem, VarOp };
export default VariablePicker;
