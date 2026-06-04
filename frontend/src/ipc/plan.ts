import { callApi } from "@/utils/pywebview";
import type { Plan } from "@/types/plan";

export async function loadPlans(): Promise<Plan[]> {
  return callApi<Plan[]>("API:PLAN:LOAD") ?? [];
}

export async function savePlans(plans: Plan[]): Promise<void> {
  return callApi("API:PLAN:SAVE", plans);
}

export async function triggerCron(hwnd: string): Promise<void> {
  return callApi("API:CRON:TRIGGER", hwnd);
}
