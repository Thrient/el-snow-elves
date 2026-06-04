import { callApi } from "@/utils/pywebview";

export async function loadSettings(): Promise<Record<string, unknown>> {
  return callApi<Record<string, unknown>>("API:SETTINGS:LOAD") ?? {};
}

export async function loadConfigList(): Promise<string[]> {
  return callApi<string[]>("API:SCRIPT:LOAD:CONFIG:LIST") ?? [];
}

export async function loadConfig(name: string): Promise<Record<string, unknown>> {
  return callApi<Record<string, unknown>>("API:SCRIPT:LOAD:CONFIG", name) ?? {};
}

export async function saveConfig(name: string, data: Record<string, unknown>): Promise<void> {
  return callApi("API:SCRIPT:SAVE:CONFIG", name, data);
}

export async function deleteConfig(name: string): Promise<void> {
  return callApi("API:SCRIPT:DELETE:CONFIG", name);
}

export async function getAutostart(): Promise<boolean> {
  return callApi<boolean>("API:AUTOSTART:GET") ?? false;
}

export async function setAutostart(enabled: boolean): Promise<void> {
  return callApi("API:AUTOSTART:SET", enabled);
}
