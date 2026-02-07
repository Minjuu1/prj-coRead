import { create } from 'zustand';
import type { Document, Thread, Section } from '../types';
import type { ThreadListItem } from '../services/api';

interface User {
  userId: string;
  createdAt: string;
  documents: string[];
}

interface AppState {
  // User state
  user: User | null;
  setUser: (user: User | null) => void;

  // Document state
  document: Document | null;
  setDocument: (document: Document | null) => void;
  sections: Section[];
  setSections: (sections: Section[]) => void;

  // Thread state
  threads: ThreadListItem[];
  setThreads: (threads: ThreadListItem[]) => void;
  fullThreads: Thread[];  // Full thread data with messages
  setFullThreads: (threads: Thread[]) => void;
  addFullThread: (thread: Thread) => void;
  selectedThread: Thread | null;
  setSelectedThread: (thread: Thread | null) => void;
  selectedThreadId: string | null;
  setSelectedThreadId: (threadId: string | null) => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;

  // Actions
  reset: () => void;
}

const initialState = {
  user: null,
  document: null,
  sections: [],
  threads: [],
  fullThreads: [] as Thread[],
  selectedThread: null,
  selectedThreadId: null,
  isLoading: false,
  error: null,
};

export const useStore = create<AppState>((set) => ({
  ...initialState,

  setUser: (user) => set({ user }),

  setDocument: (document) => set({ document }),
  setSections: (sections) => set({ sections }),

  setThreads: (threads) => set({ threads }),
  setFullThreads: (fullThreads) => set({ fullThreads }),
  addFullThread: (thread) =>
    set((state) => ({
      fullThreads: [...state.fullThreads, thread],
    })),
  setSelectedThread: (selectedThread) => set({ selectedThread }),
  setSelectedThreadId: (selectedThreadId) => set({ selectedThreadId }),

  setIsLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  reset: () => set(initialState),
}));
