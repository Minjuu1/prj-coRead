import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useUserStore } from '../stores/userStore'
import { usePaperStore } from '../stores/paperStore'
import { getUserPapers, getPaperStatus, reprocessPaper } from '../services/api'
import { UploadModal } from '../components/UploadModal'
import type { LibraryPaper } from '../types'

const BASE = 'http://localhost:8000'

export default function LibraryPage() {
  const navigate = useNavigate()
  const userId = useUserStore((s) => s.userId) ?? 'anonymous'
  const setPaper = usePaperStore((s) => s.setPaper)

  const [papers, setPapers] = useState<LibraryPaper[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set())
  const pollRefs = useRef<Record<string, ReturnType<typeof setInterval>>>({})

  // 초기 로드
  useEffect(() => {
    getUserPapers(userId)
      .then((data) => {
        setPapers(data)
        data.filter((p) => p.status === 'processing').forEach((p) => startPolling(p.paperId))
      })
      .catch((err) => console.error('[library] getUserPapers failed:', err))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId])

  // 컴포넌트 언마운트 시 모든 interval 정리
  useEffect(() => {
    const refs = pollRefs.current
    return () => { Object.values(refs).forEach(clearInterval) }
  }, [])

  function startPolling(paperId: string) {
    if (pollRefs.current[paperId]) return
    setProcessingIds((prev) => new Set(prev).add(paperId))
    pollRefs.current[paperId] = setInterval(async () => {
      try {
        const { status } = await getPaperStatus(paperId, userId)
        if (status === 'ready' || status === 'error') {
          clearInterval(pollRefs.current[paperId])
          delete pollRefs.current[paperId]
          setProcessingIds((prev) => { const s = new Set(prev); s.delete(paperId); return s })
          // 완료된 논문 메타 갱신
          const updated = await getUserPapers(userId)
          setPapers(updated)
        }
      } catch { /* 네트워크 오류 시 계속 polling */ }
    }, 2000)
  }

  function handleUploadStarted(paperId: string) {
    // 임시 카드 추가
    const placeholder: LibraryPaper = {
      paperId,
      title: 'Processing...',
      authors: [],
      status: 'processing',
      chunkCount: 0,
      threadCount: 0,
      uploadedAt: new Date().toISOString(),
      filename: '',
    }
    setPapers((prev) => [placeholder, ...prev])
    startPolling(paperId)
  }

  function handleOpenPaper(paper: LibraryPaper) {
    const pdfUrl = `${BASE}/papers/${paper.paperId}/pdf`
    setPaper(paper.paperId, pdfUrl)
    navigate(`/reader/${paper.paperId}`)
  }

  async function handleRegenerate(paperId: string) {
    if (processingIds.has(paperId)) return
    await reprocessPaper(paperId, userId)
    setPapers((prev) =>
      prev.map((p) => p.paperId === paperId ? { ...p, status: 'processing' } : p)
    )
    startPolling(paperId)
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', padding: '48px 40px' }}>
      {/* 헤더 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '24px', fontWeight: 600, color: 'var(--text)', margin: 0 }}>
            My Library
          </h1>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
            {userId}
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          style={{
            background: 'var(--accent)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius)',
            padding: '10px 20px',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
            cursor: 'pointer',
          }}
        >
          + Upload
        </button>
      </div>

      {/* 목록 */}
      {loading ? (
        <p style={{ fontFamily: 'var(--font-sans)', fontSize: '14px', color: 'var(--text-muted)' }}>Loading...</p>
      ) : papers.length === 0 ? (
        <div style={{ textAlign: 'center', paddingTop: '80px' }}>
          <p style={{ fontFamily: 'var(--font-sans)', fontSize: '15px', color: 'var(--text-muted)' }}>
            No papers yet
          </p>
          <button
            onClick={() => setShowUploadModal(true)}
            style={{
              marginTop: '16px',
              background: 'none',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius)',
              padding: '8px 20px',
              fontSize: '13px',
              fontFamily: 'var(--font-sans)',
              color: 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            Upload your first paper
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
          {papers.map((paper, index) => (
            <PaperCard
              key={paper.paperId}
              paper={paper}
              index={index + 1}
              isProcessing={processingIds.has(paper.paperId) || paper.status === 'processing'}
              onOpen={() => handleOpenPaper(paper)}
              onRegenerate={() => handleRegenerate(paper.paperId)}
            />
          ))}
        </div>
      )}

      {showUploadModal && (
        <UploadModal
          onClose={() => setShowUploadModal(false)}
          onUploadStarted={handleUploadStarted}
        />
      )}
    </div>
  )
}

// ────────────────────────────────────────────
// PaperCard
// ────────────────────────────────────────────

interface PaperCardProps {
  paper: LibraryPaper
  index: number
  isProcessing: boolean
  onOpen: () => void
  onRegenerate: () => void
}

function PaperCard({ paper, index, isProcessing, onOpen, onRegenerate }: PaperCardProps) {
  const statusColor = {
    ready: 'var(--accent)',
    processing: '#f59e0b',
    error: 'var(--critical)',
  }[paper.status]

  const statusLabel = {
    ready: 'ready',
    processing: 'processing...',
    error: 'error',
  }[paper.status]

  const uploadDate = paper.uploadedAt
    ? new Date(paper.uploadedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    : ''

  const authorText = paper.authors?.length > 0
    ? paper.authors.slice(0, 3).join(', ') + (paper.authors.length > 3 ? ' et al.' : '')
    : ''

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '20px 0',
        borderBottom: '1px solid var(--border)',
        opacity: paper.status === 'error' ? 0.6 : 1,
      }}
    >
      {/* 넘버 */}
      <span style={{
        fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-faint)',
        minWidth: '24px', textAlign: 'right', flexShrink: 0,
      }}>
        {index}
      </span>

      {/* 메인 텍스트 */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontFamily: 'var(--font-serif)', fontSize: '14px', fontWeight: 600,
          color: 'var(--text)',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>
          {paper.title || paper.filename || 'Untitled'}
        </div>
        {authorText && (
          <div style={{ fontFamily: 'var(--font-sans)', fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {authorText}
          </div>
        )}
      </div>

      {/* 상태 + 카운트 */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0, minWidth: '160px' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: statusColor }}>
          {isProcessing && <span style={{ marginRight: '4px' }}>·</span>}
          {statusLabel}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)' }}>
          {paper.status === 'ready'
            ? `${paper.threadCount} threads · ${paper.chunkCount} chunks`
            : uploadDate}
        </span>
      </div>

      {/* 버튼들 */}
      <div style={{ display: 'flex', gap: '8px', flexShrink: 0 }}>
        <button
          onClick={onRegenerate}
          disabled={isProcessing}
          style={{
            background: 'none',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)', padding: '6px 14px',
            fontSize: '12px', fontFamily: 'var(--font-mono)',
            color: isProcessing ? 'var(--text-faint)' : 'var(--text-muted)',
            cursor: isProcessing ? 'not-allowed' : 'pointer',
          }}
        >
          Regenerate
        </button>
        <button
          onClick={onOpen}
          disabled={paper.status !== 'ready'}
          style={{
            background: paper.status === 'ready' ? 'var(--accent)' : 'var(--border)',
            color: '#fff', border: 'none',
            borderRadius: 'var(--radius)', padding: '6px 18px',
            fontSize: '12px', fontFamily: 'var(--font-sans)', fontWeight: 500,
            cursor: paper.status === 'ready' ? 'pointer' : 'not-allowed',
          }}
        >
          Read
        </button>
      </div>
    </div>
  )
}
