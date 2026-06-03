import { useCharacterStore } from "@/store/character.ts";
import { useTaskStore } from "@/store/task-store.ts";
import { useUpdateStore } from "@/store/update-store.ts";


declare global {
  interface Window {
    useCharacterStore?: typeof useCharacterStore;
    useTaskStore?: typeof useTaskStore;
    useUpdateStore?: typeof useUpdateStore;
  }
}


window.useCharacterStore = useCharacterStore
window.useTaskStore = useTaskStore
window.useUpdateStore = useUpdateStore