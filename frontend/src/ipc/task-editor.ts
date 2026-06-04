import { callApi } from "@/utils/pywebview";
import type { FullTask } from "@/types/task-editor";

export async function loadFullTask(id: string): Promise<FullTask | null> {
  return callApi<FullTask>("API:TASK:LOAD:FULL", id);
}

export async function saveFullTask(id: string, task: FullTask): Promise<void> {
  return callApi("API:TASK:SAVE:FULL", id, task);
}

export async function createTask(
  name: string, version: string, author: string, description: string,
): Promise<string> {
  return callApi<string>("API:TASK:CREATE", name, version, author, description);
}

export async function deleteTask(id: string): Promise<void> {
  return callApi("API:TASK:DELETE", id);
}

export async function loadPositions(taskId: string): Promise<Record<string, { x: number; y: number }>> {
  return callApi("API:TASK:LOAD:POSITIONS", taskId) ?? {};
}

export async function savePositions(
  taskId: string, positions: Record<string, { x: number; y: number }>,
): Promise<void> {
  return callApi("API:TASK:SAVE:POSITIONS", taskId, positions);
}

export async function clearCommonCache(): Promise<void> {
  return callApi("API:COMMON:CACHE:CLEAR");
}
