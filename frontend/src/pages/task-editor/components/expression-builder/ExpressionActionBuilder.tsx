import { useState, useEffect, useCallback, useRef, useMemo, type FC } from "react";
import { Select, Input, Button } from "antd";
import { ThunderboltOutlined, BranchesOutlined, FilterOutlined } from "@ant-design/icons";
import { buildExpr, parseExpr, defaultCond, COMPARE_OPS, type Cond } from "@/utils/expression";
import VariablePicker from "@/pages/task-editor/components/variable-picker/VariablePicker";

type Mode = "true" | "var" | "compare";

interface Props {
  value: string;
  varOptions: { value: string; label: string }[];
  onChange: (expr: string) => void;
  modes?: Mode[];
  values?: Record<string, unknown>;
  valueTypes?: Record<string, import("@/types/task").VarType>;
  layout?: { model?: string; store?: string }[][];
}

const MODES: { key: Mode; icon: React.ReactNode; label: string; hint: string }[] = [
  { key: "true", icon: <ThunderboltOutlined />, label: "直接通过", hint: "始终成功" },
  { key: "var", icon: <BranchesOutlined />, label: "变量判断", hint: "变量为真即通过" },
  { key: "compare", icon: <FilterOutlined />, label: "条件比较", hint: "多条件组合" },
];

// Cell model → runtime type mapping for union with values-based detection
const MODEL_LIST_TYPES = new Set(["el-input-tags", "el-checkbox-group"]);
const MODEL_NUM_TYPES = new Set(["el-input-number", "el-slider"]);
const MODEL_BOOL_TYPES = new Set(["el-switch", "el-checkbox"]);

