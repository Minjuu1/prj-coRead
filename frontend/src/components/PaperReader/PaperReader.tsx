import { useRef, useState, useCallback, useMemo, useEffect } from 'react'
import {
  PdfLoader, PdfHighlighter, TextHighlight, MonitoredHighlightContainer,
  useHighlightContainerContext,
} from 'react-pdf-highlighter-extended'
import type { Highlight, PdfHighlighterUtils } from 'react-pdf-highlighter-extended'
import 'pdfjs-dist/web/pdf_viewer.css'
import { usePaperStore } from '../../stores/paperStore'
import { useThreadStore } from '../../stores/threadStore'
import type { GrobidRect } from '../../types'

interface PaperReaderProps {
  pdfUrl: string
  threadPanelOpen?: boolean
  onToggleThreadPanel?: () => void
  onReprocess?: () => void
  reprocessing?: boolean
}

const workerSrc =
  'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs'

const ZOOM_STEPS = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0]

function grobidToHighlightRect(r: GrobidRect) {
  return { x1: r.x1, y1: r.y1, x2: r.x2, y2: r.y2, width: r.width, height: r.height, pageNumber: r.page }
}

function boundingBox(rects: GrobidRect[]) {
  const x1 = Math.min(...rects.map((r) => r.x1))
  const y1 = Math.min(...rects.map((r) => r.y1))
  const x2 = Math.max(...rects.map((r) => r.x2))
  const y2 = Math.max(...rects.map((r) => r.y2))
  const r = rects[0]
  return { x1, y1, x2, y2, width: r.width, height: r.height, pageNumber: r.page }
}

export function PaperReader({ pdfUrl, threadPanelOpen, onToggleThreadPanel, onReprocess, reprocessing }: PaperReaderProps) {
  const highlighterUtilsRef = useRef<PdfHighlighterUtils | undefined>(undefined)
  const [scale, setScale] = useState<number>(1.0)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(0)
  const [pageInput, setPageInput] = useState('1')

  const activeSources = usePaperStore((s) => s.activeSources)
  const threads = useThreadStore((s) => s.threads)
  const activeThreadId = useThreadStore((s) => s.activeThreadId)

  // 모든 스레드 → 하이라이트
  const allThreadHighlights = useMemo<Highlight[]>(() => {
    return threads
      .filter((t) => t.chunkRects && t.chunkRects.length > 0)
      .map((t) => {
        const pageRects = t.chunkRects!.filter((r) => r.page === t.chunkRects![0].page)
        const bbox = boundingBox(pageRects)
        return {
          id: t.id,
          position: {
            boundingRect: bbox,
            rects: pageRects.map(grobidToHighlightRect),
            pageNumber: bbox.pageNumber,
          },
          content: { text: t.chunkContent ?? '' },
        } satisfies Highlight
      })
  }, [threads])

  // RAG 소스 하이라이트
  const sourceHighlights = useMemo<Highlight[]>(() => {
    return activeSources
      .filter((src) => src.rects && src.rects.length > 0)
      .map((src) => {
        const pageRects = src.rects.filter((r) => r.page === src.rects[0].page)
        const bbox = boundingBox(pageRects)
        return {
          id: `src-${src.chunkId}`,
          position: {
            boundingRect: bbox,
            rects: pageRects.map(grobidToHighlightRect),
            pageNumber: bbox.pageNumber,
          },
          content: { text: src.content },
        } satisfies Highlight
      })
  }, [activeSources])

  const highlights = useMemo<Highlight[]>(
    () => [...allThreadHighlights, ...sourceHighlights],
    [allThreadHighlights, sourceHighlights]
  )

  // 패널에서 스레드 선택 시 PDF 스크롤 (커스텀 이벤트로 분리)
  useEffect(() => {
    const handler = (e: Event) => {
      const { threadId } = (e as CustomEvent<{ threadId: string }>).detail
      const h = allThreadHighlights.find((h) => h.id === threadId)
      if (h && highlighterUtilsRef.current) {
        highlighterUtilsRef.current.scrollToHighlight(h)
      }
    }
    window.addEventListener('coread:scrollToThread', handler)
    return () => window.removeEventListener('coread:scrollToThread', handler)
  }, [allThreadHighlights])

  const getViewer = () => highlighterUtilsRef.current?.getViewer()

  const applyScale = (next: number) => {
    setScale(next)
    const v = getViewer()
    if (v) (v as any).currentScaleValue = String(next)
  }

  const zoomIn = () => {
    const current = getViewer()?.currentScale ?? scale
    const next = ZOOM_STEPS.find((s) => s > current + 0.01) ?? ZOOM_STEPS[ZOOM_STEPS.length - 1]
    applyScale(next)
  }

  const zoomOut = () => {
    const current = getViewer()?.currentScale ?? scale
    const prev = [...ZOOM_STEPS].reverse().find((s) => s < current - 0.01) ?? ZOOM_STEPS[0]
    applyScale(prev)
  }

  const goToPage = (page: number) => {
    const v = getViewer()
    if (!v) return
    const clamped = Math.max(1, Math.min(page, totalPages))
    v.currentPageNumber = clamped
    setCurrentPage(clamped)
    setPageInput(String(clamped))
  }

  const handleUtilsRef = useCallback((utils: PdfHighlighterUtils) => {
    highlighterUtilsRef.current = utils
    const poll = setInterval(() => {
      const v = utils.getViewer()
      if (v && v.pagesCount > 0) {
        setTotalPages(v.pagesCount)
        if (v.currentScale && v.currentScale > 0) setScale(v.currentScale)
        clearInterval(poll)
      }
    }, 200)
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden' }}>
      {/* 툴바 */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        padding: '6px 12px', borderBottom: '1px solid var(--border)',
        background: 'var(--bg)', flexShrink: 0,
      }}>
        <button onClick={() => goToPage(currentPage - 1)} disabled={currentPage <= 1} style={btnStyle}>‹</button>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <input
            value={pageInput}
            onChange={(e) => setPageInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') goToPage(Number(pageInput)) }}
            onBlur={() => goToPage(Number(pageInput))}
            style={{ width: '36px', textAlign: 'center', border: '1px solid var(--border)', borderRadius: '4px', padding: '2px 4px', fontFamily: 'var(--font-mono)', fontSize: '12px', background: 'var(--bg)' }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-faint)' }}>
            / {totalPages || '—'}
          </span>
        </div>
        <button onClick={() => goToPage(currentPage + 1)} disabled={currentPage >= totalPages} style={btnStyle}>›</button>

        <div style={{ width: '1px', height: '16px', background: 'var(--border)', margin: '0 4px' }} />

        <button onClick={zoomOut} style={btnStyle}>−</button>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)', minWidth: '40px', textAlign: 'center' }}>
          {Math.round(scale * 100)}%
        </span>
        <button onClick={zoomIn} style={btnStyle}>+</button>

        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          {allThreadHighlights.length > 0 && (
            <div style={{ fontSize: '11px', color: 'var(--text-faint)', fontFamily: 'var(--font-mono)' }}>
              {allThreadHighlights.length} threads
            </div>
          )}
          {onReprocess && (
            <button
              onClick={onReprocess}
              disabled={reprocessing}
              title="Re-run pipeline"
              style={{ ...btnStyle, width: 'auto', padding: '0 8px', fontSize: '11px', fontFamily: 'var(--font-mono)', opacity: reprocessing ? 0.5 : 1 }}
            >
              {reprocessing ? 'Processing…' : 'Reprocess'}
            </button>
          )}
          {onToggleThreadPanel && (
            <button
              onClick={onToggleThreadPanel}
              title={threadPanelOpen ? 'Close thread panel' : 'Open thread panel'}
              style={{
                ...btnStyle, width: '28px',
                background: threadPanelOpen ? 'var(--bg-panel)' : 'var(--bg)',
                borderColor: threadPanelOpen ? 'var(--accent)' : 'var(--border)',
                color: threadPanelOpen ? 'var(--text)' : 'var(--text-faint)',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <rect x="1" y="2" width="2" height="10" rx="1" fill="currentColor" />
                <rect x="5" y="2" width="8" height="10" rx="1" fill="currentColor" opacity="0.35" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* PDF 뷰어 */}
      <div style={{ position: 'relative', flex: 1, overflow: 'hidden', background: 'var(--bg-panel)' }}>
        <PdfLoader
          document={pdfUrl}
          workerSrc={workerSrc}
          beforeLoad={() => (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-faint)' }}>
              Loading PDF...
            </div>
          )}
          errorMessage={(error) => (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '8px' }}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-muted)' }}>Could not load PDF</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>{error.message}</span>
            </div>
          )}
          onError={(e) => console.error('[PdfLoader]', e)}
        >
          {(pdfDocument) => (
            <PdfHighlighter
              pdfDocument={pdfDocument}
              highlights={highlights}
              pdfScaleValue={scale}
              utilsRef={handleUtilsRef}
              style={{ position: 'absolute', inset: 0, overflow: 'auto' }}
            >
              <HighlightRenderer />
            </PdfHighlighter>
          )}
        </PdfLoader>
      </div>
    </div>
  )
}

