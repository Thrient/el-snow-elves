import { create } from 'zustand'
import { useSettingsStore } from '@/store/settings-store'
import type { TaskBase, TaskListItem } from '@/types/task'
import type { PlanBase } from '@/types/plan'
import { getCronEngine, removeCronEngine } from '@/engine/CronEngine'
import { mergeValues } from '@/utils/mergeValues'

export type ExecuteItem = TaskBase

export interface TaskUpdateInfo {
  name: string
  hubTaskId: number
  localVersion: string
  hubVersion: string
}

type ExecuteEntry = ExecuteItem & { _uid: number }

let _executeUidCounter = 0

type Character = {
  character: string
  hwnd: string
  running: boolean
  locked: boolean
  opacity: number
  currentTask: string | null
  executeList: ExecuteEntry[]
  plans: PlanBase[]
}

type State = {
  characters: Character[]
  selectedHwnd: string | null
  taskList: TaskListItem[]
  taskLoading: boolean
  taskUpdates: TaskUpdateInfo[]
  add: (data: Omit<Character, 'executeList' | 'plans'> & { executeList: ExecuteItem[]; plans?: PlanBase[] }) => void
  remove: (hwnd: string) => void
  update: (data: Partial<Character> & { hwnd: string }) => void
  popExecute: (hwnd: string) => ExecuteItem | undefined
  setSelectedHwnd: (hwnd: string | null) => void
  pushExecute: (hwnd: string, item: ExecuteItem) => void
  pushExecuteBatch: (hwnd: string, items: ExecuteItem[]) => void
  unshiftExecute: (hwnd: string, item: ExecuteItem) => void
  removeExecute: (hwnd: string, uid: number) => void
  clearExecute: (hwnd: string) => void
  updateExecuteValues: (hwnd: string, uid: number, values: Record<string, unknown>) => void
  updateExecuteVersion: (hwnd: string, uid: number, version: string | null) => void
  updateExecuteAuthor: (hwnd: string, uid: number, author: string, version: string, values: Record<string, unknown>) => void
  reorderExecute: (hwnd: string, orderedUids: number[]) => void
  setPlans: (hwnd: string, plans: PlanBase[]) => void
  syncPlansToAllWindows: (plans: PlanBase[]) => void
  loadTasks: () => Promise<void>
  updateTaskValues: (name: string, values: Record<string, unknown>) => void
  setTaskUpdates: (updates: TaskUpdateInfo[]) => void
  dismissTaskUpdate: (name: string, hubTaskId: number) => void
}

