export interface TaskListItem {
  id: string;
  name: string;
  version: string;
  author: string;
  description: string;
  steps: Record<string, unknown>;
  start: string;
}
