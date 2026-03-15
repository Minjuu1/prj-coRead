import { useRef, useState } from 'react'
import { usePaperStore } from '../stores/paperStore'
import { uploadPaper } from '../services/api'

interface UploadPageProps {
  onSuccess: () => void
}

type Phase = 'idle' | 'uploading' | 'processing' | 'error'

const STAGE_LABELS: Record<string, string> = {
  ingestion: '논문 파싱 중...',
  agents: '에이전트 생성 중...',
  reading: '에이전트 읽기 중...',
  cross_reading: '논쟁 지점 추출 중...',
  discussions: '토론 생성 중...',
}

function streamPipelineStatus(
  paperId: string,
  onStage: (label: string) => void,
  onReady: () => void,
  onError: () => void,
): () => void {
  const es = new EventSource(`http://localhost:8000/papers/${paperId}/pipeline-stream`)
  let settled = false  // done 이벤트를 받은 후 onerror가 중복 실행되는 것을 방지

  es.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data)
      if (event.stage === 'done') {
        settled = true
        es.close()
        event.status === 'ready' ? onReady() : onError()
      } else {
        const label = STAGE_LABELS[event.stage]
        if (label) onStage(label)
      }
    } catch { /* ignore */ }
  }
  es.onerror = () => {
    if (settled) return
    settled = true
    es.close()
    onError()
  }
  return () => es.close()
}

export default function UploadPage({ onSuccess }: UploadPageProps) {
  const [file, setFile] = useState<File | null>(null)
  const [phase, setPhase] = useState<Phase>('idle')
  const [stageLabel, setStageLabel] = useState('파이프라인 실행 중...')
  const closeStream = useRef<(() => void) | null>(null)
  const setPaper = usePaperStore((s) => s.setPaper)

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!file) return

    setPhase('uploading')
    try {
      const { paperId } = await uploadPaper(file)
      const url = `http://localhost:8000/papers/${paperId}/pdf`
      setPaper(paperId, url)
      setPhase('processing')
      setStageLabel('파이프라인 실행 중...')
      closeStream.current = streamPipelineStatus(
        paperId,
        (label) => setStageLabel(label),
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
    processing: stageLabel,
    error: '오류 발생 — 다시 시도',
  }[phase]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'var(--bg)' }}>
      <h2 style={{ fontFamily: 'var(--font-sans)', fontSize: '22px', fontWeight: 600, color: 'var(--text)', margin: '0 0 8px 0' }}>
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
