import { create } from 'zustand'
import { useSettingsStore } from '@/store/settings-store'
import type { TaskBase } from '@/types/task'
import type { PlanBase } from '@/types/plan'
import { getCronEngine, removeCronEngine } from '@/engine/CronEngine'

export type ExecuteItem = TaskBase

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
  add: (data: Omit<Character, 'executeList' | 'plans'> & { executeList: ExecuteItem[]; plans?: PlanBase[] }) => void
  remove: (hwnd: string) => void
  update: (data: Partial<Character> & { hwnd: string }) => void
  popExecute: (hwnd: string) => ExecuteItem | undefined
  setSelectedHwnd: (hwnd: string | null) => void
  pushExecute: (hwnd: string, item: ExecuteItem) => void
  unshiftExecute: (hwnd: string, item: ExecuteItem) => void
  removeExecute: (hwnd: string, uid: number) => void
  clearExecute: (hwnd: string) => void
  updateExecuteValues: (hwnd: string, uid: number, values: Record<string, unknown>) => void
  reorderExecute: (hwnd: string, orderedUids: number[]) => void
  setPlans: (hwnd: string, plans: PlanBase[]) => void
  syncPlansToAllWindows: (plans: PlanBase[]) => void
}

export const useCharacterStore = create<State>((set, get) => ({
  characters: [],
  selectedHwnd: null,
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
      set((state) => ({
        characters: state.characters.map((character) =>
          character.hwnd === hwnd
            ? { ...character, currentTask: item.name, executeList: character.executeList.slice(1) }
            : character
        ),
      }))
      const settingsValues = useSettingsStore.getState().values ?? {}
      return { ...item, values: { ...item.values, CONFIG: settingsValues } }
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
  pushExecute: (hwnd: string, item: ExecuteItem) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: [
                ...character.executeList,
                { ...item, _uid: _executeUidCounter++ },
              ],
            }
          : character
      ),
    })),
  unshiftExecute: (hwnd: string, item: ExecuteItem) =>
    set((state) => ({
      characters: state.characters.map((character) =>
        character.hwnd === hwnd
          ? {
              ...character,
              executeList: [
                { ...item, _uid: _executeUidCounter++ },
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
}))