function HighlightRenderer() {
  const { highlight, isScrolledTo, highlightBindings } = useHighlightContainerContext()
  const activeThreadId = useThreadStore((s) => s.activeThreadId)
  const setActiveThread = useThreadStore((s) => s.setActiveThread)

  if (!highlight?.position) return null

  const isThread = !highlight.id.startsWith('src-')
  const isActive = isThread && highlight.id === activeThreadId
  const bbox = highlight.position.boundingRect

  const handleBadgeClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    setActiveThread(highlight.id === activeThreadId ? null : highlight.id)
  }

  return (
    <MonitoredHighlightContainer highlightBindings={highlightBindings}>
      <TextHighlight
        isScrolledTo={isScrolledTo}
        highlight={highlight}
        style={isThread
          ? { background: isActive ? '#fbbf24' : '#fefce8' }
          : undefined
        }
      />
      {isThread && (
        <div
          style={{
            position: 'absolute',
            left: (bbox as any).left + (bbox as any).width + 6,
            top: (bbox as any).top,
            zIndex: 20,
            pointerEvents: 'auto',
          }}
        >
          <button
            onClick={handleBadgeClick}
            title="Open thread"
            style={{
              width: '22px',
              height: '22px',
              borderRadius: '50%',
              border: isActive ? '1.5px solid #b45309' : '1.5px solid #d97706',
              background: isActive ? '#fef3c7' : '#fffbeb',
              cursor: 'pointer',
              fontSize: '12px',
              lineHeight: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: isActive ? '0 0 0 2px rgba(245,158,11,0.3)' : '0 1px 3px rgba(0,0,0,0.12)',
              transition: 'all 0.15s',
              padding: 0,
            }}
          >
            💬
          </button>
        </div>
      )}
    </MonitoredHighlightContainer>
  )
}

const btnStyle: React.CSSProperties = {
  width: '24px', height: '24px',
  display: 'flex', alignItems: 'center', justifyContent: 'center',
  border: '1px solid var(--border)', borderRadius: '4px',
  background: 'var(--bg)', color: 'var(--text)',
  fontFamily: 'var(--font-sans)', fontSize: '14px',
  cursor: 'pointer',
  padding: 0,
}
