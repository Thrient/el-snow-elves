/**
 * 合并任务 values：repo 默认值打底 → 用户值覆盖 → 可选注入 CONFIG
 *
 * @param repoDefaults  任务 repo 中的默认 values
 * @param queuedValues  队列中用户已填的 values
 * @param configValues  可选，settings.values 作为 CONFIG 注入（仅 popExecute 使用）
 */
export function mergeValues(
  repoDefaults: Record<string, unknown>,
  queuedValues: Record<string, unknown>,
  configValues?: Record<string, unknown>,
): Record<string, unknown> {
  const merged = { ...repoDefaults, ...queuedValues };
  if (configValues) {
    merged["CONFIG"] = configValues;
  }
  return merged;
}
