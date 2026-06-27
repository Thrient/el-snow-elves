export interface TaskListItem {
  name: string;
  author?: string;
  versions: string[];
  latest: string;
  description: string;
  steps: Record<string, unknown>;
  start: string;
  layout?: Record<string, unknown>[][];
  values?: Record<string, unknown>;
}
