import { create } from "zustand";
import { persist } from "zustand/middleware";
import { temporal } from "zundo";
import type { FullTask, Step } from "@/types/task";

type ViewMode = "json" | "flow";

type EditorState = {
  currentTask: FullTask | null;
  isDirty: boolean;
  loading: boolean;
  viewMode: ViewMode;

  loadTask: (taskId: string) => Promise<void>;
  saveTask: () => Promise<void>;
  createTask: (
    name: string,
    version: string,
    author: string,
    description: string
  ) => Promise<string>;
  recoverDraft: () => FullTask | null;
  discardDraft: () => void;
  setDirty: (dirty: boolean) => void;
  setViewMode: (mode: ViewMode) => void;

  renameStep: (oldName: string, newName: string, isCommon: boolean) => void;
  updateStep: (name: string, step: Step, isCommon: boolean) => void;
  addStep: (name: string, isCommon: boolean) => void;
  removeStep: (name: string, isCommon: boolean) => void;
  updateStart: (start: string) => void;
  updateMonitors: (monitors: FullTask["monitors"]) => void;
};

export const useEditorStore = create<EditorState>()(
  temporal(
    persist(
      (set, get) => ({
      currentTask: null,
      isDirty: false,
      loading: false,
      viewMode: "json",

      loadTask: async (taskId) => {
        set({ loading: true, isDirty: false });
        try {
          const task = await window.pywebview?.api.emit(
            "API:TASK:LOAD:FULL",
            taskId
          );
          set({ currentTask: task ?? null, isDirty: false, loading: false });
          useEditorStore.temporal.getState().clear();
        } catch {
          set({ loading: false, currentTask: null, isDirty: false });
        }
      },

      saveTask: async () => {
        const { currentTask } = get();
        if (!currentTask) return;
        await window.pywebview?.api.emit(
          "API:TASK:SAVE:FULL",
          currentTask.id,
          currentTask
        );
        set({ isDirty: false });
      },

      createTask: async (name, version, author, description) => {
        const taskId = await window.pywebview?.api.emit(
          "API:TASK:CREATE",
          name,
          version,
          author,
          description
        );
        await get().loadTask(taskId);
        set({ isDirty: true });
        return taskId;
      },

      recoverDraft: () => {
        // The persist middleware handles reading from localStorage automatically.
        // This is called explicitly if user confirms recovery.
        const state = get();
        return state.currentTask && state.isDirty ? state.currentTask : null;
      },

      discardDraft: () => {
        set({ currentTask: null, isDirty: false });
        // Force persist to save the cleared state
        sessionStorage.removeItem("editor-draft-v2");
        localStorage.removeItem("editor-draft-v2");
      },

      setDirty: (dirty) => set({ isDirty: dirty }),
      setViewMode: (mode) => set({ viewMode: mode }),

      renameStep: (oldName, newName, isCommon) => {
        const { currentTask } = get();
        if (!currentTask) return;
        const key = isCommon ? "common" : "steps";
        const steps = { ...currentTask[key] };
        if (!steps[oldName] || steps[newName]) return;
        steps[newName] = steps[oldName];
        delete steps[oldName];
        set({ currentTask: { ...currentTask, [key]: steps }, isDirty: true });
      },

      updateStep: (name, step, isCommon) => {
        const { currentTask } = get();
        if (!currentTask) return;
        const key = isCommon ? "common" : "steps";
        const updated = {
          ...currentTask,
          [key]: { ...currentTask[key], [name]: step },
        };
        set({ currentTask: updated, isDirty: true });
      },

      addStep: (name, isCommon) => {
        const { currentTask } = get();
        if (!currentTask) return;
        const key = isCommon ? "common" : "steps";
        if (currentTask[key][name]) return; // already exists
        const updated = {
          ...currentTask,
          [key]: {
            ...currentTask[key],
            [name]: { action: "", params: {} },
          },
        };
        set({ currentTask: updated, isDirty: true });
      },

      removeStep: (name, isCommon) => {
        const { currentTask } = get();
        if (!currentTask) return;
        const key = isCommon ? "common" : "steps";
        const newSteps = { ...currentTask[key] };
        delete newSteps[name];
        const updated = { ...currentTask, [key]: newSteps };
        set({ currentTask: updated, isDirty: true });
      },

      updateStart: (start) => {
        const { currentTask } = get();
        if (!currentTask) return;
        set({ currentTask: { ...currentTask, start }, isDirty: true });
      },

      updateMonitors: (monitors) => {
        const { currentTask } = get();
        if (!currentTask) return;
        set({ currentTask: { ...currentTask, monitors }, isDirty: true });
      },
    }),
    {
      name: "editor-draft-v2",
      partialize: (state) => state.isDirty ? { currentTask: state.currentTask } : { currentTask: null },
    }
  ),
  {
    partialize: (state: EditorState) => ({ currentTask: state.currentTask }),
    limit: 50,
  })
);
