import { useState, useEffect, useCallback, useMemo, useRef, type FC } from "react";
import {
  Button, message, Modal, Space, Tag, Tooltip,
} from "antd";
import {
  ArrowLeftOutlined, ArrowRightOutlined, CameraOutlined, CodeOutlined, EditOutlined,
  FunctionOutlined, SaveOutlined,
  ReloadOutlined, SettingOutlined,
} from "@ant-design/icons";
import { useEditorStore } from "@/store/editor-store";
import { useCharacterStore } from "@/store/character-store";
import TaskList from "./components/TaskList";
import ScreenshotCropperModal from "@/pages/task-editor/components/screenshot-cropper/ScreenshotCropperModal";
import FlowEditor from "@/pages/task-editor/components/flow-editor/FlowEditor";
import VariablePanel from "@/pages/task-editor/components/variable-panel/VariablePanel";
import { useSettingsStore } from "@/store/settings-store";
import { taskToFlow, flowToTask } from "@/utils/flow-convert";
import type { FullTask, Step } from "@/types/task";
import type { StepNodeData, StepEdgeData } from "@/types/flow";
import type { Node, Edge } from "@xyflow/react";
import type { EditorCtx } from "@/types/task-editor/actions";
import { BUILTIN_VARS } from "@/types/task-editor/actions";
import { extractAllParams } from "@/utils/expression";
import LayoutBuilder from "./LayoutBuilder";
import StepPanel from "./StepPanel";
import TaskSettingsModal from "./TaskSettingsModal";

