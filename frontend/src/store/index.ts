import { useCharacterStore } from "@/store/character-store";
import { useSessionStore } from "@/store/session-store";
import { useUpdateStore } from "@/store/update-store";
import { useSettingsStore } from "@/store/settings-store";

declare global {
  interface Window {
    useCharacterStore?: typeof useCharacterStore;
    useSessionStore?: typeof useSessionStore;
    useUpdateStore?: typeof useUpdateStore;
    useSettingsStore?: typeof useSettingsStore;
  }
}


window.useCharacterStore = useCharacterStore;
window.useSessionStore = useSessionStore;
window.useUpdateStore = useUpdateStore;
window.useSettingsStore = useSettingsStore;
