export {}

declare global {
  interface Window {
    pywebview: {
      api: {
        emit(name: string);
        emit(name: string, arg1: unknown);
        emit(name: string, arg1: unknown, arg2: unknown);
        emit(name: string, ...args: unknown[]);
      }
    }
  }
}

