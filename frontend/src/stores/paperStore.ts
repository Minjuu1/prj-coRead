import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ChunkSource, GrobidRect } from '../types'

interface PaperStore {
  paperId: string | null
  pdfUrl: string | null
  // 마지막 채팅 응답에서 참조한 청크 (PDF 하이라이팅용)
  activeSources: ChunkSource[]
  // 현재 선택된 스레드의 청크 위치 (PDF 연동)
  activeThreadRects: GrobidRect[] | null
  activeThreadChunkId: string | null
  setPaper: (paperId: string, pdfUrl: string) => void
  clearPaper: () => void
  setActiveSources: (sources: ChunkSource[]) => void
  clearActiveSources: () => void
  setActiveThreadHighlight: (chunkId: string, rects: GrobidRect[]) => void
  clearActiveThreadHighlight: () => void
}

export const usePaperStore = create<PaperStore>()(
  persist(
    (set) => ({
      paperId: null,
      pdfUrl: null,
      activeSources: [],
      activeThreadRects: null,
      activeThreadChunkId: null,
      setPaper: (paperId, pdfUrl) => set({ paperId, pdfUrl }),
      clearPaper: () => set({ paperId: null, pdfUrl: null, activeSources: [], activeThreadRects: null, activeThreadChunkId: null }),
      setActiveSources: (sources) => set({ activeSources: sources }),
      clearActiveSources: () => set({ activeSources: [] }),
      setActiveThreadHighlight: (chunkId, rects) => set({ activeThreadChunkId: chunkId, activeThreadRects: rects }),
      clearActiveThreadHighlight: () => set({ activeThreadChunkId: null, activeThreadRects: null }),
    }),
    { name: 'coread-paper' }
  )
)