export const useCharacterStore = create<State>((set, get) => ({
  characters: [],
  selectedHwnd: null,
  taskList: [],
  taskLoading: true,
  taskUpdates: [],
  add: (data) => {
    const plans = data.plans ?? [];
    const executeList = data.executeList;
    set((state) => ({
      characters: [
        ...state.characters,
        {
          character: data.character,
          hwnd: data.hwnd,
          running: data.running,
          locked: data.locked ?? true,
          opacity: data.opacity,
          currentTask: data.currentTask,
          plans,
          executeList: executeList.map((item) => ({
            ...item,
            author: item.author ?? "匿名作者",
            _uid: _executeUidCounter++,
          })),
        },
      ],
    }));
    // 启动计划调度器
    const eng = getCronEngine(data.hwnd, executeList);
    eng.start(plans);
  },
  update: (data: Partial<Character> & { hwnd: string }) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === data.hwnd ? { ...character, ...data } : character
      ),
    })),
  popExecute: (hwnd: string) => {
    const character = get().characters.find((c) => c.hwnd === hwnd)
    const item = character?.executeList[0]
    if (item) {
      const taskName = (item as any).taskName || item.name;
      set((state) => ({
        characters: state.characters.map((character) =>
          character.hwnd === hwnd
            ? { ...character, currentTask: taskName, executeList: character.executeList.slice(1) }
            : character
        ),
      }))
      const taskMeta = get().taskList.find((t: any) => t.name === taskName);
      const repoDefaults = (taskMeta as any)?.values ?? {};
      const settingsValues = useSettingsStore.getState().values ?? {};
      return { ...item, values: mergeValues(repoDefaults, item.values ?? {}, settingsValues) };
    }
    // 队列已空，清除当前任务名
    set((state) => ({
      characters: state.characters.map((c) =>
        c.hwnd === hwnd ? { ...c, currentTask: null } : c
      ),
    }))
    return item
  },
  remove: (hwnd: string) => {
    removeCronEngine(hwnd);
    set((state) => ({
      characters: state.characters.filter((c) => c.hwnd !== hwnd),
      selectedHwnd: state.selectedHwnd === hwnd ? null : state.selectedHwnd,
    }));
  },
  setSelectedHwnd: (hwnd: string | null) => set({ selectedHwnd: hwnd }),
  pushExecute: (hwnd: string, item: ExecuteItem & { taskName?: string; version?: string | null; debugStart?: string; debugSingle?: boolean }) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: [
                ...character.executeList,
                {
                  id: item.id,
                  name: item.name,
                  taskName: (item as any).taskName ?? item.name,
                  version: (item as any).version ?? null,
                  author: (item as any).author ?? "匿名作者",
                  values: item.values ?? {},
                  valueTypes: item.valueTypes,
                  debugStart: (item as any).debugStart,
                  debugSingle: (item as any).debugSingle ?? false,
                  _uid: _executeUidCounter++,
                },
              ],
            }
          : character
      ),
    })),
  pushExecuteBatch: (hwnd: string, items: ExecuteItem[]) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: [
                ...character.executeList,
                ...items.map((item) => ({
                  id: item.id,
                  name: item.name,
                  taskName: (item as any).taskName ?? item.name,
                  version: (item as any).version ?? null,
                  author: (item as any).author ?? "匿名作者",
                  values: item.values ?? {},
                  valueTypes: item.valueTypes,
                  debugStart: (item as any).debugStart,
                  debugSingle: (item as any).debugSingle ?? false,
                  _uid: _executeUidCounter++,
                })),
              ],
            }
          : character
      ),
    })),
  unshiftExecute: (hwnd: string, item: ExecuteItem & { taskName?: string; version?: string | null; debugStart?: string; debugSingle?: boolean }) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: [
                {
                  id: item.id,
                  name: item.name,
                  taskName: (item as any).taskName ?? item.name,
                  version: (item as any).version ?? null,
                  author: (item as any).author ?? "匿名作者",
                  values: item.values ?? {},
                  valueTypes: item.valueTypes,
                  debugStart: (item as any).debugStart,
                  debugSingle: (item as any).debugSingle ?? false,
                  _uid: _executeUidCounter++,
                },
                ...character.executeList,
              ],
            }
          : character
      ),
    })),
  removeExecute: (hwnd: string, uid: number) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: character.executeList.filter((item) => item._uid !== uid),
            }
          : character
      ),
    })),
  clearExecute: (hwnd: string) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? { ...character, executeList: [] }
          : character
      ),
    })),
  updateExecuteValues: (hwnd: string, uid: number, values: Record<string, unknown>) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: character.executeList.map((item) =>
                item._uid === uid ? { ...item, values } : item
              ),
            }
          : character
      ),
    })),
  updateExecuteVersion: (hwnd: string, uid: number, version: string | null) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: character.executeList.map((item) =>
                item._uid === uid ? { ...item, version: version as any } : item
              ),
            }
          : character
      ),
    })),
  updateExecuteAuthor: (hwnd, uid, author, version, values) =>
    set((state) => ({
      characters: state.characters.map((c) =>
        c.hwnd !== hwnd ? c : {
          ...c,
          executeList: c.executeList.map((item) =>
            item._uid !== uid ? item : {
              ...item,
              author,
              version,
              values,
            }
          ),
        }
      ),
    })),
  setPlans: (hwnd: string, plans: PlanBase[]) => {
    set((state) => ({
      characters: state.characters.map((c) =>
        c.hwnd === hwnd ? { ...c, plans } : c
      ),
    }));
    const eng = getCronEngine(hwnd, []);
    eng.start(plans);
  },
  syncPlansToAllWindows: (plans: PlanBase[]) => {
    const { characters } = get();
    for (const c of characters) {
      set((state) => ({
        characters: state.characters.map((ch) =>
          ch.hwnd === c.hwnd ? { ...ch, plans } : ch
        ),
      }));
      const eng = getCronEngine(c.hwnd, []);
      eng.start(plans);
    }
  },
  reorderExecute: (hwnd: string, orderedUids: number[]) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: orderedUids
                .map((uid) => character.executeList.find((item) => item._uid === uid))
                .filter((item): item is ExecuteEntry => item !== undefined),
            }
          : character
      ),
    })),
  loadTasks: async () => {
    try {
      const result = await window.pywebview?.api.emit("API:SCRIPT:LOAD:LIST");
      set({ taskList: (result ?? []) as TaskListItem[], taskLoading: false });
    } catch { set({ taskLoading: false }); }
  },
  setTaskUpdates: (updates: TaskUpdateInfo[]) => {
    set({ taskUpdates: updates })
  },

  dismissTaskUpdate: (name: string, hubTaskId: number) => {
    set(state => ({
      taskUpdates: state.taskUpdates.filter(
        u => !(u.name === name && u.hubTaskId === hubTaskId)
      ),
    }))
  },

  updateTaskValues: (name, values) =>
    set((state) => ({
      taskList: state.taskList.map((t) =>
        t.name === name ? { ...t, values } : t
      ),
    })),
}))
