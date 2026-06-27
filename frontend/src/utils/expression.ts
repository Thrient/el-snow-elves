/** Shared expression parse/build utilities */

export const COMPARE_OPS = ["==", "!=", ">", "<", ">=", "<="];

export interface Cond {
  var: string;
  op: string;
  val: string;
  logic: string;
}

export const defaultCond = (logic = "&&"): Cond => ({ var: "", op: "==", val: "", logic });

export const stripBraces = (v: string) => (v.startsWith("{") ? v.slice(1, -1) : v);

// Only quote values that are literal strings (not numbers, not variable refs)
const isLiteralString = (v: string) => {
  if (!v) return false;
  if (/^-?\d+(\.\d+)?$/.test(v.trim())) return false; // number
  if (/^(true|false)$/i.test(v.trim())) return false;  // boolean
  if (/^\{.+\}$/.test(v.trim())) return false;          // {var} reference
  if (/^[a-zA-Z_一-鿿][\w一-鿿]*$/.test(v.trim())) return false; // bare var name
  return true; // string literal
};
export const condPart = (c: Cond) => {
  const left = stripBraces(c.var);
  const right = isLiteralString(c.val) ? `'${c.val}'` : c.val;
  return `${left} ${c.op} ${right}`;
};

/** Build expression string from Cond[] — {a == '1' && b == '2'} */
export const buildExpr = (conds: Cond[]): string => {
  const valid = conds.filter((c) => c.var);
  if (valid.length === 0) return "";
  return `{${valid.map((c, i) => (i > 0 ? ` ${c.logic === '&&' ? 'and' : 'or'} ` : "") + condPart(c)).join("")}}`;
};

