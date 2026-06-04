import { callApi } from "@/utils/pywebview";

export async function listAccounts(): Promise<Record<string, unknown>[]> {
  return callApi<Record<string, unknown>[]>("API:ACCOUNT:LIST") ?? [];
}

export async function saveAccount(name: string, data: Record<string, unknown>): Promise<void> {
  return callApi("API:ACCOUNT:SAVE", name, data);
}

export async function deleteAccount(name: string): Promise<void> {
  return callApi("API:ACCOUNT:DELETE", name);
}

export async function renameAccount(oldName: string, newName: string): Promise<void> {
  return callApi("API:ACCOUNT:RENAME", oldName, newName);
}

export async function saveOrder(order: string[]): Promise<void> {
  return callApi("API:ACCOUNT:SAVE_ORDER", order);
}

export async function quickStart(): Promise<void> {
  return callApi("API:ACCOUNT:QUICK_START");
}

export async function startRecord(): Promise<void> {
  return callApi("API:ACCOUNT:RECORD:START");
}

export async function startChannelRecord(channel: string): Promise<void> {
  return callApi("API:ACCOUNT:RECORD:START:CHANNEL", channel);
}

export async function stopRecord(): Promise<void> {
  return callApi("API:ACCOUNT:RECORD:STOP");
}

export async function recordStatus(): Promise<string> {
  return callApi<string>("API:ACCOUNT:RECORD:STATUS");
}

export async function startReplay(name: string): Promise<void> {
  return callApi("API:ACCOUNT:REPLAY:START", name);
}

export async function stopReplay(): Promise<void> {
  return callApi("API:ACCOUNT:REPLAY:STOP");
}

export async function getGamePath(): Promise<string> {
  return callApi<string>("API:GAME:GET_PATH") ?? "";
}

export async function setGamePath(path: string): Promise<void> {
  return callApi("API:GAME:SET_PATH", path);
}
