import { useState, useMemo, useEffect, type FC } from "react";
import { AutoComplete, Input, Popover } from "antd";
import { SearchOutlined } from "@ant-design/icons";

// ── Types ──

interface VarItem {
  syntax: string;
  label: string;
  category: "config" | "task" | "system" | "step";
}

interface OpDef {
  key: string;
  title: string;
  desc: string;
  expr: string;
  arg?: { label: string; type: "number" | "text" };
}

type Context = "when" | "set" | "args" | "params";

interface Props {
  variables: VarItem[];
  onInsert: (expr: string) => void;
  children?: React.ReactNode;
  placeholder?: string;
  context?: Context;
  value?: string;
  modes?: string[];
  inline?: boolean;
  /** 变量显式类型 — 优先于名称推断 */
  valueTypes?: Record<string, import("@/types/task").VarType>;
}

// ── Type helpers ──

const TYPE_LABELS: Record<string, string> = { list: "列表", number: "数字", string: "字符串", boolean: "布尔" };
const TYPE_COLORS: Record<string, string> = { list: "#c62828", number: "#1565c0", string: "#6a1b9a", boolean: "#2e7d32" };
const TYPE_BG: Record<string, string> = { list: "#fce4ec", number: "#e3f2fd", string: "#f3e5f5", boolean: "#e8f5e9" };

function extractBareName(syntax: string): string {
  return syntax.replace(/^\{|\}$/g, "").replace(/[+\-*/!><=?.\[\]() ]/g, "").trim();
}

function detectType(v: VarItem, valueTypes?: Record<string, import("@/types/task").VarType>): string {
  const bare = extractBareName(v.syntax);
  // 1. 显式类型（最高优先）
  if (valueTypes && bare in valueTypes) {
    const vt = valueTypes[bare];
    if (vt === "list") return "list";
    if (vt === "number") return "number";
    if (vt === "switch") return "boolean";
    return "string";
  }
  // 2. 系统变量 — 名称推断
  if (v.category === "system") {
    if (/index|i$/i.test(bare)) return "number";
    if (/len|count|size|result/i.test(bare)) return "number";
  }
  // 3. 默认文本
  return "string";
}

// ── Operations per type ──

