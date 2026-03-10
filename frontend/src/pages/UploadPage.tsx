import { useState } from 'react'
import { usePaperStore } from '../stores/paperStore'
import { uploadPaper, getPaperStatus } from '../services/api'

interface UploadPageProps {
  onSuccess: () => void
}

type Phase = 'idle' | 'uploading' | 'processing' | 'error'

function pollStatus(paperId: string, onReady: () => void, onError: () => void) {
  const id = setInterval(async () => {
    try {
      const { status } = await getPaperStatus(paperId)
      if (status === 'ready') {
        clearInterval(id)
        onReady()
      } else if (status === 'error') {
        clearInterval(id)
        onError()
      }
    } catch {
      clearInterval(id)
      onError()
    }
  }, 2000)
}

export default function UploadPage({ onSuccess }: UploadPageProps) {
  const [file, setFile] = useState<File | null>(null)
  const [phase, setPhase] = useState<Phase>('idle')
  const setPaper = usePaperStore((s) => s.setPaper)

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!file) return

    setPhase('uploading')
    try {
      const { paperId, url } = await uploadPaper(file)
      setPaper(paperId, url)
      setPhase('processing')
      pollStatus(
        paperId,
        () => onSuccess(),
        () => setPhase('error'),
      )
    } catch {
      setPhase('error')
    }
  }

  const busy = phase === 'uploading' || phase === 'processing'

  const statusLabel = {
    idle: '업로드',
    uploading: '업로드 중...',
    processing: '파이프라인 실행 중...',
    error: '오류 발생 — 다시 시도',
  }[phase]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
      <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '22px', fontWeight: 600, color: 'var(--text)', margin: '0 0 8px 0' }}>
        논문 업로드
      </h2>
      <p style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--text-muted)', margin: '0 0 28px 0' }}>
        PDF 파일을 선택해주세요
      </p>

      <form onSubmit={handleUpload} style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '280px' }}>
        <input
          type="file"
          accept=".pdf"
          disabled={busy}
          onChange={(e) => { setFile(e.target.files?.[0] ?? null); setPhase('idle') }}
          style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--text)', cursor: 'pointer' }}
        />
        <button
          type="submit"
          disabled={!file || busy}
          style={{
            background: file && !busy ? 'var(--accent)' : 'var(--border)',
            color: '#ffffff',
            border: 'none',
            borderRadius: 'var(--radius)',
            padding: '12px',
            width: '100%',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
            cursor: file && !busy ? 'pointer' : 'not-allowed',
            transition: 'background 0.15s',
          }}
        >
          {statusLabel}
        </button>

        {phase === 'processing' && (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-faint)', textAlign: 'center', margin: 0 }}>
            GROBID 파싱 + Thread 생성 중 (1~2분 소요)
          </p>
        )}
        {phase === 'error' && (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--critical)', textAlign: 'center', margin: 0 }}>
            파이프라인 실패 — 로그를 확인하세요
          </p>
        )}
      </form>
    </div>
  )
}
