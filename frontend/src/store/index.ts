import { useCharacterStore } from "@/store/character-store";
import { useSessionStore } from "@/store/session-store";
import { useUpdateStore } from "@/store/update-store";


declare global {
  interface Window {
    useCharacterStore?: typeof useCharacterStore;
    useSessionStore?: typeof useSessionStore;
    useUpdateStore?: typeof useUpdateStore;
  }
}


window.useCharacterStore = useCharacterStore;
window.useSessionStore = useSessionStore;
window.useUpdateStore = useUpdateStore;