const OPS_BY_TYPE: Record<string, OpDef[]> = {
  list: [
    { key: "value",  title: "取值",       desc: "直接取列表引用",                           expr: "{var}" },
    { key: "loop",   title: "循环取值",   desc: "遍历每一项，自动注入 index/len/reset",      expr: "{var[循环]}" },
    { key: "index",  title: "取下标 [n]", desc: "按位置取第 n 项，从 0 开始，支持 {变量}",    expr: "{var[?]}",   arg: { label: "下标", type: "text" } },
    { key: "choice", title: "随机选择",   desc: "随机取列表中一项 choice(var)",              expr: "{choice(var)}" },
    { key: "len",    title: "求长度",     desc: "返回元素个数 len(var)",                      expr: "{len(var)}" },
    { key: "first",  title: "取第一个",   desc: "等价于 [0]",                                expr: "{var[0]}" },
    { key: "last",   title: "取最后一个", desc: "取列表末尾项",                              expr: "{var[last]}" },
  ],
  number: [
    { key: "value",  title: "取值",       desc: "直接取数字值",                             expr: "{var}" },
    { key: "inc",    title: "自增 ++",    desc: "每次执行 +1",                               expr: "{var++}" },
    { key: "dec",    title: "自减 --",    desc: "每次执行 -1",                               expr: "{var--}" },
    { key: "add",    title: "加法 +n",    desc: "加上一个数值",                             expr: "{var+?}",   arg: { label: "数值", type: "number" } },
    { key: "sub",    title: "减法 -n",    desc: "减去一个数值",                             expr: "{var-?}",   arg: { label: "数值", type: "number" } },
    { key: "eq",     title: "等于 ==",    desc: "判断是否等于某值",                         expr: "{var==?}",  arg: { label: "值", type: "number" } },
    { key: "neq",    title: "不等于 !=",  desc: "判断是否不等于某值",                       expr: "{var!=?}",  arg: { label: "值", type: "number" } },
    { key: "compare",title: "条件比较",   desc: ">, <, >=, <=, ==, !=",                     expr: "{var>?}",   arg: { label: "比较值", type: "number" } },
  ],
  string: [
    { key: "value",  title: "取值",       desc: "直接取字符串值",                           expr: "{var}" },
    { key: "eq",     title: "等于 ==",    desc: "判断是否等于某文本",                       expr: "{var==?}",  arg: { label: "文本", type: "text" } },
    { key: "neq",    title: "不等于 !=",  desc: "判断是否不等于某文本",                     expr: "{var!=?}",  arg: { label: "文本", type: "text" } },
    { key: "concat", title: "拼接 +",     desc: "连接字符串",                               expr: "{var+?}",   arg: { label: "文本", type: "text" } },
    { key: "len",    title: "求长度",     desc: "返回字符数 len(var)",                       expr: "{len(var)}" },
    { key: "contains",title:"判断包含",   desc: "检查是否包含指定文本",                      expr: "{var⊃?}",  arg: { label: "关键词", type: "text" } },
    { key: "slice",  title: "截取子串",   desc: "截取 [start, end)",                        expr: "{var[?:?]}",arg: { label: "范围", type: "text" } },
  ],
  boolean: [
    { key: "value",  title: "取值",       desc: "直接取布尔值",                             expr: "{var}" },
    { key: "not",    title: "取反 !",     desc: "true ↔ false 翻转",                        expr: "{!var}" },
    { key: "eq",     title: "相等判断",   desc: "比较是否等于",                             expr: "{var==?}",  arg: { label: "值", type: "text" } },
    { key: "neq",    title: "不等判断",   desc: "比较是否不等于",                           expr: "{var!=?}",  arg: { label: "值", type: "text" } },
  ],
};

// ── Builder steps ──
type BuildStep = "var" | "op" | "arg" | "confirm";

const STEP_LABELS: Record<BuildStep, string> = {
  var: "选变量", op: "定操作", arg: "填参数", confirm: "确认",
};

