import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Thread, Message } from '../types'

interface ThreadStore {
  activeThreadId: string | null
  threads: Thread[]
  // 스레드별 메시지 (스레드 전환해도 각 대화 유지)
  messagesByThreadId: Record<string, Message[]>
  isStreaming: boolean

  setActiveThread: (threadId: string | null) => void
  setThreads: (threads: Thread[]) => void
  addMessage: (threadId: string, msg: Message) => void
  setStreaming: (v: boolean) => void
  clearThread: (threadId: string) => void
}

export const useThreadStore = create<ThreadStore>()(
  persist(
    (set) => ({
      activeThreadId: null,
      threads: [],
      messagesByThreadId: {},
      isStreaming: false,

      setActiveThread: (threadId) => set({ activeThreadId: threadId }),
      setThreads: (threads) => set({ threads }),
      addMessage: (threadId, msg) =>
        set((s) => ({
          messagesByThreadId: {
            ...s.messagesByThreadId,
            [threadId]: [...(s.messagesByThreadId[threadId] ?? []), msg],
          },
        })),
      setStreaming: (v) => set({ isStreaming: v }),
      clearThread: (threadId) =>
        set((s) => {
          const next = { ...s.messagesByThreadId }
          delete next[threadId]
          return { messagesByThreadId: next }
        }),
    }),
    {
      name: 'coread-thread',
      partialize: (s) => ({
        activeThreadId: s.activeThreadId,
        messagesByThreadId: s.messagesByThreadId,
      }),
    }
  )
)
