import { callApi } from "@/utils/pywebview";

export async function captureTemplate(hwnd: string, name: string): Promise<void> {
  return callApi("API:TEMPLATE:CAPTURE", hwnd, name);
}

export async function captureTemplatePng(hwnd: string, name: string): Promise<void> {
  return callApi("API:TEMPLATE:CAPTURE:PNG", hwnd, name);
}

export async function saveTemplate(name: string, hwnd: string): Promise<void> {
  return callApi("API:TEMPLATE:SAVE", name, hwnd);
}

export async function applyPreprocess(
  hwnd: string, config: Record<string, unknown>,
): Promise<{ dataUrl: string }> {
  return callApi("API:PREPROCESS:APPLY", hwnd, config);
}
