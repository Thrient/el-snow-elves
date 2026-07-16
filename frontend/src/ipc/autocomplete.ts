import { callApi } from "@/utils/pywebview";

export async function getActions(): Promise<{ value: string; label: string }[]> {
  return callApi<{ value: string; label: string }[]>("API:AUTOCOMPLETE:ACTIONS") ?? [];
}

export async function getTemplates(
  taskName: string | null, version: string | null, author?: string,
): Promise<string[]> {
  return callApi<string[]>("API:AUTOCOMPLETE:TEMPLATES", taskName, version, author ?? "匿名作者") ?? [];
}

export async function getCommonSteps(): Promise<Record<string, {
  action?: string; params?: Record<string, unknown>;
}>> {
  return callApi("API:AUTOCOMPLETE:COMMON:STEPS") ?? {};
}
