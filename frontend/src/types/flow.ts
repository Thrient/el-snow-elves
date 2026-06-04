import type { FlowType } from "@/utils/flow-convert";

export type { FlowType };

export interface StepNodeData {
  stepName: string;
  action?: string;
  description?: string;
  isCommon: boolean;
  isStart: boolean;
}

export interface StepEdgeData {
  flowType: FlowType;
}
