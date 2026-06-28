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
  accepts?: Record<string, unknown>;
  next?: string;
  success?: string;
  failure?: string;
}

const SUB_LISTS = ["prefix", "postfix", "failure_extra", "success_extra"] as const;

/**
 * Extract {param:default} template parameters from a step's own definition
 * and its direct call-site args — no recursion into sub-steps or chains.
 * Only {var:default} templates and non-string params keys are treated as overridable parameters.
 */
export function extractAllParams(
  stepName: string,
  allStepsData: Record<string, StepDef | undefined>,
  _visited?: Set<string>,
  _skipOwnParams?: boolean,
): Record<string, unknown> {
  if (!stepName || stepName === "任务结束") return {};

  const stepData = allStepsData[stepName];
  if (!stepData) return {};

  const result: Record<string, unknown> = {};

  // Only extract {var:default} templates — bare var refs ({var}) and function
  // args (len/split) are NOT parameters, they're internal dependencies.
  const scanStr = (s: string) => {
    for (const m of s.matchAll(/\{([^{:}]+):([^}]*)\}/g)) {
      if (!(m[1] in result)) result[m[1]] = m[2];
    }
  };

  // 1. From own params — args array and named params values
  const ownArgs = stepData.params?.args;
  if (Array.isArray(ownArgs)) {
    for (const arg of ownArgs) scanStr(String(arg));
  } else if (typeof ownArgs === "string") {
    scanStr(ownArgs);
  }
  // Non-args params keys: string values scanned for templates,
  // non-string values captured directly as overridable config
  if (stepData.params) {
    for (const [k, v] of Object.entries(stepData.params)) {
      if (k === "args") continue;
      if (typeof v === "string") scanStr(v);
      else if (Array.isArray(v)) v.forEach(item => { if (typeof item === "string") scanStr(item); });
      else if (v !== undefined) {
        if (!(k in result)) result[k] = v;
      }
    }
  }

  // 2. From preset values — scan for {var:default} templates
  //    (postset/success_set/failure_set are outputs, not parameters)
  const presetItems = (stepData as Record<string, unknown>)["preset"] as { name: string; value: unknown }[] | undefined;
  if (presetItems) {
    for (const item of presetItems) {
      if (typeof item.value === "string") scanStr(item.value);
    }
  }

  // 3. From direct call-site args in prefix/postfix/failure_extra/success_extra
  //    — only the args themselves, no recursion into the called step
  for (const key of SUB_LISTS) {
    const items = (stepData as Record<string, unknown>)[key] as StepDef[keyof Pick<StepDef, "prefix" | "postfix" | "failure_extra" | "success_extra">] | undefined;
    if (!items) continue;
    for (const item of items) {
      if (typeof item === "object" && item.args) {
        if (Array.isArray(item.args)) {
          for (const v of item.args as unknown[]) {
            if (typeof v === "string") scanStr(v);
          }
        } else {
          for (const [k, v] of Object.entries(item.args as Record<string, unknown>)) {
            if (!(k in result)) result[k] = v;
            if (typeof v === "string") scanStr(v);
          }
        }
      }
    }
  }

  return result;
}
