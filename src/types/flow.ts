import type { Node, Edge } from "@xyflow/react";
import type { FullTask, Step } from "@/types/task";

const STEP_NODE = "stepNode";

export interface StepNodeData {
  [key: string]: unknown;
  stepName: string;
  action?: string;
  description?: string;
  isCommon: boolean;
  isStart: boolean;
}

export interface StepEdgeData {
  [key: string]: unknown;
  flowType: "success" | "failure" | "next";
}

export function taskToFlow(task: FullTask, savedPositions?: Record<string, { x: number; y: number }>): {
  nodes: Node<StepNodeData>[];
  edges: Edge<StepEdgeData>[];
} {
  const nodes: Node<StepNodeData>[] = [];
  const edges: Edge<StepEdgeData>[] = [];
  const allSteps = { ...task.steps, ...task.common };

  const names = Object.keys(allSteps);
  const cols = Math.ceil(Math.sqrt(names.length));
  const spacingX = 220;
  const spacingY = 100;

  names.forEach((name, i) => {
    const step = allSteps[name];
    const isCommon = name in (task.common ?? {});
    const isStart = name === task.start;
    const col = i % cols;
    const row = Math.floor(i / cols);
    const pos = savedPositions?.[name] ?? { x: col * spacingX + 50, y: row * spacingY + 50 };
    nodes.push({
      id: name,
      type: STEP_NODE,
      position: pos,
      data: {
        stepName: name,
        action: step.action,
        description: step.description,
        isCommon,
        isStart,
      },
    });
  });

  // Edges
  for (const [name, step] of Object.entries(allSteps)) {
    const targets: { target: string; flowType: "success" | "failure" | "next" }[] = [];
    if (step.success) targets.push({ target: step.success, flowType: "success" });
    if (step.failure) targets.push({ target: step.failure, flowType: "failure" });
    if (step.next) targets.push({ target: step.next, flowType: "next" });

    for (const { target, flowType } of targets) {
      if (!(target in allSteps)) continue;
      edges.push({
        id: `${name}-${flowType}-${target}`,
        source: name,
        target,
        sourceHandle: flowType,
        type: "step",
        animated: true,
        data: { flowType },
        style: {
          stroke:
            flowType === "success" ? "#52c41a" : flowType === "failure" ? "#ff4d4f" : "#8b8fa3",
          strokeWidth: 2,
        },
        markerEnd: {
          type: "arrowclosed",
          color:
            flowType === "success" ? "#52c41a" : flowType === "failure" ? "#ff4d4f" : "#8b8fa3",
        },
      });
    }
  }

  return { nodes, edges };
}

export function flowToTask(
  nodes: Node<StepNodeData>[],
  edges: Edge<StepEdgeData>[],
  original: FullTask
): FullTask {
  const steps: Record<string, Step> = {};
  const common: Record<string, Step> = {};

  // Preserve original step data, update from nodes
  for (const node of nodes) {
    const key = node.data.stepName;
    const orig = original.steps[key] ?? original.common[key] ?? {};
    const step: Step = {
      ...orig,
      action: orig.action ?? node.data.action ?? "",
      description: orig.description ?? node.data.description,
      success: undefined,
      failure: undefined,
      next: undefined,
    };
    if (node.data.isCommon) {
      common[key] = step;
    } else {
      steps[key] = step;
    }
  }

  // Apply edges
  for (const edge of edges) {
    const sourceStep = steps[edge.source] ?? common[edge.source];
    if (!sourceStep) continue;
    const ft = edge.data?.flowType;
    if (ft === "success") sourceStep.success = edge.target;
    else if (ft === "failure") sourceStep.failure = edge.target;
    else if (ft === "next") sourceStep.next = edge.target;
  }

  return { ...original, steps, common };
}
