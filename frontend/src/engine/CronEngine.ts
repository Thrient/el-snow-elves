import { Cron } from "croner";
import type { PlanBase } from "@/types/plan";
import type { ExecuteItem } from "@/store/character";
import { callApi } from "@/utils/pywebview";

function getCharStore() { return window.useCharacterStore!.getState(); }
function getTaskStore() { return window.useTaskStore!.getState(); }

type CronJob = Cron;

export class CronEngine {
  private hwnd: string;
  private initialQueue: ExecuteItem[];
  private jobs: CronJob[] = [];

  constructor(hwnd: string, initialQueue: ExecuteItem[]) {
    this.hwnd = hwnd;
    this.initialQueue = [...initialQueue];
  }

  start(plans: PlanBase[]) {
    this.stop();
    for (const plan of plans) {
      if (!plan.enabled) continue;
      try {
        const job = new Cron(plan.cron, () => this.execute(plan.action));
        this.jobs.push(job);
      } catch { /* 无效的 cron */ }
    }
  }

  stop() {
    for (const job of this.jobs) job.stop();
    this.jobs = [];
  }

  private async execute(action: PlanBase["action"]) {
    try {
      window.pywebview?.api.emit("API:CRON:TRIGGER", this.hwnd, action.type, action.params);
      if (action.type === "refill_queue") {
        await this.executeRefill(action.params);
      } else if (action.type === "push_task") {
        this.executePush(action.params);
      }
    } catch { /* */ }
  }

  private async executeRefill(params: Record<string, unknown>) {
    const store = getCharStore();
    const source = params.source as string;

    if (source === "config") {
      const configName = params.configName as string;
      if (!configName) return;
      try {
        const config = await callApi<{ queue?: ExecuteItem[] }>("API:SCRIPT:LOAD:CONFIG", configName);
        if (config?.queue && Array.isArray(config.queue)) {
          store.clearExecute(this.hwnd);
          for (const item of config.queue) {
            store.pushExecute(this.hwnd, {
              id: item.id, name: item.name, version: item.version, values: item.values ?? {},
            });
          }
        }
      } catch { /* */ }
    } else {
      store.clearExecute(this.hwnd);
      for (const item of this.initialQueue) {
        store.pushExecute(this.hwnd, { ...item });
      }
    }
  }

  private executePush(params: Record<string, unknown>) {
    const taskId = params.taskId as string;
    if (!taskId) return;
    const task = getTaskStore().taskList.find((t) => t.id === taskId);
    if (!task) return;
    getCharStore().unshiftExecute(this.hwnd, {
      id: task.id,
      name: task.name,
      version: task.version,
      values: (params.values ?? {}) as Record<string, unknown>,
    });
  }
}

const engines = new Map<string, CronEngine>();

export function getCronEngine(hwnd: string, initialQueue: ExecuteItem[]): CronEngine {
  let eng = engines.get(hwnd);
  if (!eng) {
    eng = new CronEngine(hwnd, initialQueue);
    engines.set(hwnd, eng);
  }
  return eng;
}

export function removeCronEngine(hwnd: string) {
  engines.get(hwnd)?.stop();
  engines.delete(hwnd);
}
