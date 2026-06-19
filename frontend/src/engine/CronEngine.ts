import { Cron } from "croner";
import { eventBus } from '@/utils/event-bus';
import type { PlanBase } from "@/types/plan";
import type { ExecuteItem } from "@/store/character-store";
import { callApi } from "@/utils/pywebview";

function getCharStore() { return window.useCharacterStore!.getState(); }
function getTaskStore() { return window.useCharacterStore!.getState(); }

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
    const taskStore = getTaskStore();
    const source = params.source as string;

    if (source === "config") {
      const configName = params.configName as string;
      if (!configName) return;
      try {
        const config = await callApi<{ queue?: ExecuteItem[] }>("API:SCRIPT:LOAD:CONFIG", configName);
        if (config?.queue && Array.isArray(config.queue)) {
          store.clearExecute(this.hwnd);
          const missingTasks: string[] = [];
          for (const item of config.queue) {
            const tn = (item as any).taskName || item.name;
            const taskMeta = taskStore.taskList.find((t: any) => t.name === tn);
            if (!taskMeta) {
              missingTasks.push(tn);
              continue;
            }
            store.pushExecute(this.hwnd, {
              id: item.id, name: item.name, version: item.version, values: item.values ?? {},
            });
          }
          if (missingTasks.length > 0) {
            eventBus.emit('notification', {
              title: '定时任务',
              description: `定时重填：${missingTasks.length} 个任务已不存在（${missingTasks.join("、")}），已跳过`,
              type: 'warning',
              duration: 5000,
            })
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
    const taskName = params.taskName as string;
    if (!taskName) return;
    const task = getTaskStore().taskList.find((t: any) => t.name === taskName);
    if (!task) {
      eventBus.emit('notification', {
        title: '计划执行失败',
        description: `任务「${taskName}」不存在，可能已被删除`,
        type: 'error',
        duration: 5000,
      })
      return;
    }
    const version = (params.version as string) || undefined;
    // 如果锁定了版本，检查版本是否存在
    if (version) {
      const taskMeta = task as any;
      if (taskMeta.versions && Array.isArray(taskMeta.versions) && !taskMeta.versions.includes(version)) {
        eventBus.emit('notification', {
          title: '版本变更',
          description: `计划「${taskName}」锁定版本 v${version} 已不存在，已切换为最新版本`,
          type: 'warning',
          duration: 5000,
        })
        getCharStore().unshiftExecute(this.hwnd, {
          id: "",
          name: taskName,
          taskName: taskName,
          version: null,
          values: (params.values ?? {}) as Record<string, unknown>,
        } as any);
        return;
      }
    }
    getCharStore().unshiftExecute(this.hwnd, {
      id: "",
      name: taskName,
      taskName: taskName,
      version: version ?? null,
      values: (params.values ?? {}) as Record<string, unknown>,
    } as any);
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