const ExpressionActionBuilder: FC<Props> = ({ value, varOptions, onChange, modes, values, valueTypes, layout }) => {
  const allowedModes = modes ?? ["true", "var", "compare"];
  const [mode, setMode] = useState<Mode>(allowedModes.includes("compare") ? "compare" : allowedModes[0]);
  const [varName, setVarName] = useState("");
  const [conds, setConds] = useState<Cond[]>([defaultCond()]);
  const [previewKey, setPreviewKey] = useState(0);
  const [opSpin, setOpSpin] = useState<Record<number, { old: string; cur: string; dir: "up" | "down" }>>({});
  const condsRef = useRef(conds);
  condsRef.current = conds;
  const condRefs = useRef<(HTMLDivElement | null)[]>([]);
  const opBtnRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Build type map: valueTypes > layout cell models > runtime values
  const varTypeMap = useMemo(() => {
    const m: Record<string, string | undefined> = {};
    // 1. From explicit valueTypes (highest priority — user-specified)
    if (valueTypes) {
      for (const [k, vt] of Object.entries(valueTypes)) {
        if (vt === "list") m[k] = "list";
        else if (vt === "number") m[k] = "number";
        else if (vt === "switch") m[k] = "boolean";
      }
    }
    // 2. From layout cell models (fallback — declared type via control)
    if (layout) {
      for (const row of layout) {
        for (const cell of row) {
          if (!cell.store || m[cell.store]) continue;
          if (MODEL_LIST_TYPES.has(cell.model ?? "")) m[cell.store] = "list";
          else if (MODEL_NUM_TYPES.has(cell.model ?? "")) m[cell.store] = "number";
          else if (MODEL_BOOL_TYPES.has(cell.model ?? "")) m[cell.store] = "boolean";
        }
      }
    }
    // 3. From runtime values (lowest priority)
    if (values) {
      for (const [k, v] of Object.entries(values)) {
        if (m[k]) continue;
        if (Array.isArray(v)) m[k] = "list";
        else if (typeof v === "number") m[k] = "number";
        else if (typeof v === "boolean") m[k] = "boolean";
      }
    }
    return m;
  }, [valueTypes, layout, values]);

  // Extended varOptions: native {var} entries + len(var) / {var}[0] for list-type variables
  const extendedVarOptions = useMemo(() => {
    const opts = [...varOptions];
    const seen = new Set(varOptions.map((o) => o.value));
    for (const opt of varOptions) {
      const bare = opt.value.replace(/^\{|\}$/g, "");
      if (!bare || bare === opt.value) continue;
      // Add len() variant for list-type variables (from layout or values)
      if (varTypeMap[bare] === "list") {
        const lenVal = `len(${bare})`;
        if (!seen.has(lenVal)) { opts.push({ value: lenVal, label: `${lenVal} — 列表长度` }); seen.add(lenVal); }
        const subVal = `{${bare}}[0]`;
        if (!seen.has(subVal)) { opts.push({ value: subVal, label: `${subVal} — 取下标` }); seen.add(subVal); }
      }
    }
    return opts;
  }, [varOptions, varTypeMap]);

  // Build varOptions array for VariablePicker (used in value fields)
  const pickerVars = useMemo(() =>
    varOptions.map((v) => ({ syntax: v.value, label: v.label, category: "task" as const })),
  [varOptions]);

  // Parse existing value on mount
  useEffect(() => {
    if (!value) return;
    const force = (m: Mode) => setMode(allowedModes.includes(m) ? m : allowedModes[0]);
    if (value === "{True}") { force("true"); return; }
    const parsed = parseExpr(value);
    if (parsed.length === 0) {
      const m = value.match(/^\{(\w+)\}$/);
      if (m && !COMPARE_OPS.some((op) => value.includes(op))) {
        setVarName(m[1]); force("var"); return;
      }
      force("true"); return;
    }
    if (parsed.length === 1 && parsed[0].op === "==" && parsed[0].val === "") {
      setVarName(parsed[0].var.replace(/[{}]/g, ""));
      force("var"); return;
    }
    setConds(parsed);
    force("compare");
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Wheel listeners for operator stepper
  useEffect(() => {
    const handles: { el: HTMLButtonElement; fn: (e: WheelEvent) => void }[] = [];
    opBtnRefs.current.forEach((el, i) => {
      if (!el) return;
      const fn = (e: WheelEvent) => {
        e.preventDefault(); e.stopPropagation();
        const cur = condsRef.current[i]; if (!cur) return;
        const idx = COMPARE_OPS.indexOf(cur.op);
        const dir: "up" | "down" = e.deltaY > 0 ? "down" : "up";
        const newIdx = dir === "down" ? (idx + 1) % COMPARE_OPS.length : idx <= 0 ? COMPARE_OPS.length - 1 : idx - 1;
        const newOp = COMPARE_OPS[newIdx];
        setOpSpin((g) => ({ ...g, [i]: { old: cur.op, cur: newOp, dir } }));
        setTimeout(() => setOpSpin((g) => { const n = { ...g }; delete n[i]; return n; }), 700);
        const next = [...condsRef.current]; next[i] = { ...next[i], op: newOp };
        const expr = buildExpr(next); if (expr) onChange(expr);
        setConds(next); setPreviewKey((k) => k + 1);
      };
      el.addEventListener("wheel", fn, { passive: false });
      handles.push({ el, fn });
    });
    return () => handles.forEach(({ el, fn }) => el.removeEventListener("wheel", fn));
  }, [onChange]);

  const fire = useCallback((expr: string) => { onChange(expr); setPreviewKey((k) => k + 1); }, [onChange]);

  const handleVarChange = (raw: string | undefined) => {
    const name = (raw ?? "").replace(/^\{|\}$/g, "");
    setVarName(name);
    if (name) fire(`{${name}}`);
  };

  const syncConds = (next: Cond[]) => { setConds(next); const expr = buildExpr(next); if (expr) fire(expr); };
  const setCond = (i: number, p: Partial<Cond>) => { const next = [...conds]; next[i] = { ...next[i], ...p }; syncConds(next); };

  const switchMode = (m: Mode) => {
    setMode(m);
    if (m === "true") fire("{True}");
    else if (m === "var") { if (varName) fire(`{${varName}}`); }
    else { const expr = buildExpr(conds); if (expr) fire(expr); }
  };

  const currentExpr = mode === "true" ? "{True}" : mode === "var" ? (varName ? `{${varName}}` : "{...}") : (buildExpr(conds) || "{...}");

  return (
    <div className="flex flex-col" style={{ gap: 10 }}>
      {/* ── Mode tabs ── */}
      <div className="flex rounded-lg p-0.5" style={{ background: "#f0ede8", gap: 2 }}>
        {MODES.filter((m) => allowedModes.includes(m.key)).map((m) => {
          const active = mode === m.key;
          return (
            <button key={m.key} onClick={() => switchMode(m.key)}
              className="flex items-center gap-1.5 flex-1 justify-center rounded-md py-1.5 px-2 text-xs transition-all duration-200 select-none outline-none border-0 cursor-pointer"
              style={{ background: active ? "#fff" : "transparent", color: active ? "#3d3630" : "#9a8e82",
                fontWeight: active ? 600 : 400, boxShadow: active ? "0 1px 2px rgba(0,0,0,0.06), 0 1px 0 rgba(0,0,0,0.03)" : "none" }}>
              <span style={{ fontSize: 12, color: active ? "#d4513b" : "#b8afa6" }}>{m.icon}</span>
              {m.label}
            </button>
          );
        })}
      </div>

      {/* ── Mode content ── */}
      <div className="rounded-lg border px-3 py-3 transition-all duration-200"
        style={{ borderColor: "#e8e3dc", background: "linear-gradient(180deg, #fdfcf9, #faf8f5)" }}>

        {/* True */}
        {mode === "true" && (
          <div className="flex items-center gap-2.5">
            <span className="inline-flex items-center justify-center rounded-md shrink-0" style={{ width: 28, height: 28, background: "#fef3ef" }}>
              <ThunderboltOutlined style={{ fontSize: 13, color: "#d4513b" }} />
            </span>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs font-semibold" style={{ color: "#3d3630" }}>无条件通过</span>
              <span className="text-[10px]" style={{ color: "#b8afa6" }}>无论任何条件，此步骤始终判定为成功</span>
            </div>
            <code className="ml-auto text-[11px] font-semibold px-2 py-0.5 rounded" style={{ background: "#fef3ef", color: "#d4513b" }}>{"{True}"}</code>
          </div>
        )}

        {/* Var */}
        {mode === "var" && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center rounded-md shrink-0" style={{ width: 28, height: 28, background: "#f3f0ec" }}>
                <BranchesOutlined style={{ fontSize: 13, color: "#6b5e55" }} />
              </span>
              <span className="text-xs font-semibold" style={{ color: "#3d3630" }}>变量判断</span>
              <span className="text-[10px]" style={{ color: "#b8afa6" }}>变量值为真（非空/非零）时通过</span>
            </div>
            <Select size="small" showSearch placeholder="选择一个变量…"
              value={varName ? `{${varName}}` : undefined} popupMatchSelectWidth={false} style={{ width: "100%" }}
              options={extendedVarOptions}
              filterOption={(input, option) => option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false}
              onChange={(v) => handleVarChange(v ?? "")} />
            {/* Operation shortcuts — shown when variable is selected */}
            {varName && (
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[10px] text-[#b8afa6] mr-1">操作:</span>
                {[{ l: "取值", e: `{${varName}}` }, { l: "++", e: `{${varName}}++` }, { l: "--", e: `{${varName}}--` },
                  { l: "长度", e: `len(${varName})` }, { l: "[0]", e: `{${varName}}[0]` }].map((op) => (
                  <button key={op.l} onClick={() => fire(op.e)}
                    className="text-[10px] font-medium px-2 py-1 rounded border transition-colors outline-none cursor-pointer"
                    style={{ borderColor: "#e8e3dc", background: "#fff", color: "#6b5e55" }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = "#fef3ef"; e.currentTarget.style.borderColor = "#d4513b"; e.currentTarget.style.color = "#d4513b"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = "#fff"; e.currentTarget.style.borderColor = "#e8e3dc"; e.currentTarget.style.color = "#6b5e55"; }}
                  >{op.l}</button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Compare */}
        {mode === "compare" && (
          <div className="flex flex-col" style={{ gap: 10 }}>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center justify-center rounded-md shrink-0" style={{ width: 28, height: 28, background: "#fef9f0" }}>
                <FilterOutlined style={{ fontSize: 13, color: "#d48806" }} />
              </span>
              <span className="text-xs font-semibold" style={{ color: "#3d3630" }}>条件比较</span>
              <span className="text-[10px]" style={{ color: "#b8afa6" }}>所有条件满足时通过</span>
              <span className="ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded" style={{ background: "#f3f0ec", color: "#9a8e82" }}>
                {conds.filter((c) => c.var).length} / {conds.length}
              </span>
            </div>

            {conds.map((c, i) => (
              <div key={i} ref={(el) => { condRefs.current[i] = el; }}
                style={{ animation: `condSlideIn 0.25s ease-out both`, animationDelay: `${i * 0.04}s` }}>
                {i > 0 && (
                  <div className="flex items-center" style={{ height: 20, paddingLeft: 16 }}>
                    <div style={{ width: 1, height: "100%", background: "#e8e3dc" }} />
                    <button onClick={() => setCond(i, { logic: c.logic === "&&" ? "||" : "&&" })}
                      className="text-[10px] px-2.5 py-px rounded-full border font-semibold transition-all select-none outline-none cursor-pointer shrink-0"
                      style={{ marginLeft: -0.5, borderColor: c.logic === "&&" ? "#d4513b33" : "#d4880633",
                        background: c.logic === "&&" ? "#fef3ef" : "#fef9f0", color: c.logic === "&&" ? "#d4513b" : "#d48806" }}>
                      {c.logic === "&&" ? "且" : "或"}
                    </button>
                  </div>
                )}

                <div className="flex items-stretch rounded-lg border bg-container transition-all duration-200 overflow-hidden"
                  style={{ borderColor: "#e8e3dc", boxShadow: "0 1px 2px rgba(0,0,0,0.02)" }}>
                  <div className="shrink-0 transition-all duration-200" style={{ width: 3,
                    background: c.var ? "linear-gradient(180deg, #d4513b, #e87a5a)" : "#d9cfc4", borderRadius: "3px 0 0 3px" }} />

                  {/* Condition number — moved to left */}
                  <div className="flex items-center justify-center shrink-0 text-[10px] font-semibold"
                    style={{ width: 22, color: c.var ? "#d4513b" : "#d9cfc4", background: c.var ? "#fef3ef" : "transparent" }}>{i + 1}</div>

                  {/* Variable */}
                  <div className="flex-1 flex items-center min-w-0" style={{ padding: "6px 0 6px 4px" }}>
                    <Select size="small" variant="borderless" className="font-semibold"
                      style={{ width: "100%", borderRadius: 0 }} placeholder="变量" showSearch
                      value={c.var || undefined} popupMatchSelectWidth={false} options={extendedVarOptions}
                      filterOption={(input, option) => option?.label?.toLowerCase().includes(input.toLowerCase()) ?? false}
                      onChange={(v) => setCond(i, { var: v ?? "" })} />
                  </div>

                  {/* Operator stepper */}
                  <div className="flex items-center shrink-0 select-none" style={{ padding: "2px 4px" }}>
                    <button onClick={() => { const idx = COMPARE_OPS.indexOf(c.op); const prevIdx = idx <= 0 ? COMPARE_OPS.length - 1 : idx - 1; const prevOp = COMPARE_OPS[prevIdx]; setOpSpin((g) => ({ ...g, [i]: { old: c.op, cur: prevOp, dir: "up" } })); setTimeout(() => setOpSpin((g) => { const n = { ...g }; delete n[i]; return n; }), 700); setCond(i, { op: prevOp }); }}
                      className="flex items-center justify-center outline-none border-0 bg-transparent cursor-pointer rounded transition-colors"
                      style={{ width: 14, height: 14, color: "#c4bbb2" }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}>
                      <svg width="8" height="5" viewBox="0 0 8 5" fill="currentColor"><path d="M4 0L7.46 4.5H.54z" /></svg>
                    </button>
                    <div className="relative" style={{ width: 32, height: 24, overflow: "hidden" }}>
                      {opSpin[i] && (
                        <span key={`spin-old-${i}`} className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xs pointer-events-none"
                          style={{ color: "#b8afa6", animation: opSpin[i].dir === "down" ? "opRollOutUp 0.6s ease-in forwards" : "opRollOutDown 0.6s ease-in forwards" }}>
                          {opSpin[i].old}</span>
                      )}
                      {opSpin[i] && (
                        <span key={`spin-cur-${i}`} className="absolute inset-0 flex items-center justify-center font-mono font-bold text-xs pointer-events-none"
                          style={{ color: "#d4513b", animation: opSpin[i].dir === "down" ? "opRollInUp 0.6s ease-out forwards" : "opRollInDown 0.6s ease-out forwards" }}>
                          {opSpin[i].cur}</span>
                      )}
                      <button ref={(el) => { opBtnRefs.current[i] = el; }}
                        className="flex items-center justify-center outline-none border-0 bg-transparent cursor-pointer font-mono font-bold text-xs rounded"
                        style={{ width: 32, height: 24, color: "#4a423b", opacity: opSpin[i] ? 0 : 1, transition: "opacity 0.15s" }}
                        onMouseEnter={(e) => { if (!opSpin[i]) e.currentTarget.style.background = "#f3f0ec"; }}
                        onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                        onClick={() => { const idx = COMPARE_OPS.indexOf(c.op); const nextIdx = (idx + 1) % COMPARE_OPS.length; const nextOp = COMPARE_OPS[nextIdx]; setOpSpin((g) => ({ ...g, [i]: { old: c.op, cur: nextOp, dir: "down" } })); setTimeout(() => setOpSpin((g) => { const n = { ...g }; delete n[i]; return n; }), 700); setCond(i, { op: nextOp }); }}>
                        {c.op}
                      </button>
                    </div>
                    <button onClick={() => { const idx = COMPARE_OPS.indexOf(c.op); const nextIdx = (idx + 1) % COMPARE_OPS.length; const nextOp = COMPARE_OPS[nextIdx]; setOpSpin((g) => ({ ...g, [i]: { old: c.op, cur: nextOp, dir: "down" } })); setTimeout(() => setOpSpin((g) => { const n = { ...g }; delete n[i]; return n; }), 700); setCond(i, { op: nextOp }); }}
                      className="flex items-center justify-center outline-none border-0 bg-transparent cursor-pointer rounded transition-colors"
                      style={{ width: 14, height: 14, color: "#c4bbb2" }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}>
                      <svg width="8" height="5" viewBox="0 0 8 5" fill="currentColor"><path d="M4 5L.54.5h6.92z" /></svg>
                    </button>
                  </div>

                  {/* Value — with VariablePicker for inserting len(var), {var}[n], etc. */}
                  <div className="flex-1 flex items-center min-w-0 gap-0.5" style={{ padding: "6px 2px 6px 0" }}>
                    <Input size="small" variant="borderless"
                      style={{ width: "100%", borderRadius: 0, fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace", fontSize: 12 }}
                      placeholder="期望值" value={c.val}
                      onChange={(e) => setCond(i, { val: e.target.value })} />
                    <VariablePicker variables={pickerVars} onInsert={(expr) => setCond(i, { val: c.val + expr })} />
                  </div>

                  <button onClick={() => { if (conds.length <= 1) syncConds([defaultCond()]); else syncConds(conds.filter((_, idx) => idx !== i)); }}
                    className="shrink-0 flex items-center justify-center text-xs transition-all duration-150 outline-none border-0 bg-transparent cursor-pointer"
                    style={{ width: 26, color: "#c4bbb2" }}
                    onMouseEnter={(e) => { e.currentTarget.style.color = "#d4513b"; e.currentTarget.style.background = "#fef3ef"; }}
                    onMouseLeave={(e) => { e.currentTarget.style.color = "#c4bbb2"; e.currentTarget.style.background = "transparent"; }}>×</button>
                </div>
              </div>
            ))}

            <Button type="dashed" size="small" block
              onClick={() => syncConds([...conds, defaultCond()])}
              style={{ borderColor: "#d9cfc4", color: "#9a8e82", borderRadius: 8, fontSize: 11, height: 30 }}>
              添加条件
            </Button>
          </div>
        )}
      </div>

      {/* ── Preview ── */}
      <div key={previewKey} className="rounded-lg px-3 py-2.5 flex items-center gap-3 overflow-hidden relative"
        style={{ background: "linear-gradient(135deg, #2b2520, #3d3630)", border: "1px solid #4a423b",
          animation: previewKey > 0 ? "exprPulse 0.4s ease-out" : undefined }}>
        <span className="text-[9px] uppercase tracking-widest shrink-0 font-semibold" style={{ color: "#9a8e82" }}>生成</span>
        <div style={{ width: 1, height: 16, background: "#4a423b", flexShrink: 0 }} />
        <code className="text-xs flex-1 truncate" style={{ color: "#f0c060", fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace" }}>
          {currentExpr}
        </code>
        <span className="shrink-0 rounded-full transition-all" style={{ width: 6, height: 6,
          background: mode === "true" ? "#10b981" : mode === "var" ? "#f59e0b" : "#3b82f6",
          boxShadow: mode === "true" ? "0 0 6px rgba(16,185,129,0.5)" : mode === "var" ? "0 0 6px rgba(245,158,11,0.5)" : "0 0 6px rgba(59,130,246,0.5)" }} />
      </div>

      <style>{`
        @keyframes exprPulse { 0%{box-shadow:0 0 0 0 rgba(240,192,96,0.3)} 50%{box-shadow:0 0 12px 2px rgba(240,192,96,0.15)} 100%{box-shadow:0 0 0 0 rgba(240,192,96,0)} }
        @keyframes condSlideIn { 0%{opacity:0;transform:translateY(-6px)} 100%{opacity:1;transform:translateY(0)} }
        @keyframes opRollOutUp { 0%{opacity:1;transform:translateY(0)} 100%{opacity:0;transform:translateY(-140%)} }
        @keyframes opRollInUp { 0%{opacity:0;transform:translateY(140%)} 100%{opacity:1;transform:translateY(0)} }
        @keyframes opRollOutDown { 0%{opacity:1;transform:translateY(0)} 100%{opacity:0;transform:translateY(140%)} }
        @keyframes opRollInDown { 0%{opacity:0;transform:translateY(-140%)} 100%{opacity:1;transform:translateY(0)} }
      `}</style>
    </div>
  );
};

export default ExpressionActionBuilder;
