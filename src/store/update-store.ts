import { create } from "zustand";

export interface UpdateInfo {
  version: string;
  changelog: string | null;
  is_mandatory: boolean;
}

interface UpdateState {
  hasUpdate: boolean;
  latestVersion: string | null;
  changelog: string | null;
  isMandatory: boolean;
  checkModalOpen: boolean;
  setUpdate: (info: UpdateInfo) => void;
  clearUpdate: () => void;
  openCheckModal: () => void;
  closeCheckModal: () => void;
}

export const useUpdateStore = create<UpdateState>((set) => ({
  hasUpdate: false,
  latestVersion: null,
  changelog: null,
  isMandatory: false,
  checkModalOpen: false,
  setUpdate: (info) => set({
    hasUpdate: true,
    latestVersion: info.version,
    changelog: info.changelog,
    isMandatory: info.is_mandatory,
    checkModalOpen: true,
  }),
  clearUpdate: () => set({
    hasUpdate: false,
    latestVersion: null,
    changelog: null,
    isMandatory: false,
    checkModalOpen: false,
  }),
  openCheckModal: () => set({ checkModalOpen: true }),
  closeCheckModal: () => set({ checkModalOpen: false }),
}));