const TaskEditorPage: FC = () => {
  const editor = useEditorStore();
  const characterStore = useCharacterStore();
  const settingsStore = useSettingsStore();

  const [taskList, setTaskList] = useState<FullTask[]>([]);
  const [cropperOpen, setCropperOpen] = useState(false);
  const [flowNodes, setFlowNodes] = useState<Node<StepNodeData>[]>([]);
  const [flowEdges, setFlowEdges] = useState<Edge<StepEdgeData>[]>([]);
  const [varVisible, setVarVisible] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [varsOpen, setVarsOpen] = useState(false);
  const [drawerStep, setDrawerStep] = useState<{ name: string; isCommon: boolean } | null>(null);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [globalCommonData, setGlobalCommonData] = useState<Record<string, { action?: string; params?: Record<string, unknown> }>>({});
  const [savedPositions, setSavedPositions] = useState<Record<string, { x: number; y: number }>>({});
  const [refreshKey, setRefreshKey] = useState(0);
  const [clipboardHasData, setClipboardHasData] = useState(false);

  const loadTaskList = useCallback(async () => {
    try {
      const raw = await window.pywebview?.api.emit("API:SCRIPT:LOAD:LIST");
      if (!raw) return;
      const fulls: FullTask[] = [];
      for (const t of raw) {
        const full = await window.pywebview?.api.emit("API:TASK:LOAD:FULL", t.id);
        if (full) fulls.push(full);
      }
      setTaskList(fulls);
    } catch { /* */ }
  }, []);

  /** 刷新所有磁盘数据（不覆盖当前编辑内容） */
  const handleRefresh = useCallback(async () => {
    // 清空后端公共步骤缓存，强制下次执行时重新读磁盘
    window.pywebview?.api.emit("API:COMMON:CACHE:CLEAR").catch(() => {});
    // 刷新全局公共步骤
    window.pywebview?.api.emit("API:AUTOCOMPLETE:COMMON:STEPS")
      .then((data: Record<string, { action?: string; params?: Record<string, unknown> }>) => {
        if (data && typeof data === "object" && !Array.isArray(data)) setGlobalCommonData(data);
      })
      .catch(() => {});
    // 刷新任务列表
    await loadTaskList();
    // 通知子组件刷新（模板列表等）
    setRefreshKey((k) => k + 1);
  }, [loadTaskList]);

  const configKeys = useMemo(() => Object.keys(settingsStore.values ?? {}), [settingsStore.values]);

  // Three separate step-name sources, merged only at point of use
  const taskStepNames = useMemo(() => Object.keys(editor.currentTask?.steps ?? {}), [editor.currentTask?.steps]);
  const taskCommonNames = useMemo(() => Object.keys(editor.currentTask?.common ?? {}), [editor.currentTask?.common]);

  const allStepNames = useMemo(() => {
    const owned = new Set([...taskStepNames, ...taskCommonNames]);
    return [...taskStepNames, ...taskCommonNames, ...Object.keys(globalCommonData).filter((n) => !owned.has(n))];
  }, [taskStepNames, taskCommonNames, globalCommonData]);

  const setVarOptions = useMemo(() => {
    const names = new Set<string>();
    const taskVals = editor.currentTask?.values ?? {};
    const collect = (steps: Record<string, Step>) => {
      for (const step of Object.values(steps))
        for (const v of step.set ?? []) {
          if (!v.name) continue;
          const bare = v.name.replace(/^\{|\}$/g, "");
          if (bare in taskVals) continue;
          names.add(bare);
        }
    };
    if (editor.currentTask) {
      collect(editor.currentTask.steps ?? {});
      collect(editor.currentTask.common ?? {});
    }
    return Array.from(names);
  }, [editor.currentTask]);

  const taskValueKeys = useMemo(() => {
    const keys = new Set(Object.keys(editor.currentTask?.values ?? {}).map(k => k.replace(/^\{|\}$/g, "")));
    // also include variable names extracted from steps' set fields — they write to the same variables dict
    for (const step of Object.values(editor.currentTask?.steps ?? {}))
      for (const v of (step as Step).set ?? []) if (v.name) keys.add(v.name.replace(/^\{|\}$/g, ""));
    for (const step of Object.values(editor.currentTask?.common ?? {}))
      for (const v of (step as Step).set ?? []) if (v.name) keys.add(v.name.replace(/^\{|\}$/g, ""));
    return Array.from(keys);
  }, [editor.currentTask?.values, editor.currentTask?.steps, editor.currentTask?.common]);

  const builtinVars = BUILTIN_VARS;
  const configVars = useMemo(() =>
    configKeys.map((k) => ({ value: `{CONFIG.${k}}`, label: `{CONFIG.${k}}` })),
    [configKeys]);
  const taskValueVars = useMemo(() =>
    taskValueKeys.map((k) => ({ value: `{${k}}`, label: `{${k}}` })),
    [taskValueKeys]);

  const makeStepOpts = (names: string[], source: Record<string, Step>, _suffix: string) =>
    names.map((k) => {
      const s = source[k];
      return { value: k, label: s?.description ? `${k} — ${s.description}` : k };
    });
  const taskSteps = useMemo(() =>
    makeStepOpts(taskStepNames, editor.currentTask?.steps ?? {}, "任务步骤"),
    [taskStepNames, editor.currentTask?.steps]);
  const taskCommonSteps = useMemo(() =>
    makeStepOpts(taskCommonNames, editor.currentTask?.common ?? {}, "任务公共步骤"),
    [taskCommonNames, editor.currentTask?.common]);
  const globalCommonSteps = useMemo(() =>
    makeStepOpts(
      Object.keys(globalCommonData).filter((n) => !taskStepNames.includes(n) && !taskCommonNames.includes(n)),
      globalCommonData,
      "全局公共步骤"
    ),
    [globalCommonData, taskStepNames, taskCommonNames]);

  /** Full step data (global + task + task-common) — needed by recursive param extraction */
  const allStepsData = { ...globalCommonData, ...editor.currentTask?.steps, ...editor.currentTask?.common };

  /** Extract {参数名:默认值} from each step via recursive transitive scan
   *  (prefix/postfix/failure_extra/success_extra + next/success/failure chains) */
  const stepParamsMap = (() => {
    const m: Record<string, Record<string, unknown>> = {};
    const taskStepNames = [...Object.keys(editor.currentTask?.steps ?? {}), ...Object.keys(editor.currentTask?.common ?? {})];
    for (const name of taskStepNames) {
      const params = extractAllParams(name, allStepsData);
      if (Object.keys(params).length > 0) m[name] = params;
    }
    return m;
  })();

  const ctx: EditorCtx = {
    stepKeys: allStepNames,
    builtinVars, configVars, taskValueVars,
    taskSteps, taskCommonSteps, globalCommonSteps,
    stepParamsMap,
    allStepsData,
    refreshKey,
    hwnd: characterStore.selectedHwnd ?? '',
    taskName: editor.currentTask?.name, version: editor.currentTask?.version,
    values: editor.currentTask?.values ?? {},
    valueTypes: editor.currentTask?.valueTypes ?? {},
    layout: editor.currentTask?.layout ?? [],
  };

  const drawerData = drawerStep && editor.currentTask
    ? (editor.currentTask[drawerStep.isCommon ? "common" : "steps"] as Record<string, Step>)?.[drawerStep.name] : null;

  const isEditing = !!editor.currentTask;

  const restorePromptedRef = useRef(false);
  const initRef = useRef(false);

  // effects
  useEffect(() => {
    if (!restorePromptedRef.current && editor.currentTask) {
      restorePromptedRef.current = true;
      Modal.confirm({
        title: "检测到未保存的草稿",
        content: `任务「${editor.currentTask.name}」有未保存的修改，是否恢复？`,
        okText: "恢复", cancelText: "放弃",
        onOk: async () => {
          if (!editor.currentTask) return;
          initRef.current = true;
          const positions = await window.pywebview?.api.emit("API:TASK:LOAD:POSITIONS", editor.currentTask.id).catch(() => ({})) ?? {};
          setSavedPositions(positions);
          requestAnimationFrame(() => {
            const { nodes, edges } = taskToFlow(editor.currentTask!, positions);
            setFlowNodes(nodes); setFlowEdges(edges);
            setTimeout(() => { initRef.current = false; }, 200);
          });
        },
        onCancel: () => editor.discardDraft(),
      });
    }
    loadTaskList();
    window.pywebview?.api.emit("API:AUTOCOMPLETE:COMMON:STEPS")
      .then((data: Record<string, { action?: string; params?: Record<string, unknown> }>) => {
        if (data && typeof data === "object" && !Array.isArray(data)) setGlobalCommonData(data);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const h = (e: BeforeUnloadEvent) => { if (editor.isDirty) { e.preventDefault(); e.returnValue = ""; } };
    window.addEventListener("beforeunload", h);
    return () => window.removeEventListener("beforeunload", h);
  }, [editor.isDirty]);

  // handlers
  const openTask = async (task: FullTask) => {
    initRef.current = true;
    await editor.loadTask(task.id);
    const positions = await window.pywebview?.api.emit("API:TASK:LOAD:POSITIONS", task.id).catch(() => ({})) ?? {};
    setSavedPositions(positions);
    requestAnimationFrame(() => {
      const current = useEditorStore.getState().currentTask;
      const { nodes, edges } = taskToFlow(current ?? task, positions);
      setFlowNodes(nodes); setFlowEdges(edges);
      // Unlock after ReactFlow finishes processing the initial nodes
      setTimeout(() => { initRef.current = false; }, 200);
    });
  };

  const closeTask = () => {
    if (editor.isDirty) {
      Modal.confirm({
        title: "有未保存的修改", okText: "保存并关闭", cancelText: "不保存",
        onOk: async () => { await editor.saveTask(); editor.discardDraft(); },
        onCancel: () => editor.discardDraft(),
      });
    } else editor.discardDraft();
  };

  // ── Copy / Paste step ──

  const handleCopyCurrentStep = useCallback(async () => {
    if (!drawerStep || !editor.currentTask) return;
    const steps = { ...editor.currentTask.steps, ...editor.currentTask.common };
    const step = steps[drawerStep.name];
    if (!step) return;
    try {
      const json = JSON.stringify({ _type: "elfStep", name: drawerStep.name, ...step });
      await navigator.clipboard.writeText(json);
      setClipboardHasData(true);
      message.success("已复制到剪贴板");
    } catch { message.error("复制失败"); }
  }, [drawerStep, editor.currentTask]);

  const handlePasteStep = useCallback(async (x: number, y: number) => {
    if (!editor.currentTask) return;
    try {
      const text = await navigator.clipboard.readText();
      const data = JSON.parse(text);
      if (data._type !== "elfStep") { message.warning("剪贴板中没有有效的步骤数据"); return; }
      const { _type, name: _oldName, ...stepData } = data;

      // Auto-rename to avoid collision
      const existing = new Set([...Object.keys(editor.currentTask.steps), ...Object.keys(editor.currentTask.common)]);
      let newName = _oldName ?? "步骤";
      if (existing.has(newName)) {
        newName = `${newName}_副本`;
        let n = 2;
        while (existing.has(newName)) { newName = `${_oldName}_副本${n}`; n++; }
      }

      editor.addStep(newName, false);
      editor.updateStep(newName, stepData as Step, false);
      setFlowNodes((prev) => [...prev, {
        id: newName, type: "stepNode", position: { x: x - 80, y: y - 20 },
        data: { stepName: newName, action: (stepData as Step).action ?? "", isCommon: false, isStart: false },
      }]);
      message.success(`已粘贴: ${newName}`);
    } catch { message.warning("剪贴板中没有有效的步骤数据"); }
  }, [editor.currentTask, editor.addStep, editor.updateStep]);

  const handleSave = async () => {
    if (editor.currentTask) {
      const updated = flowToTask(flowNodes, flowEdges, editor.currentTask);
      useEditorStore.setState({ currentTask: updated });
    }
    await editor.saveTask();
    if (editor.currentTask) {
      const positions: Record<string, { x: number; y: number }> = {};
      for (const n of flowNodes) positions[n.id] = n.position;
      setSavedPositions(positions);
      window.pywebview?.api.emit("API:TASK:SAVE:POSITIONS", editor.currentTask.id, positions).catch(() => {});
    }
    loadTaskList();
    message.success("保存成功");
  };
  const handleSaveRef = useRef(handleSave);
  handleSaveRef.current = handleSave;

  const drawerStepRef = useRef(drawerStep);
  drawerStepRef.current = drawerStep;

  const clipboardHasDataRef = useRef(clipboardHasData);
  clipboardHasDataRef.current = clipboardHasData;
  const handleCopyCurrentStepRef = useRef(handleCopyCurrentStep);
  handleCopyCurrentStepRef.current = handleCopyCurrentStep;
  const handlePasteStepRef = useRef(handlePasteStep);
  handlePasteStepRef.current = handlePasteStep;

  // Temporal (undo/redo) subscription
  const syncFlowFromTask = useCallback(() => {
    const task = useEditorStore.getState().currentTask;
    if (!task) return;
    requestAnimationFrame(() => {
      const { nodes, edges } = taskToFlow(task, savedPositions);
      setFlowNodes(nodes); setFlowEdges(edges);
    });
  }, [savedPositions]);

  useEffect(() => {
    const unsub = useEditorStore.temporal.subscribe((s) => {
      setCanUndo(s.pastStates.length > 0);
      setCanRedo(s.futureStates.length > 0);
    });
    return unsub;
  }, []);

  useEffect(() => {
    if (!isEditing) return;
    const h = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "s") { e.preventDefault(); handleSaveRef.current(); }
      if ((e.ctrlKey || e.metaKey) && e.key === "z") { e.preventDefault(); useEditorStore.temporal.getState().undo(); syncFlowFromTask(); }
      if ((e.ctrlKey || e.metaKey) && e.key === "y") { e.preventDefault(); useEditorStore.temporal.getState().redo(); syncFlowFromTask(); }
      if ((e.ctrlKey || e.metaKey) && e.key === "c") {
        if (drawerStepRef.current && document.activeElement?.closest(".react-flow")) { e.preventDefault(); handleCopyCurrentStepRef.current(); }
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "v") {
        if (clipboardHasDataRef.current) {
          const tag = document.activeElement?.tagName?.toLowerCase();
          const isInput = tag === "input" || tag === "textarea" || tag === "select" || document.activeElement?.getAttribute("contenteditable") === "true";
          if (isInput) return;
          e.preventDefault();
          const rfEl = document.querySelector(".react-flow__viewport");
          if (rfEl) {
            const rect = rfEl.getBoundingClientRect();
            handlePasteStepRef.current(rect.width / 2, rect.height / 2);
          }
        }
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [isEditing]);

  // 抽屉步骤被外部删除（undo 等）时自动关闭
  useEffect(() => {
    if (!drawerStep || !editor.currentTask) return;
    const steps = editor.currentTask[drawerStep.isCommon ? "common" : "steps"] as Record<string, Step> | undefined;
    if (!steps?.[drawerStep.name]) {
      setDrawerStep(null);
    }
  }, [editor.currentTask, drawerStep]);

  if (!isEditing) {
    return (
      <TaskList
        taskList={taskList}
        onOpenTask={openTask}
        onCreateTask={async (name, version, author, description) => {
          if (!name.trim() || !version.trim()) { message.error("名称和版本不能为空"); return; }
          try {
            await editor.createTask(name.trim(), version.trim(), author.trim(), description);
            message.success("任务创建成功"); loadTaskList();
            const task = useEditorStore.getState().currentTask;
            if (task) {
              requestAnimationFrame(() => {
                const { nodes, edges } = taskToFlow(task);
                setFlowNodes(nodes); setFlowEdges(edges);
              });
            }
          } catch (e: unknown) { message.error(e instanceof Error ? e.message : "创建失败"); }
        }}
      />
    );
  }

  return (
    <div className="page-container !p-0 overflow-hidden">
      <div className="page-header gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Button type="text" icon={<ArrowLeftOutlined />} onClick={closeTask} className="!text-[#6b7280] hover:!text-[#1a1a2e]">返回</Button>
          <div className="w-px h-5 bg-[#e5e7eb]" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#eef2ff] flex items-center justify-center">
              <CodeOutlined className="text-sm text-[#1677ff]" /></div>
            <span className="text-sm font-bold text-[#1a1a2e]">{editor.currentTask!.name}</span>
            <Tag color="blue" className="m-0 text-[11px]">v{editor.currentTask!.version}</Tag>
            {editor.isDirty && <Tag color="orange" className="m-0 text-[11px]">已修改</Tag>}
          </div>
          <div className="w-px h-5 bg-[#e5e7eb] mx-1" />
          <div className="flex items-center gap-0.5">
            <Tooltip title="撤销 Ctrl+Z"><Button size="small" type="text" icon={<ArrowLeftOutlined />} disabled={!canUndo}
              onClick={() => { useEditorStore.temporal.getState().undo(); syncFlowFromTask(); }} /></Tooltip>
            <Tooltip title="重做 Ctrl+Y"><Button size="small" type="text" icon={<ArrowRightOutlined />} disabled={!canRedo}
              onClick={() => { useEditorStore.temporal.getState().redo(); syncFlowFromTask(); }} /></Tooltip>
          </div>
          <div className="w-px h-5 bg-[#e5e7eb] mx-1" />
          <Button size="small" icon={<SettingOutlined />} onClick={() => setSettingsOpen(true)}>设置</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => setVarsOpen(true)}>变量编辑</Button>
          <Button size="small" type={varVisible ? "primary" : "text"} icon={<FunctionOutlined />} onClick={() => setVarVisible(!varVisible)}>变量参考</Button>
        </div>
        <Space size="small">
          <Button icon={<CameraOutlined />} disabled={!characterStore.selectedHwnd} onClick={() => setCropperOpen(true)}>截图模板</Button>
          <Button type="primary" icon={<SaveOutlined />} disabled={!editor.isDirty} onClick={handleSave}>
            保存 <span className="text-[10px] opacity-60 ml-0.5">Ctrl+S</span></Button>
          <Tooltip title="从磁盘重新加载数据"><Button icon={<ReloadOutlined />} onClick={handleRefresh} /></Tooltip>
        </Space>
      </div>

      <div className="flex flex-1 min-h-0">
        <div className="flex-1 min-h-0 bg-white">
          <FlowEditor task={editor.currentTask!} nodes={flowNodes} edges={flowEdges}
            onNodesChange={(ns) => { setFlowNodes(ns); if (!initRef.current) editor.setDirty(true); }}
            onEdgesChange={(es) => { setFlowEdges(es); if (!initRef.current) editor.setDirty(true); }}
            onNodesDelete={(ids) => {
              ids.forEach((id) => {
                const isCommon = id in (editor.currentTask?.common ?? {});
                editor.removeStep(id, isCommon);
              });
              if (drawerStep && ids.includes(drawerStep.name)) setDrawerStep(null);
            }}
            onNodeClick={(nodeId) => setDrawerStep({ name: nodeId, isCommon: nodeId in (editor.currentTask?.common ?? {}) })}
            onCreateStep={(x, y, isCommon) => {
              const name = `步骤_${Date.now()}`;
              editor.addStep(name, isCommon);
              setFlowNodes([...flowNodes, { id: name, type: "stepNode", position: { x: x - 80, y: y - 20 }, data: { stepName: name, action: "", isCommon, isStart: false } }]);
            }} />
        </div>
        <div className={`shrink-0 border-l border-[#e8eaed] bg-white flex flex-col transition-all duration-300 ease-in-out overflow-hidden ${drawerStep ? "w-[440px]" : "w-0 border-l-0"}`}>
          {drawerStep && drawerData && (
            <StepPanel stepName={drawerStep.name} step={drawerData} isCommon={drawerStep.isCommon} ctx={ctx}
              onClose={() => setDrawerStep(null)}
              onRename={(nn) => {
                const oldName = drawerStep.name;
                editor.renameStep(oldName, nn, drawerStep.isCommon);
                setDrawerStep({ name: nn, isCommon: drawerStep.isCommon });
                setFlowNodes((prev) => {
                  const positions: Record<string, { x: number; y: number }> = {};
                  for (const n of prev) positions[n.id] = { ...n.position };
                  if (positions[oldName]) { positions[nn] = positions[oldName]; delete positions[oldName]; }
                  setSavedPositions((sp) => ({ ...sp, ...positions }));
                  const task = useEditorStore.getState().currentTask;
                  if (!task) return prev;
                  const { nodes, edges } = taskToFlow(task, positions);
                  setFlowEdges(edges);
                  return nodes;
                });
              }}
              onUpdate={(field, value) => {
                if (!editor.currentTask) return;
                const key = drawerStep.isCommon ? "common" : "steps";
                editor.updateStep(drawerStep.name, { ...useEditorStore.getState().currentTask![key][drawerStep.name], [field]: value }, drawerStep.isCommon);
                if (field === "action" || field === "description") {
                  setFlowNodes((prev) => prev.map((n) =>
                    n.id === drawerStep.name ? { ...n, data: { ...n.data, [field]: value } } : n
                  ));
                }
              }}
              onDelete={() => {
                const name = drawerStep.name;
                editor.removeStep(name, drawerStep.isCommon);
                setDrawerStep(null);
                setFlowNodes((prev) => prev.filter((n) => n.id !== name));
                setFlowEdges((prev) => prev.filter((e) => e.source !== name && e.target !== name));
              }}
              onCopy={handleCopyCurrentStep} />
          )}
        </div>
        <VariablePanel taskValues={editor.currentTask?.values ?? {}} configKeys={configKeys}
          stepNames={allStepNames} setVariables={setVarOptions}
          visible={varVisible} onToggle={() => setVarVisible(false)} />
      </div>

      <Modal title="变量与布局" open={varsOpen} onCancel={() => setVarsOpen(false)}
        footer={null} width={900} destroyOnClose>
        {editor.currentTask && (
          <LayoutBuilder
            initialLayout={editor.currentTask.layout ?? []}
            initialValues={editor.currentTask.values ?? {}}
            initialValueTypes={editor.currentTask.valueTypes ?? {}}
            onCancel={() => setVarsOpen(false)}
            onConfirm={(newLayout, newValues, newValueTypes) => {
              useEditorStore.setState({
                currentTask: { ...editor.currentTask!, layout: newLayout, values: newValues, valueTypes: newValueTypes },
                isDirty: true,
              });
              setVarsOpen(false);
            }}
          />
        )}
      </Modal>

      {editor.currentTask && (
        <TaskSettingsModal
          open={settingsOpen}
          task={editor.currentTask}
          stepNames={allStepNames}
          onClose={() => setSettingsOpen(false)}
        />
      )}
      {characterStore.selectedHwnd && (
        <ScreenshotCropperModal open={cropperOpen} hwnd={characterStore.selectedHwnd}
          taskName={editor.currentTask?.name} version={editor.currentTask?.version}
          onClose={() => setCropperOpen(false)} onSaved={() => {}} />)}
    </div>
  );
};

export default TaskEditorPage;
