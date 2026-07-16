export interface TaskListItem {
  name: string;
  author?: string;
  hub_task_id?: number;  // Hub task ID for version tracking
  versions: string[];
  latest: string;
  description: string;
  steps: Record<string, unknown>;
  start: string;
  layout?: Record<string, unknown>[][];
  values?: Record<string, unknown>;
}
