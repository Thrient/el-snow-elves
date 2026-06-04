import { callApi } from "@/utils/pywebview";

export async function readLogs(
  page: number, pageSize: number,
): Promise<{ total: number; rows: Record<string, unknown>[] }> {
  return callApi("API:LOG:READ", page, pageSize) ?? { total: 0, rows: [] };
}

export async function listLogFiles(): Promise<string[]> {
  return callApi<string[]>("API:LOG:FILES") ?? [];
}
