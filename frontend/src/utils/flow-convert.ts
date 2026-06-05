import type { Node, Edge } from "@xyflow/react";
import type { FullTask, Step } from "@/types/task";
import type { StepNodeData, StepEdgeData } from "@/types/flow";

const STEP_NODE = "stepNode";

type FlowType = "success" | "failure" | "next";
const FLOW_TYPES: FlowType[] = ["success", "failure", "next"];

export type { FlowType };

function edgeColor(flowType: string): string {
  return flowType === "success" ? "#52c41a" : flowType === "failure" ? "#ff4d4f" : "#8b8fa3";
}

function collectTargets(step: Step): { target: string; flowType: FlowType }[] {
  const targets: { target: string; flowType: FlowType }[] = [];
  for (const ft of FLOW_TYPES) {
    const t = step[ft] as string | undefined;
    if (t) targets.push({ target: t, flowType: ft });
  }
  return targets;
}

export function taskToFlow(
  task: FullTask,
  savedPositions?: Record<string, { x: number; y: number }>,
  loopSteps?: string[],
): {
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
        isMonitorLoop: loopSteps?.includes(name),
      },
    });
  });

  for (const [name, step] of Object.entries(allSteps)) {
    for (const { target, flowType } of collectTargets(step)) {
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
          stroke: edgeColor(flowType),
          strokeWidth: 2,
        },
        markerEnd: {
          type: "arrowclosed",
          color: edgeColor(flowType),
        },
      });
    }
  }

  return { nodes, edges };
}

export function flowToTask(
  nodes: Node<StepNodeData>[],
  edges: Edge<StepEdgeData>[],
  original: FullTask,
): FullTask {
  const steps: Record<string, Step> = {};
  const common: Record<string, Step> = {};

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

  for (const edge of edges) {
    const sourceStep = steps[edge.source] ?? common[edge.source];
    if (sourceStep && edge.data?.flowType) {
      (sourceStep as Record<string, unknown>)[edge.data.flowType] = edge.target;
    }
  }

  return { ...original, steps, common };
}
