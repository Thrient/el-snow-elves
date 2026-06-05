import { useState, useMemo, useCallback, useRef, type FC } from "react";
import {
  ReactFlow, Background, Controls,
  applyNodeChanges, applyEdgeChanges,
  type Node, type Edge, type Connection, type NodeChange, type EdgeChange,
  MarkerType, type ReactFlowInstance,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { SnippetsOutlined, SyncOutlined, StopOutlined } from "@ant-design/icons";
import StepNode from "./StepNode";
import StepEdge from "./StepEdge";
import type { StepNodeData, StepEdgeData } from "@/types/flow";
import type { Step } from "@/types/task";

type FullTaskLike = { id: string; name: string; steps: Record<string, Step>; common: Record<string, Step>; start: string; };

interface Props {
  task: FullTaskLike;
  nodes: Node<StepNodeData>[];
  edges: Edge<StepEdgeData>[];
  onNodesChange: (nodes: Node<StepNodeData>[]) => void;
  onEdgesChange: (edges: Edge<StepEdgeData>[]) => void;
  onNodeClick: (nodeId: string) => void;
  onCreateStep: (x: number, y: number, isCommon: boolean) => void;
  onNodesDelete?: (ids: string[]) => void;
  clipboardHasData?: boolean;
  onPasteStep?: (x: number, y: number) => void;
  loopSteps?: string[];
  onToggleLoop?: (stepName: string) => void;
}

const nodeTypes = { stepNode: StepNode };
const edgeTypes = { step: StepEdge };

const FlowEditor: FC<Props> = ({
  nodes, edges, onNodesChange, onEdgesChange, onNodeClick, onCreateStep, onNodesDelete,
  clipboardHasData, onPasteStep,
  loopSteps = [], onToggleLoop,
}) => {
  const [menu, setMenu] = useState<{ x: number; y: number; type: "canvas" | "node"; nodeId?: string } | null>(null);
  const rfRef = useRef<HTMLDivElement>(null);
  const rfInstance = useRef<ReactFlowInstance<Node<StepNodeData>, Edge<StepEdgeData>>>(null);

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => { onNodesChange(applyNodeChanges(changes, nodes) as unknown as Node<StepNodeData>[]); },
    [nodes, onNodesChange],
  );
  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => { onEdgesChange(applyEdgeChanges(changes, edges) as unknown as Edge<StepEdgeData>[]); },
    [edges, onEdgesChange],
  );
  const handleConnect = useCallback(
    (conn: Connection) => {
      if (!conn.source || !conn.target) return;
      const ft = (conn.sourceHandle ?? "next") as "success" | "failure" | "next";
      const filtered = edges.filter((e) => !(e.source === conn.source && e.data?.flowType === ft));
      const newEdge: Edge<StepEdgeData> = {
        id: `${conn.source}-${ft}-${conn.target}`, source: conn.source, target: conn.target,
        sourceHandle: conn.sourceHandle, targetHandle: conn.targetHandle, type: "step", animated: true, data: { flowType: ft },
        style: { stroke: ft === "success" ? "#52c41a" : ft === "failure" ? "#ff4d4f" : "#8b8fa3", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed },
      };
      filtered.push(newEdge);
      onEdgesChange(filtered);
    },
    [edges, onEdgesChange],
  );

  const defaultEdgeOptions = useMemo(() => ({
    type: "step" as const,
    style: { stroke: "#8b8fa3", strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed as const },
  }), []);

  const handlePaneContextMenu = useCallback((e: React.MouseEvent | MouseEvent) => {
    if ("preventDefault" in e) e.preventDefault();
    if (!rfRef.current) return;
    const rect = rfRef.current.getBoundingClientRect();
    setMenu({ x: e.clientX - rect.left, y: e.clientY - rect.top, type: "canvas" });
  }, []);

  const handleNodeContextMenu = useCallback(
    (e: React.MouseEvent | MouseEvent, node: Node<StepNodeData>) => {
      if ("preventDefault" in e) e.preventDefault();
      if (!rfRef.current) return;
      const rect = rfRef.current.getBoundingClientRect();
      setMenu({ x: e.clientX - rect.left, y: e.clientY - rect.top, type: "node", nodeId: node.id });
    },
    [],
  );

  const handleCreateStep = (isCommon: boolean) => {
    if (!menu || !rfInstance.current || !rfRef.current) return;
    const rect = rfRef.current.getBoundingClientRect();
    const pos = rfInstance.current.screenToFlowPosition({ x: menu.x + rect.left, y: menu.y + rect.top });
    onCreateStep(pos.x, pos.y, isCommon);
    setMenu(null);
  };

  const handlePasteAt = () => {
    if (!menu || !rfInstance.current || !rfRef.current) return;
    const rect = rfRef.current.getBoundingClientRect();
    const pos = rfInstance.current.screenToFlowPosition({ x: menu.x + rect.left, y: menu.y + rect.top });
    onPasteStep?.(pos.x, pos.y);
    setMenu(null);
  };

  return (
    <div ref={rfRef} className="w-full h-full relative" style={{ zoom: "calc(1 / var(--zoom))" }}>
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={handleNodesChange} onEdgesChange={handleEdgesChange}
        onConnect={handleConnect}
        onNodeClick={(_, node) => onNodeClick(node.id)}
        onPaneContextMenu={handlePaneContextMenu}
        onNodeContextMenu={(e, node) => handleNodeContextMenu(e, node as Node<StepNodeData>)}
        onInit={(instance) => { rfInstance.current = instance; }}
        nodeTypes={nodeTypes as any} edgeTypes={edgeTypes as any}
        defaultEdgeOptions={defaultEdgeOptions}
        deleteKeyCode={["Backspace", "Delete"]}
        onNodesDelete={(deleted) => onNodesDelete?.(deleted.map((n) => n.id))}
        fitView panOnDrag selectNodesOnDrag nodesDraggable nodesConnectable elementsSelectable
        attributionPosition="bottom-left"
      >
        <Background /><Controls />
      </ReactFlow>

      {/* Context menu */}
      {menu && (
        <>
          <div className="fixed inset-0 z-50" onClick={() => setMenu(null)} />
          <div className="absolute z-50 bg-white rounded-xl shadow-lg border border-[#eef0f2] py-1 min-w-[180px] overflow-hidden"
            style={{ left: menu.x, top: menu.y }}>
            {menu.type === "node" && menu.nodeId ? (
              /* ── Node right-click menu ── */
              <>
                {loopSteps.includes(menu.nodeId) ? (
                  <button
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-[#f5f7fa] transition-colors text-left border-0 bg-transparent"
                    onClick={() => {
                      onToggleLoop?.(menu.nodeId!);
                      setMenu(null);
                    }}
                  >
                    <div className="w-7 h-7 rounded-lg bg-[#f5f0ff] flex items-center justify-center shrink-0">
                      <StopOutlined className="text-[13px] text-[#722ed1]" />
                    </div>
                    <div>
                      <div className="text-[13px] font-medium text-[#1a1a2e] leading-tight">关闭循环检测</div>
                      <div className="text-[10px] text-[#8b8fa3] leading-tight">从循环列表中移除</div>
                    </div>
                  </button>
                ) : (
                  <button
                    className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-[#f5f7fa] transition-colors text-left border-0 bg-transparent"
                    onClick={() => {
                      onToggleLoop?.(menu.nodeId!);
                      setMenu(null);
                    }}
                  >
                    <div className="w-7 h-7 rounded-lg bg-[#f5f0ff] flex items-center justify-center shrink-0">
                      <SyncOutlined className="text-[13px] text-[#722ed1]" />
                    </div>
                    <div>
                      <div className="text-[13px] font-medium text-[#1a1a2e] leading-tight">开启循环检测</div>
                      <div className="text-[10px] text-[#8b8fa3] leading-tight">加入监控循环列表</div>
                    </div>
                  </button>
                )}
              </>
            ) : (
              /* ── Canvas context menu ── */
              <>
                <button className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-[#f5f7fa] transition-colors text-left border-0 bg-transparent"
                  onClick={() => handleCreateStep(false)}>
                  <div className="w-7 h-7 rounded-lg bg-[#eef2ff] flex items-center justify-center shrink-0">
                    <span className="text-[13px] text-[#1677ff]">+</span>
                  </div>
                  <div>
                    <div className="text-[13px] font-medium text-[#1a1a2e] leading-tight">普通步骤</div>
                    <div className="text-[10px] text-[#8b8fa3] leading-tight">添加一个任务步骤</div>
                  </div>
                </button>
                <button className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-[#f5f7fa] transition-colors text-left border-0 bg-transparent"
                  onClick={() => handleCreateStep(true)}>
                  <div className="w-7 h-7 rounded-lg bg-[#fff7e6] flex items-center justify-center shrink-0">
                    <span className="text-[13px] text-[#f59e0b]">+</span>
                  </div>
                  <div>
                    <div className="text-[13px] font-medium text-[#1a1a2e] leading-tight">公共步骤</div>
                    <div className="text-[10px] text-[#8b8fa3] leading-tight">覆盖全局公共步骤</div>
                  </div>
                </button>
                {clipboardHasData && (
                  <>
                    <div className="border-t border-[#f0f0f0] my-1" />
                    <button className="w-full flex items-center gap-2.5 px-4 py-2.5 hover:bg-[#f5f7fa] transition-colors text-left border-0 bg-transparent"
                      onClick={handlePasteAt}>
                      <div className="w-7 h-7 rounded-lg bg-[#f0fdf4] flex items-center justify-center shrink-0">
                        <SnippetsOutlined className="text-[13px] text-[#52c41a]" />
                      </div>
                      <div>
                        <div className="text-[13px] font-medium text-[#1a1a2e] leading-tight">粘贴步骤</div>
                        <div className="text-[10px] text-[#8b8fa3] leading-tight">将复制的步骤粘贴到此处</div>
                      </div>
                    </button>
                  </>
                )}
              </>
            )}
          </div>
        </>
      )}

    </div>
  );
};

export default FlowEditor;
