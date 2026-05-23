import { create } from "zustand";

export interface UpdateInfo {
  version: string;
  changelog: string | null;
  is_mandatory: boolean;
}

interface UpdateState {
  hasUpdate: boolean;
  latestVersion: string | null;
  currentVersion: string;
  changelog: string | null;
  isMandatory: boolean;
  checkModalOpen: boolean;
  downloading: boolean;
  progress: number;
  currentFile: string;
  totalFiles: number;
  completedFiles: number;
  downloadDone: boolean;
  setCurrentVersion: (v: string) => void;
  setUpdate: (info: UpdateInfo) => void;
  clearUpdate: () => void;
  openCheckModal: () => void;
  closeCheckModal: () => void;
  startDownload: (total: number) => void;
  updateProgress: (file: string, completed: number) => void;
  finishDownload: () => void;
  cancelDownload: () => void;
}

export const useUpdateStore = create<UpdateState>((set) => ({
  hasUpdate: false,
  latestVersion: null,
  currentVersion: "?.?.?",
  changelog: null,
  isMandatory: false,
  checkModalOpen: false,
  downloading: false,
  progress: 0,
  currentFile: "",
  totalFiles: 0,
  completedFiles: 0,
  downloadDone: false,

  setCurrentVersion: (v) => set({ currentVersion: v }),

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

  startDownload: (total) => set({
    downloading: true,
    progress: 0,
    totalFiles: total,
    completedFiles: 0,
    currentFile: "准备下载...",
    downloadDone: false,
  }),
  updateProgress: (file, completed) => set((s) => ({
    currentFile: file,
    completedFiles: completed,
    progress: s.totalFiles > 0 ? Math.round((completed / s.totalFiles) * 100) : 0,
  })),
  finishDownload: () => set({
    downloading: false,
    downloadDone: true,
    progress: 100,
  }),
  cancelDownload: () => set({
    downloading: false,
    downloadDone: false,
    progress: 0,
    totalFiles: 0,
    completedFiles: 0,
    currentFile: "",
  }),
}));