/** Parse expression string back to Cond[] */
export const parseExpr = (expr: string): Cond[] => {
  if (!expr) return [];
  let inner = expr.trim();
  if (inner.startsWith("{") && inner.endsWith("}") && inner.indexOf("{", 1) === -1) {
    inner = inner.slice(1, -1);
  }
  const parts = inner.split(/\s*(&&|\|\||\band\b|\bor\b)\s*/);
  const result: Cond[] = [];
  for (let i = 0; i < parts.length; i++) {
    const seg = parts[i].trim();
    if (seg === "&&" || seg === "||" || seg === "and" || seg === "or") continue;
    let s = seg;
    if (s.startsWith("{")) s = s.slice(1);
    if (s.endsWith("}")) s = s.slice(0, -1);
    const m = s.match(/^(.+?)\s*(==|!=|>=|<=|>|<)\s*(['"])?([^'"]*?)\3?$/);
    if (m) {
      const prev = parts[i - 1]?.trim();
      const logic = prev === "||" || prev === "or" ? "||" : "&&";
      result.push({ var: `{${m[1].trim()}}`, op: m[2], val: m[4] ?? m[3] ?? "", logic });
    }
  }
  return result;
};

/** Step definition shape for param extraction */
interface StepDef {
  action?: string;
  params?: { args?: string[]; [k: string]: unknown };
  prefix?: (string | { step: string; args?: Record<string, unknown>; when?: string })[];
  postfix?: (string | { step: string; args?: Record<string, unknown>; when?: string })[];
  failure_extra?: (string | { step: string; args?: Record<string, unknown>; when?: string })[];
  success_extra?: (string | { step: string; args?: Record<string, unknown>; when?: string })[];
  preset?: { name: string; value: unknown }[];
  postset?: { name: string; value: unknown }[];
  success_set?: { name: string; value: unknown }[];
  failure_set?: { name: string; value: unknown }[];
  next?: string;
  success?: string;
  failure?: string;
}

const SUB_LISTS = ["prefix", "postfix", "failure_extra", "success_extra"] as const;

/**
 * Recursively extract all {param:default} template parameters from a step
 * and its entire sub-step/next chain (prefix, postfix, failure_extra, success_extra,
 * and their next/success/failure targets).
 */
export function extractAllParams(
  stepName: string,
  allStepsData: Record<string, StepDef | undefined>,
  visited: Set<string> = new Set(),
  skipOwnParams = false,
): Record<string, unknown> {
  if (!stepName || stepName === "任务结束" || visited.has(stepName)) return {};
  visited.add(stepName);

  const stepData = allStepsData[stepName];
  if (!stepData) return {};

  const result: Record<string, unknown> = {};

  // Scan a string value for both {var:default} and {split(var,...)} / {len(var)} patterns
  const scanStr = (s: string) => {
    // {var:default}
    for (const m of s.matchAll(/\{([^{:}]+):([^}]*)\}/g)) {
      if (!(m[1] in result)) result[m[1]] = m[2];
    }
    // {split(var, sep)} / {len(var)} — extract bare variable names from function args
    for (const m of s.matchAll(/\b(split|len)\s*\(\s*([^,)]+)/g)) {
      const name = m[2].trim();
      if (name && !(name in result)) result[name] = "";
    }
  };

  // 1. From own params — both args array and named params values
  if (!skipOwnParams) {
    const ownArgs = stepData.params?.args;
    if (Array.isArray(ownArgs)) {
      for (const arg of ownArgs) scanStr(String(arg));
    } else if (typeof ownArgs === "string") {
      scanStr(ownArgs);
    }
    // Also scan all non-args params values
    if (stepData.params) {
      for (const [k, v] of Object.entries(stepData.params)) {
        if (k === "args") continue;
        if (typeof v === "string") scanStr(v);
        else if (Array.isArray(v)) v.forEach(item => { if (typeof item === "string") scanStr(item); });
        else if (v !== undefined) {
          // Capture raw non-string params (number, boolean, null) as overridable args
          if (!(k in result)) result[k] = v;
        }
      }
    }
  }

  // 1b. From preset/postset/success_set/failure_set values
  for (const key of ["preset", "postset", "success_set", "failure_set"] as const) {
    const items = (stepData as Record<string, unknown>)[key] as { name: string; value: unknown }[] | undefined;
    if (!items) continue;
    for (const item of items) {
      if (typeof item.value === "string") scanStr(item.value);
      if (item.name && !(item.name in result)) result[item.name] = "";
    }
  }

  // 2. From sub-step call sites (prefix/postfix/failure_extra/success_extra)
  for (const key of SUB_LISTS) {
    const items = (stepData as Record<string, unknown>)[key] as StepDef[keyof Pick<StepDef, "prefix" | "postfix" | "failure_extra" | "success_extra">] | undefined;
    if (!items) continue;
    for (const item of items) {
      const itemName = typeof item === "string" ? item : item?.step;
      const isListArgs = typeof item === "object" && Array.isArray(item.args);
      // 2a. Extract from call-site args
      if (typeof item === "object" && item.args) {
        if (isListArgs) {
          // list args: scan items for template refs (no named keys)
          for (const v of item.args as unknown as unknown[]) {
            if (typeof v === "string") scanStr(v);
          }
        } else {
          // dict args: scan keys and values
          for (const [k, v] of Object.entries(item.args as Record<string, unknown>)) {
            if (!(k in result)) result[k] = v;
            if (typeof v === "string") scanStr(v);
          }
        }
      }
      // 2b. Recurse into the called step; skip own params when args is a list
      if (itemName) {
        const inner = extractAllParams(itemName, allStepsData, visited, isListArgs);
        for (const [k, v] of Object.entries(inner)) {
          if (!(k in result)) result[k] = v;
        }
      }
    }
  }

  // 3. Follow next/success/failure chains (subflow continues through these)
  for (const key of ["next", "success", "failure"] as const) {
    const target = (stepData as Record<string, unknown>)[key] as string | undefined;
    if (target && target !== "任务结束") {
      const chain = extractAllParams(target, allStepsData, visited);
      for (const [k, v] of Object.entries(chain)) {
        if (!(k in result)) result[k] = v;
      }
    }
  }

  return result;
}
