import { useRef, useState, useCallback, useEffect } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { usePaperStore } from '../stores/paperStore'
import { useThreadStore } from '../stores/threadStore'
import { useUserStore } from '../stores/userStore'
import { PaperReader } from '../components/PaperReader/PaperReader'
import { ThreadPanel } from '../components/ThreadPanel/ThreadPanel'
import { getThreads, getPaperStatus, reprocessPaper } from '../services/api'

const BASE = 'http://localhost:8000'
const MIN_LEFT = 320
const MIN_RIGHT = 300

export default function ReaderPage() {
  const { paperId: paramPaperId } = useParams<{ paperId: string }>()
  const { paperId: storePaperId, pdfUrl: storePdfUrl } = usePaperStore()

  // URL param 우선, 없으면 Zustand store fallback
  const paperId = paramPaperId ?? storePaperId
  const pdfUrl = paramPaperId
    ? `${BASE}/papers/${paramPaperId}/pdf`
    : storePdfUrl

  const userId = useUserStore((s) => s.userId) ?? 'anonymous'
  const setThreads = useThreadStore((s) => s.setThreads)
  const [leftWidth, setLeftWidth] = useState<number | null>(null)
  const [threadPanelOpen, setThreadPanelOpen] = useState(true)
  const [reprocessing, setReprocessing] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const handleReprocess = useCallback(async () => {
    if (!paperId || reprocessing) return
    setReprocessing(true)
    await reprocessPaper(paperId, userId)
    pollRef.current = setInterval(async () => {
      const { status } = await getPaperStatus(paperId, userId)
      if (status === 'ready' || status === 'error') {
        clearInterval(pollRef.current!)
        pollRef.current = null
        setReprocessing(false)
        if (status === 'ready') {
          const threads = await getThreads(paperId, userId)
          setThreads(threads)
        }
      }
    }, 2000)
  }, [paperId, userId, reprocessing, setThreads])

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])
  const containerRef = useRef<HTMLDivElement>(null)
  const dragging = useRef(false)

  // threads 로드
  useEffect(() => {
    if (!paperId) return
    getThreads(paperId, userId).then(setThreads)
  }, [paperId, userId, setThreads])

  // 초기 너비: 컨테이너 너비 - 420px (thread panel)
  useEffect(() => {
    if (containerRef.current) {
      setLeftWidth(containerRef.current.offsetWidth - 720)
    }
  }, [])

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    dragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!dragging.current || !containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const newLeft = e.clientX - rect.left
      const containerW = containerRef.current.offsetWidth
      if (newLeft >= MIN_LEFT && containerW - newLeft >= MIN_RIGHT) {
        setLeftWidth(newLeft)
      }
    }
    const onMouseUp = () => {
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [])

  if (!pdfUrl) return <Navigate to="/library" replace />

  return (
    <div
      ref={containerRef}
      style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}
    >
      {/* PDF 뷰어 */}
      <div
        style={{
          width: threadPanelOpen ? (leftWidth ?? 'calc(100% - 720px)') : '150%',
          flexShrink: 0,
          overflow: 'hidden',
          transition: threadPanelOpen ? 'none' : 'width 0.2s ease',
        }}
      >
        <PaperReader
          pdfUrl={pdfUrl}
          threadPanelOpen={threadPanelOpen}
          onToggleThreadPanel={() => setThreadPanelOpen((v) => !v)}
          onReprocess={handleReprocess}
          reprocessing={reprocessing}
        />
      </div>

      {/* 드래그 핸들 */}
      {threadPanelOpen && (
        <div
          onMouseDown={onMouseDown}
          style={{
            width: '4px', flexShrink: 0,
            background: 'var(--border)',
            cursor: 'col-resize',
            transition: 'background 0.15s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--border)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'var(--border)')}
        />
      )}

      {/* Thread Panel */}
      {threadPanelOpen && (
        <div style={{ flex: 1, minWidth: MIN_RIGHT, overflow: 'hidden' }}>
          <ThreadPanel />
        </div>
      )}
    </div>
  )
}
