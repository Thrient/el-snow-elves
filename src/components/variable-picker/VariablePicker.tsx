import { useState, useMemo, type FC } from "react";
import { Input, Popover } from "antd";
import { SearchOutlined } from "@ant-design/icons";

type VarOp = "get" | "inc" | "dec" | "default" | "sub" | "len";

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
];

interface VarItem {
  syntax: string;
  label: string;
  category: "config" | "task" | "system" | "step";
}

interface Props {
  variables: VarItem[];
  onInsert: (expr: string) => void;
  children: React.ReactNode;
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
  set:    ["inc", "dec", "get", "default", "len", "sub"],
  when:   ["len", "get", "sub", "inc", "dec", "default"],
  args:   ["get", "default", "len", "sub", "inc", "dec"],
  params: ["get", "default", "sub", "len", "inc", "dec"],
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
    <div style={{ width: 340, maxHeight: 420, display: "flex", flexDirection: "column" }}>
      {/* Search */}
      <div style={{ padding: "0 0 10px", flexShrink: 0 }}>
        <Input
          size="small"
          prefix={<SearchOutlined style={{ color: "#b8afa6" }} />}
          placeholder={placeholder ?? "搜索变量…"}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          allowClear
          style={{ borderRadius: 10 }}
        />
      </div>

      {/* Variable list */}
      <div style={{ flex: 1, overflowY: "auto" }}>
        {Array.from(grouped.entries()).map(([cat, items]) => {
          const dot = CAT_COLORS[cat] ?? "#9ca3af";
          return (
            <div key={cat} style={{ marginBottom: 12 }}>
              <div style={{
                fontSize: 10,
                fontWeight: 600,
                color: "#9ca3af",
                letterSpacing: "0.04em",
                marginBottom: 6,
                padding: "0 4px",
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}>
                <span style={{ width: 6, height: 6, borderRadius: "50%", background: dot, flexShrink: 0 }} />
                {CAT_LABELS[cat] ?? cat}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                {items.map((item) => {
                  const bare = item.syntax.replace(/^\{|\}$/g, "");
                  const isRecent = recentVar === bare;
                  const isExpanded = expandedRows.has(item.syntax);

                  return (
                    <div
                      key={item.syntax}
                      onDoubleClick={() => handlePick(bare, orderedOps[0].key)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 6,
                        padding: "5px 8px",
                        borderRadius: 10,
                        background: isRecent ? "#fef3ef" : "transparent",
                        cursor: "default",
                        transition: "background 0.15s",
                      }}
                      onMouseEnter={(e) => { if (!isRecent) e.currentTarget.style.background = "#f5f4f0"; }}
                      onMouseLeave={(e) => { if (!isRecent) e.currentTarget.style.background = "transparent"; }}
                    >
                      {/* Variable name */}
                      <code
                        style={{
                          fontSize: 12,
                          fontWeight: 600,
                          color: "#3d3630",
                          minWidth: 0,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
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
                        <div style={{
                          marginTop: 4,
                          paddingTop: 4,
                          borderTop: "1px solid #f0ede8",
                          width: "100%",
                        }}>
                          <div style={{ display: "flex", gap: 3 }}>
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
          <div style={{ textAlign: "center", padding: 24, fontSize: 12, color: "#c4bbb2" }}>
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
      {children}
    </Popover>
  );
};

export { ALL_OPS };
export type { VarItem, VarOp };
export default VariablePicker;
