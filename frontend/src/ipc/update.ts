import { callApi } from "@/utils/pywebview";

export async function checkUpdate(): Promise<Record<string, unknown> | null> {
  return callApi<Record<string, unknown>>("API:UPDATE:CHECK");
}

export async function downloadUpdate(currentVersion: string): Promise<void> {
  return callApi("API:UPDATE:DOWNLOAD", { current_version: currentVersion });
}

export async function applyUpdate(): Promise<void> {
  return callApi("API:UPDATE:APPLY");
}

export async function getVersion(): Promise<string> {
  return callApi<string>("API:APP:VERSION") ?? "0.0.0";
}

export async function getUpdateDiff(
  currentVersion: string, manifest: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  return callApi("API:UPDATE:DIFF", { current_version: currentVersion, manifest }) ?? {};
}
