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
  totalBytes: number;
  downloadedBytes: number;
  lastSpeed: number;
  downloadDone: boolean;
  setCurrentVersion: (v: string) => void;
  setUpdate: (info: UpdateInfo) => void;
  clearUpdate: () => void;
  openCheckModal: () => void;
  closeCheckModal: () => void;
  setDownloadedBytes: (bytes: number) => void;
  startDownload: (files: number, bytes: number) => void;
  updateProgress: (file: string, completed: number, bytes: number) => void;
  finishDownload: () => void;
  cancelDownload: () => void;
}

let _speedTime = 0;
let _speedLast = 0;

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
  totalBytes: 0,
  downloadedBytes: 0,
  lastSpeed: 0,
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

  setDownloadedBytes: (bytes: number) => set((s) => {
    const now = Date.now();
    const dt = (now - (_speedTime as number)) / 1000;
    const db = bytes - (_speedLast as number);
    const speed = dt > 0.1 ? Math.round(db / dt) : s.lastSpeed;
    _speedTime = now;
    _speedLast = bytes;
    return { downloadedBytes: bytes, lastSpeed: speed };
  }),

  startDownload: (files, bytes) => {
    _speedTime = Date.now();
    _speedLast = 0;
    set({
      downloading: true,
      progress: 0,
      totalFiles: files,
      completedFiles: 0,
      totalBytes: bytes,
      downloadedBytes: 0,
      lastSpeed: 0,
      currentFile: "准备下载...",
      downloadDone: false,
    });
  },
  updateProgress: (file, completed, bytes) => set((s) => {
    const now = Date.now();
    const dt = (now - (_speedTime as number)) / 1000;
    const db = bytes - (_speedLast as number);
    const speed = dt > 0.1 ? Math.round(db / dt) : s.lastSpeed;
    _speedTime = now;
    _speedLast = bytes;
    return {
      currentFile: file,
      completedFiles: completed,
      downloadedBytes: bytes,
      lastSpeed: speed,
      progress: s.totalFiles > 0 ? Math.round((completed / s.totalFiles) * 100) : 0,
    };
  }),
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
    totalBytes: 0,
    downloadedBytes: 0,
    lastSpeed: 0,
    currentFile: "",
  }),
}));
