import { callApi } from "@/utils/pywebview";
import type { Task } from "@/types/task-editor";

export async function loadTaskList(): Promise<Task[]> {
  const raw = await callApi<Task[]>("API:SCRIPT:LOAD:LIST");
  return raw ?? [];
}

export async function exportTask(id: string, path: string): Promise<void> {
  return callApi("API:TASK:EXPORT", id, path);
}

export async function exportBatch(ids: string[], path: string): Promise<void> {
  return callApi("API:TASK:EXPORT:BATCH", ids, path);
}

export async function importTask(path: string): Promise<Task> {
  return callApi<Task>("API:TASK:IMPORT", path);
}
