import { BaseEdge, getSmoothStepPath, useInternalNode, Position, type Edge, type EdgeProps } from "@xyflow/react";
import type { StepEdgeData } from "@/types/flow";

const HANDLE_LEFT: Record<string, number> = {
  success: 0.20,
  failure: 0.50,
  next:    0.80,
};

export default function StepEdge({
  id,
  source,
  target,
  sourceHandleId,
  style,
  markerEnd,
}: EdgeProps<Edge<StepEdgeData>>) {
  const sourceNode = useInternalNode(source!);
  const targetNode = useInternalNode(target!);

  if (!sourceNode || !targetNode) return null;

  const sw = sourceNode.measured?.width ?? 0;
  const sh = sourceNode.measured?.height ?? 0;
  const tw = targetNode.measured?.width ?? 0;

  // Source: specific bottom handle at HANDLE_LEFT percentage
  const handleLeft = sourceHandleId ? (HANDLE_LEFT[sourceHandleId] ?? 0.5) : 0.5;
  const sourceX = sourceNode.position.x + sw * handleLeft;
  const sourceY = sourceNode.position.y + sh;

  // Target: slightly above the node's top edge so the arrow doesn't overlap
  const targetX = targetNode.position.x + tw / 2;
  const targetY = targetNode.position.y - 6;

  const [edgePath] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition: Position.Bottom,
    targetX,
    targetY,
    targetPosition: Position.Top,
  });

  return <BaseEdge id={id} path={edgePath} style={style as React.CSSProperties} markerEnd={markerEnd} />;
}
