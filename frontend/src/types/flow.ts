import type { FlowType } from "@/utils/flow-convert";

export type { FlowType };

export interface StepNodeData {
  stepName: string;
  action?: string;
  description?: string;
  isCommon: boolean;
  isStart: boolean;
  /** ReactFlow requires Record<string, unknown> — do not remove */
  [key: string]: unknown;
}

export interface StepEdgeData {
  flowType: FlowType;
  /** ReactFlow requires Record<string, unknown> — do not remove */
  [key: string]: unknown;
}
