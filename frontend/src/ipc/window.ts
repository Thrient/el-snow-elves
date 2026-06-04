import { callApi } from "@/utils/pywebview";

export interface WindowInfo {
  hwnd: string;
  title: string;
  pid: number;
}

export async function searchWindows(): Promise<WindowInfo[]> {
  return callApi<WindowInfo[]>("API:SCRIPT:SEARCH") ?? [];
}

export async function bindWindow(hwnd: string, characterName: string): Promise<void> {
  return callApi("API:SCRIPT:BIND", hwnd, characterName);
}

export async function unbindWindow(hwnd: string): Promise<void> {
  return callApi("API:SCRIPT:UNBIND", hwnd);
}

export async function resumeWindow(hwnd: string): Promise<void> {
  return callApi("API:SCRIPT:RESUME", hwnd);
}

export async function pauseWindow(hwnd: string): Promise<void> {
  return callApi("API:SCRIPT:PAUSE", hwnd);
}

export async function stopWindow(hwnd: string): Promise<void> {
  return callApi("API:SCRIPT:STOP", hwnd);
}

export async function setWindowOpacity(hwnd: string, opacity: number): Promise<void> {
  return callApi("API:SCRIPT:SET_OPACITY", hwnd, opacity);
}

export async function pushExecute(hwnd: string, payload: Record<string, unknown>): Promise<void> {
  return callApi("API:SCRIPT:PUSH_EXECUTE", hwnd, payload);
}
