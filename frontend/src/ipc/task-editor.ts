import { callApi } from "@/utils/pywebview";
import type { FullTask } from "@/types/task-editor";

export async function loadFullTask(id: string): Promise<FullTask | null> {
  return callApi<FullTask>("API:TASK:LOAD:FULL", id);
}

export async function saveFullTask(id: string, task: FullTask): Promise<void> {
  return callApi("API:TASK:SAVE:FULL", id, task);
}

export async function createTask(
  name: string, version: string, description: string,
): Promise<string> {
  return callApi<string>("API:TASK:CREATE", name, version, description);
}

export async function deleteTask(id: string): Promise<void> {
  return callApi("API:TASK:DELETE", id);
}

export async function saveAsNewVersion(
  id: string, newVersion: string,
): Promise<{ taskId: string; name: string; version: string }> {
  return callApi("API:TASK:SAVE:AS:NEW", id, newVersion);
}

export async function loadPositions(name: string, version: string): Promise<Record<string, { x: number; y: number }>> {
  return callApi("API:TASK:LOAD:POSITIONS", name, version) ?? {};
}

export async function savePositions(
  name: string, version: string, positions: Record<string, { x: number; y: number }>,
): Promise<void> {
  return callApi("API:TASK:SAVE:POSITIONS", name, version, positions);
}

export async function clearCommonCache(): Promise<void> {
  return callApi("API:COMMON:CACHE:CLEAR");
}