const VarOpBuilder: FC<Props> = ({ variables, onInsert, children, placeholder, context, value, modes, inline, valueTypes }) => {
  const isWhen = context === "when";
  const showTrue = isWhen && (!modes || modes.includes("true"));

  // ── State ──
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState<BuildStep>("var");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [selectedVar, setSelectedVar] = useState<VarItem | null>(null);
  const [selectedOp, setSelectedOp] = useState<OpDef | null>(null);
  const [opArg, setOpArg] = useState("");
  const [compound, setCompound] = useState<{ expr: string; connector: string | null }[]>([]);
  const [submitted, setSubmitted] = useState(false);

  // Sub-expression builder for arg values
  const [argMode, setArgMode] = useState<"input" | "var" | "op">("input");
  const [argVar, setArgVar] = useState<VarItem | null>(null);
  const [argOp, setArgOp] = useState<OpDef | null>(null);
  const [argSubArg, setArgSubArg] = useState("");

  // Parse initial value
  useEffect(() => {
    if (!value || !open) return;
    if (value === "{True}") {
      setStep("confirm");
      setSelectedVar({ syntax: "True", label: "直接通过", category: "system" });
      setSelectedOp({ key: "true", title: "直接通过", desc: "", expr: "{True}" });
      return;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Reset on open
  useEffect(() => {
    if (open) {
      setStep("var");
      setSearch("");
      setTypeFilter("all");
      setSelectedVar(null);
      setSelectedOp(null);
      setOpArg("");
      setCompound([]);
      setArgMode("input");
      setArgVar(null);
      setArgOp(null);
      setArgSubArg("");
      setSubmitted(false);
    }
  }, [open]);


  // ── Computed ──
  const filteredVars = useMemo(() => {
    let list = variables;
    if (typeFilter !== "all") {
      list = list.filter(v => detectType(v, valueTypes) === typeFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(v =>
        v.syntax.toLowerCase().includes(q) || v.label.toLowerCase().includes(q),
      );
    }
    return list;
  }, [variables, typeFilter, search]);

  const ops = useMemo(() => {
    if (!selectedVar) return [];
    if (selectedVar.syntax === "True") return [];
    const type = detectType(selectedVar, valueTypes);
    return OPS_BY_TYPE[type] || OPS_BY_TYPE.string;
  }, [selectedVar]);

  const needsArgStep = selectedOp?.arg != null;

  const stepDefs = useMemo(() => {
    const defs: BuildStep[] = ["var", "op"];
    if (selectedOp && needsArgStep) defs.push("arg");
    defs.push("confirm");
    return defs;
  }, [selectedOp, needsArgStep]);

  const stepIndex = stepDefs.indexOf(step);

  const canProceed = (): boolean => {
    if (step === "var") return showTrue ? true : !!selectedVar;
    if (step === "op") return !!selectedOp;
    if (step === "arg") return opArg.trim() !== "";
    return true;
  };

  // ── Expression building ──
  const buildSingle = (): string => {
    if (selectedVar?.syntax === "True") return "{True}";
    if (!selectedVar || !selectedOp) return "{…}";
    const bare = selectedVar.syntax.replace(/^\{|\}$/g, "");
    let expr = selectedOp.expr.replace("var", bare);
    if (selectedOp.arg && opArg) {
      const arg = opArg.replace(/^\{|\}$/g, "");
      const isNumber = /^-?\d+$/.test(arg);
      const isVarName = variables.some(v => v.syntax.replace(/^\{|\}$/g, "") === arg);
      const val = (selectedOp.arg.type === "text" && !isNumber && !isVarName) ? `'${arg}'` : arg;
      expr = expr.replace("?", val);
    }
    return expr.replace(/\?/g, "…");
  };

  const buildCompound = (): string => {
    const current = buildSingle();
    if (!isWhen || compound.length === 0) return current;
    return compound.map(c => c.expr + (c.connector ? " " + c.connector + " " : "")).join("") + current;
  };

  // ── Navigation ──
  const goNext = () => {
    if (!canProceed()) return;
    const idx = stepDefs.indexOf(step);
    if (idx < stepDefs.length - 1) {
      setStep(stepDefs[idx + 1]);
    }
  };

  const goBack = () => {
    const idx = stepDefs.indexOf(step);
    if (idx > 0) {
      const prev = stepDefs[idx - 1];
      if (prev === "var") { setSelectedOp(null); setOpArg(""); }
      setStep(prev);
    }
  };

  const commitAndContinue = (connector: "&&" | "||") => {
    setCompound(prev => [...prev, { expr: buildSingle(), connector }]);
    setStep("var");
    setSelectedVar(null);
    setSelectedOp(null);
    setOpArg("");
    setSearch("");
    setTypeFilter("all");
  };

  const finish = () => {
    const expr = buildCompound();
    onInsert(expr);
    setSubmitted(true);
    setOpen(false);
  };

  const selectVar = (v: VarItem) => {
    setSelectedVar(v);
    setSelectedOp(null);
    setOpArg("");
    setStep("op");
  };

  const selectOp = (op: OpDef) => {
    setSelectedOp(op);
    setOpArg("");
    if (op.arg) {
      setStep("arg");
    } else {
      setStep("confirm");
    }
  };

  // ── Render helpers ──
  const stripBraces = (s: string) => s.replace(/^\{|\}$/g, "");

  // ── Popover content ──
  const content = (
    <div style={{ width: 320, maxHeight: 440, display: "flex", flexDirection: "column" }}>
      {/* ── Step indicators ── */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "center", gap: 0, padding: "0 0 14px",
        fontSize: 11, color: "#b8afa6", flexShrink: 0,
      }}>
        {stepDefs.map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: 0 }}>
            {i > 0 && (
              <div style={{
                width: 28, height: 1, margin: "0 2px",
                background: i <= stepIndex ? "#a5d6a7" : "#e8e3dc",
                transition: "background 0.2s",
              }} />
            )}
            <div style={{
              display: "flex", alignItems: "center", gap: 3,
              cursor: i < stepIndex && !submitted ? "pointer" : "default",
              opacity: i > stepIndex ? 0.4 : 1,
            }}
            onClick={() => { if (i < stepIndex && !submitted) { setStep(s); if (s === "var") { setSelectedOp(null); setOpArg(""); } } }}
            >
              <div style={{
                width: 22, height: 22, borderRadius: "50%",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 11, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                background: i < stepIndex ? "#e8f5e9" : i === stepIndex ? "#d4513b" : "#f5f0ea",
                color: i < stepIndex ? "#2e7d32" : i === stepIndex ? "#fff" : "#b8afa6",
                border: i < stepIndex ? "2px solid #a5d6a7" : i === stepIndex ? "2px solid #d4513b" : "2px solid #e8e3dc",
                borderStyle: s === "arg" && i === stepIndex ? "dashed" : "solid",
                transition: "all 0.2s",
              }}>{i + 1}</div>
              <span style={{
                fontWeight: i === stepIndex ? 600 : 400,
                color: i < stepIndex ? "#2e7d32" : i === stepIndex ? "#d4513b" : "#b8afa6",
              }}>{STEP_LABELS[s]}</span>
            </div>
          </div>
        ))}
      </div>

      {/* ── Step content ── */}
      <div style={{ flex: 1 }} key={step}>
        {/* Step: Pick Variable */}
        {step === "var" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {showTrue && (
              <button
                onClick={() => {
                  setSelectedVar({ syntax: "True", label: "直接通过", category: "system" });
                  setSelectedOp({ key: "true", title: "直接通过", desc: "", expr: "{True}" });
                  setStep("confirm");
                }}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  padding: "8px 12px", borderRadius: 10,
                  border: "1.5px solid #10b98133", background: "#ecfdf5",
                  cursor: "pointer", width: "100%", textAlign: "left",
                  transition: "all 0.15s",
                }}
                onMouseEnter={e => { e.currentTarget.style.background = "#d1fae5"; }}
                onMouseLeave={e => { e.currentTarget.style.background = "#ecfdf5"; }}
              >
                <span style={{ fontSize: 18 }}>⚡</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 600, color: "#065f46" }}>直接通过</div>
                  <div style={{ fontSize: 10, color: "#6b7280" }}>无条件，始终判定为成功</div>
                </div>
                <code style={{ fontSize: 11, fontWeight: 600, color: "#10b981", background: "#d1fae5", padding: "2px 8px", borderRadius: 5 }}>{"{True}"}</code>
              </button>
            )}

            <Input
              size="small"
              prefix={<SearchOutlined style={{ color: "#b8afa6" }} />}
              placeholder={placeholder ?? "搜索变量…"}
              value={search}
              onChange={e => setSearch(e.target.value)}
              allowClear
              style={{ borderRadius: 10 }}
            />

            <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
              {["all", "list", "number", "string", "boolean"].map(k => (
                <button
                  key={k}
                  onClick={() => setTypeFilter(k)}
                  style={{
                    padding: "3px 11px", borderRadius: 20,
                    fontSize: 10, fontWeight: 600,
                    border: typeFilter === k ? "1.5px solid #d4513b" : "1.5px solid #e8e3dc",
                    background: typeFilter === k ? "#d4513b" : "#fff",
                    color: typeFilter === k ? "#fff" : "#8b857e",
                    cursor: "pointer", outline: "none",
                    transition: "all 0.15s",
                  }}
                >{k === "all" ? "全部" : TYPE_LABELS[k]}</button>
              ))}
            </div>

            <div style={{
              maxHeight: 200, overflowY: "auto",
              border: "1px solid #e8e3dc", borderRadius: 10,
              background: "#faf8f5",
            }}>
              {filteredVars.length === 0 ? (
                <div style={{ textAlign: "center", padding: 24, fontSize: 12, color: "#b8afa6" }}>无匹配变量</div>
              ) : (
                filteredVars.map(v => {
                  const type = detectType(v, valueTypes);
                  const bare = stripBraces(v.syntax);
                  return (
                    <div
                      key={v.syntax}
                      onClick={() => selectVar(v)}
                      style={{
                        display: "flex", alignItems: "center", gap: 8,
                        padding: "8px 12px",
                        cursor: "pointer",
                        borderBottom: "1px solid #f0ece6",
                        background: "#fff",
                        transition: "background 0.12s",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = "#fefcfa"; }}
                      onMouseLeave={e => { e.currentTarget.style.background = "#fff"; }}
                    >
                      <span style={{ fontSize: 16, flexShrink: 0 }}>{type === "list" ? "📋" : type === "number" ? "🔢" : type === "boolean" ? "🔘" : "📝"}</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "#3d3630", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{bare}</div>
                        {v.label && v.label !== bare && (
                          <div style={{ fontSize: 10, color: "#b8afa6", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.label}</div>
                        )}
                      </div>
                      <span style={{
                        fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 20,
                        background: TYPE_BG[type] || "#f3f4f6", color: TYPE_COLORS[type] || "#6b7280",
                        flexShrink: 0,
                      }}>{TYPE_LABELS[type] || "未知"}</span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* Step: Pick Operation */}
        {step === "op" && selectedVar && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10, overflow: "hidden" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, overflowY: "auto", alignContent: "start" }}>
              {ops.map(op => {
                const bare = stripBraces(selectedVar.syntax);
                const preview = op.expr.replace("var", bare).replace(/\?/g, "…");
                return (
                  <div
                    key={op.key}
                    onClick={() => selectOp(op)}
                    style={{
                      padding: "6px 10px",
                      borderRadius: 8,
                      border: "1.5px solid #e8e3dc",
                      background: "#fff",
                      cursor: "pointer",
                      transition: "all 0.15s",
                    }}
                    onMouseEnter={e => {
                      e.currentTarget.style.borderColor = "#cbbdb0";
                      e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.04)";
                    }}
                    onMouseLeave={e => {
                      e.currentTarget.style.borderColor = "#e8e3dc";
                      e.currentTarget.style.boxShadow = "none";
                    }}
                  >
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#3d3630", lineHeight: 1.2 }}>{op.title}</div>
                    <div style={{ fontSize: 10, color: "#8b857e", marginTop: 1, lineHeight: 1.2 }}>{op.desc}</div>
                    <code style={{
                      display: "inline-block", marginTop: 3,
                      fontSize: 10, fontWeight: 500,
                      color: "#d4513b", background: "rgba(212,81,59,0.05)",
                      padding: "0 6px", borderRadius: 4,
                    }}>{preview}</code>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Step: Fill Argument */}
        {step === "arg" && selectedVar && selectedOp && (
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 14,
            padding: "20px 0",
          }}>
            <div
              onClick={() => setStep("op")}
              style={{
                display: "inline-flex", alignItems: "center", gap: 5, alignSelf: "center",
                padding: "4px 12px", fontSize: 11, fontWeight: 500,
                background: "rgba(212,81,59,0.06)", border: "1px solid rgba(212,81,59,0.15)",
                borderRadius: 20, cursor: "pointer",
              }}
            >
              <span style={{ color: "#d4513b", fontWeight: 600 }}>{stripBraces(selectedVar.syntax)}</span>
              <span style={{ color: "#8b857e" }}>· {selectedOp.title}</span>
              <span style={{ color: "#b8afa6", fontSize: 10 }}>↩</span>
            </div>

            {argMode === "input" ? (
              <>
                <div style={{
                  background: "#fff", border: "2px solid #d4513b",
                  borderRadius: 14, padding: "24px 28px",
                  display: "flex", flexDirection: "column",
                  alignItems: "center", gap: 12,
                  boxShadow: "0 0 0 3px rgba(212,81,59,0.08)",
                }}>
                  <label style={{ fontSize: 13, fontWeight: 600, color: "#3d3630" }}>
                    输入{selectedOp.arg!.label}
                  </label>
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    <AutoComplete
                      value={opArg}
                      onChange={v => setOpArg(v)}
                      options={variables.map(v => ({ value: v.syntax, label: v.syntax.replace(/^\{|\}$/g, "") }))}
                      filterOption={(input, option) =>
                        option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
                      }
                      style={{ width: 160 }}
                      placeholder="数字或 {变量}"
                    />
                    <button
                      onClick={() => { setArgMode("var"); setArgVar(null); setArgOp(null); setArgSubArg(""); }}
                      style={{
                        width: 32, height: 32,
                        borderRadius: 8, border: "1.5px solid #d0d5dd",
                        background: "#faf8f5", cursor: "pointer",
                        fontSize: 14, fontWeight: 700, color: "#6366f1",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        transition: "all 0.15s",
                      }}
                      title="构建表达式"
                    >fx</button>
                  </div>
                </div>
                <div style={{ fontSize: 11, color: "#b8afa6" }}>Enter 确认 · fx 构建表达式</div>
              </>
            ) : argMode === "var" ? (
              <div style={{
                background: "#fff", border: "2px solid #6366f1",
                borderRadius: 14, padding: "16px 20px",
                display: "flex", flexDirection: "column", gap: 6,
                boxShadow: "0 0 0 3px rgba(99,102,241,0.08)",
                maxHeight: 220, overflowY: "auto",
              }} className="thin-scrollbar">
                <div style={{ fontSize: 11, fontWeight: 600, color: "#6366f1", marginBottom: 2 }}>
                  选择变量
                  <button onClick={() => setArgMode("input")}
                    style={{ marginLeft: 8, fontSize: 10, color: "#b8afa6", border: "none", background: "none", cursor: "pointer" }}>← 返回</button>
                </div>
                {variables.map(v => {
                  const type = detectType(v, valueTypes);
                  const bare = stripBraces(v.syntax);
                  return (
                    <div key={v.syntax} onClick={() => { setArgVar(v); setArgMode("op"); }}
                      style={{
                        display: "flex", alignItems: "center", gap: 6,
                        padding: "6px 10px", borderRadius: 8, cursor: "pointer",
                        background: "#faf8f5", transition: "background 0.12s",
                      }}
                      onMouseEnter={e => { e.currentTarget.style.background = "#eef2ff"; }}
                      onMouseLeave={e => { e.currentTarget.style.background = "#faf8f5"; }}
                    >
                      <span style={{ fontSize: 12 }}>{type==="list"?"📋":type==="number"?"🔢":"📝"}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: "#3d3630" }}>{bare}</span>
                      <span style={{ fontSize: 9, color: "#b8afa6" }}>{TYPE_LABELS[type]}</span>
                    </div>
                  );
                })}
              </div>
            ) : argMode === "op" && argVar ? (
              <div style={{
                background: "#fff", border: "2px solid #6366f1",
                borderRadius: 14, padding: "16px 20px",
                display: "flex", flexDirection: "column", gap: 6,
                boxShadow: "0 0 0 3px rgba(99,102,241,0.08)",
                maxHeight: 220, overflowY: "auto",
              }} className="thin-scrollbar">
                <div style={{ fontSize: 11, fontWeight: 600, color: "#6366f1", marginBottom: 2 }}>
                  {stripBraces(argVar.syntax)} · 选择操作
                  <button onClick={() => setArgMode("var")}
                    style={{ marginLeft: 8, fontSize: 10, color: "#b8afa6", border: "none", background: "none", cursor: "pointer" }}>← 返回</button>
                </div>
                {(() => {
                  const vtype = detectType(argVar, valueTypes);
                  const ops = OPS_BY_TYPE[vtype] ?? [];
                  return ops.map(op => {
                    const preview = op.expr.replace("var", stripBraces(argVar.syntax)).replace(/\?/g, "…");
                    return (
                      <div key={op.key}
                        onClick={() => {
                          if (op.arg) {
                            setArgOp(op);
                            // 直接构建，无子参数的跳过二次确认
                          } else {
                            const inner = op.expr.replace("var", stripBraces(argVar.syntax));
                            setOpArg(inner);
                            setArgMode("input");
                          }
                        }}
                        style={{
                          display: "flex", alignItems: "center", justifyContent: "space-between",
                          padding: "6px 10px", borderRadius: 8, cursor: "pointer",
                          background: argOp?.key === op.key ? "#eef2ff" : "#faf8f5",
                          transition: "background 0.12s",
                        }}
                        onMouseEnter={e => { e.currentTarget.style.background = "#eef2ff"; }}
                        onMouseLeave={e => { e.currentTarget.style.background = argOp?.key === op.key ? "#eef2ff" : "#faf8f5"; }}
                      >
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: "#3d3630" }}>{op.title}</div>
                          <div style={{ fontSize: 10, color: "#b8afa6" }}>{op.desc}</div>
                        </div>
                        <code style={{ fontSize: 10, color: "#6366f1", background: "#eef2ff", padding: "2px 6px", borderRadius: 4 }}>{preview}</code>
                      </div>
                    );
                  });
                })()}
                {/* Sub-arg input for ops that need it */}
                {argOp?.arg && (
                  <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 4 }}>
                    <AutoComplete
                      value={argSubArg}
                      onChange={v => setArgSubArg(v)}
                      options={variables.map(v => ({ value: v.syntax, label: v.syntax.replace(/^\{|\}$/g, "") }))}
                      filterOption={(input, option) =>
                        option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false
                      }
                      style={{ flex: 1 }}
                      placeholder={argOp.arg.label}
                    />
                    <button
                      onClick={() => {
                        const bare = stripBraces(argVar.syntax);
                        let expr = argOp.expr.replace("var", bare);
                        if (argSubArg) {
                          const sub = argSubArg.replace(/^\{|\}$/g, "");
                          const isNum = /^-?\d+$/.test(sub);
                          const isVarName = variables.some(v => stripBraces(v.syntax) === sub);
                          const v = (!isNum && !isVarName) ? `'${sub}'` : sub;
                          expr = expr.replace("?", v);
                        }
                        setOpArg(expr);
                        setArgMode("input");
                      }}
                      style={{
                        padding: "4px 10px", borderRadius: 8,
                        border: "none", background: "#6366f1", color: "#fff",
                        fontWeight: 600, fontSize: 11, cursor: "pointer",
                      }}
                    >确定</button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}

        {/* Step: Confirm */}
        {step === "confirm" && (
          <div style={{
            display: "flex", flexDirection: "column", alignItems: "center", gap: 12,
            padding: "12px 0",
          }}>
            {isWhen && compound.length > 0 && (
              <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 6, justifyContent: "center", marginBottom: 4 }}>
                {compound.map((c, i) => (
                  <span key={i} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <code style={{
                      fontSize: 11, fontWeight: 500,
                      padding: "3px 8px", borderRadius: 6,
                      background: "rgba(212,81,59,0.05)", color: "#8b857e",
                    }}>{c.expr}</code>
                    {c.connector && (
                      <span style={{
                        fontSize: 10, fontWeight: 700,
                        padding: "1px 6px", borderRadius: 10,
                        background: c.connector === "&&" ? "#e8f5e9" : "#fff3e0",
                        color: c.connector === "&&" ? "#2e7d32" : "#e65100",
                      }}>{c.connector === "&&" ? "且" : "或"}</span>
                    )}
                  </span>
                ))}
                <button
                  onClick={() => { setCompound([]); setStep("var"); setSelectedVar(null); setSelectedOp(null); }}
                  style={{
                    border: "none", background: "transparent", cursor: "pointer",
                    color: "#b8afa6", fontSize: 14, padding: "2px 4px",
                  }}
                  title="清除条件链"
                >✕</button>
              </div>
            )}
            <code style={{
              padding: "14px 24px",
              background: "linear-gradient(135deg, #2b2520, #3d3630)",
              borderRadius: 14, color: "#f0c060",
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 16, fontWeight: 500,
              boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
            }}>
              {buildCompound()}
            </code>

            <div style={{ fontSize: 11, color: "#8b857e" }}>
              {buildSingle()}
            </div>

            {isWhen && !submitted && (
              <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                <button
                  onClick={() => commitAndContinue("&&")}
                  style={{
                    display: "flex", alignItems: "center", gap: 4,
                    padding: "6px 14px", borderRadius: 8,
                    border: "1.5px solid #a5d6a7",
                    background: "#fff", color: "#2e7d32",
                    fontSize: 12, fontWeight: 600,
                    cursor: "pointer", outline: "none",
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#e8f5e9"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#fff"; }}
                >+ 且 (&&)</button>
                <button
                  onClick={() => commitAndContinue("||")}
                  style={{
                    display: "flex", alignItems: "center", gap: 4,
                    padding: "6px 14px", borderRadius: 8,
                    border: "1.5px solid #ffcc80",
                    background: "#fff", color: "#e65100",
                    fontSize: 12, fontWeight: 600,
                    cursor: "pointer", outline: "none",
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = "#fff3e0"; }}
                  onMouseLeave={e => { e.currentTarget.style.background = "#fff"; }}
                >+ 或 (||)</button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        paddingTop: 14, borderTop: "1px solid #f0ece6", marginTop: 10, flexShrink: 0,
      }}>
        <button
          onClick={step === "var" ? () => setOpen(false) : goBack}
          style={{
            padding: "6px 14px", borderRadius: 8,
            border: "none", background: "transparent",
            color: "#8b857e", fontSize: 12, fontWeight: 500,
            cursor: "pointer", outline: "none",
          }}
        >{step === "var" ? "取消" : "← 上一步"}</button>

        <div style={{ flex: 1 }} />

        <button
          onClick={step === "confirm" ? finish : goNext}
          disabled={!canProceed()}
          style={{
            padding: "7px 20px", borderRadius: 8,
            border: "none",
            background: canProceed() ? "#d4513b" : "#e8e3dc",
            color: canProceed() ? "#fff" : "#b8afa6",
            fontSize: 12, fontWeight: 600,
            cursor: canProceed() ? "pointer" : "not-allowed",
            outline: "none",
            boxShadow: canProceed() ? "0 2px 8px rgba(212,81,59,0.3)" : "none",
            transition: "all 0.15s",
          }}
        >{step === "confirm" ? "✓ 填入" : "下一步 →"}</button>
      </div>
    </div>
  );

  if (inline) {
    return <div style={{ width: "100%" }}>{content}</div>;
  }

  return (
    <Popover
      trigger="click"
      placement="bottomLeft"
      open={open}
      onOpenChange={setOpen}
      content={content}
      overlayStyle={{ maxWidth: 380 }}
      destroyTooltipOnHide
    >
      {children ?? (
        <span className="inline-flex items-center justify-center w-5 h-5 rounded text-[#9ca3af] hover:text-[#d4513b] hover:bg-[#fef3ef] transition-colors cursor-pointer select-none text-[11px] font-semibold">
          fx
        </span>
      )}
    </Popover>
  );
};

export default VarOpBuilder;
export type { VarItem };
