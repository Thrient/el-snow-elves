const MAX_RETRIES = 20
const RETRY_DELAY = 500

export const waitForPywebview = async (): Promise<boolean> => {
  for (let i = 0; i < MAX_RETRIES; i++) {
    if (window.pywebview) return true
    await new Promise((r) => setTimeout(r, RETRY_DELAY))
  }
  return false
}

/** Typed IPC wrapper. PyWebView is always available at runtime. */
export const callApi = async <T>(name: string, ...args: unknown[]): Promise<T> => {
  return window.pywebview.api.emit(name, ...args) as Promise<T>;
}
