import { create } from "zustand";

export interface Account {
  name: string;
  createdAt: number;
  type?: string;
  port?: number;
}

type State = {
  accounts: Account[];
  loading: boolean;
  loadAccounts: () => Promise<void>;
};

export const useAccountStore = create<State>((set) => ({
  accounts: [],
  loading: true,
  loadAccounts: async () => {
    try {
      const result = await window.pywebview?.api.emit("API:ACCOUNT:LIST");
      set({ accounts: (result ?? []) as Account[], loading: false });
    } catch {
      set({ loading: false });
    }
  },
}));
