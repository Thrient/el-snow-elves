export interface PlanAction {
  type: "refill_queue" | "push_task";
  params: Record<string, unknown>;
}

export interface PlanBase {
  name: string;
  templateId: string;
  cron: string;
  enabled: boolean;
  action: PlanAction;
}

export interface Plan extends PlanBase {
  id: string;
  createdAt: number;
  updatedAt: number;
}

export interface PlanTemplate {
  id: string;
  name: string;
  description: string;
  defaultCron: string;
  actionType: PlanAction["type"];
  paramSchema: Record<string, unknown>;
}

export const PLAN_TEMPLATES: PlanTemplate[] = [
  {
    id: "restart",
    name: "定时重启",
    description: "定时重新填充窗口的执行队列（替换）",
    defaultCron: "0 5 * * *",
    actionType: "refill_queue",
    paramSchema: {
      source: { type: "enum", label: "填充来源", options: ["current_queue", "config"], default: "current_queue" },
      configName: { type: "string", label: "配置文件名", required: false },
    },
  },
  {
    id: "push_task",
    name: "限时任务",
    description: "定时推送任务到窗口执行队列",
    defaultCron: "*/30 * * * *",
    actionType: "push_task",
    paramSchema: {
      taskId: { type: "string", label: "任务", required: true },
    },
  },
];
