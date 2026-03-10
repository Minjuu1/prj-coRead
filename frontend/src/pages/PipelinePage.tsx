import { useState } from 'react'
import { usePaperStore } from '../stores/paperStore'

const BASE = 'http://localhost:8000'

interface StageResult {
  label: string
  count: number
  data: any[]
}

function downloadJson(filename: string, data: any) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function StageCard({ label, result, loading }: { label: string; result: StageResult | null; loading: boolean }) {
  const [expanded, setExpanded] = useState<number | null>(null)

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: '8px',
      overflow: 'hidden',
      background: 'var(--bg)',
    }}>
      {/* 헤더 */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: result ? '1px solid var(--border)' : 'none',
        background: 'var(--bg-panel)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', letterSpacing: '0.06em', color: 'var(--text-faint)' }}>
            {label.toUpperCase()}
          </span>
          {loading && (
            <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>불러오는 중...</span>
          )}
          {result && (
            <span style={{
              fontSize: '11px', fontFamily: 'var(--font-mono)',
              background: 'var(--accent-light)', color: 'var(--accent)',
              padding: '1px 7px', borderRadius: '10px',
            }}>
              {result.count}개
            </span>
          )}
        </div>
        {result && result.count > 0 && (
          <button
            onClick={() => downloadJson(`${label.toLowerCase().replace(/\s/g, '_')}.json`, result.data)}
            style={{
              padding: '4px 12px', fontSize: '11px', fontFamily: 'var(--font-mono)',
              border: '1px solid var(--border)', borderRadius: '4px',
              background: 'var(--bg)', color: 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            ↓ JSON
          </button>
        )}
      </div>

      {/* 아이템 목록 */}
      {result && result.data.length > 0 && (
        <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
          {result.data.map((item, i) => (
            <div
              key={i}
              style={{
                borderBottom: i < result.data.length - 1 ? '1px solid var(--border)' : 'none',
              }}
            >
              {/* 요약 행 */}
              <div
                onClick={() => setExpanded(expanded === i ? null : i)}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: '10px',
                  padding: '10px 16px', cursor: 'pointer',
                  background: expanded === i ? 'var(--bg-panel)' : 'transparent',
                  transition: 'background 0.1s',
                }}
              >
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-faint)', flexShrink: 0, marginTop: '2px' }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '12px', color: 'var(--text)', lineHeight: 1.5, marginBottom: '2px' }}>
                    {/* chunks: content 미리보기 / threads: contestablePoint */}
                    {item.contestablePoint
                      ? `"${item.contestablePoint.slice(0, 120)}${item.contestablePoint.length > 120 ? '…' : ''}"`
                      : (item.content ?? '').slice(0, 120) + ((item.content ?? '').length > 120 ? '…' : '')}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {item.section && (
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-faint)' }}>
                        {item.section}
                      </span>
                    )}
                    {item.pageStart !== undefined && (
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-faint)' }}>
                        p.{item.pageStart}
                      </span>
                    )}
                    {item.rects !== undefined && (
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: item.rects.length > 0 ? '#16a34a' : '#dc2626' }}>
                        {item.rects.length > 0 ? `rects: ${item.rects.length}` : 'no coords'}
                      </span>
                    )}
                    {item.status && (
                      <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-faint)' }}>
                        {item.status}
                      </span>
                    )}
                  </div>
                </div>
                <span style={{ fontSize: '10px', color: 'var(--text-faint)', flexShrink: 0 }}>
                  {expanded === i ? '▲' : '▼'}
                </span>
              </div>

              {/* 펼침: raw JSON */}
              {expanded === i && (
                <pre style={{
                  margin: 0, padding: '10px 16px',
                  background: '#1e1e2e',
                  color: '#cdd6f4',
                  fontSize: '11px', fontFamily: 'var(--font-mono)',
                  overflowX: 'auto', lineHeight: 1.6,
                  borderTop: '1px solid var(--border)',
                }}>
                  {JSON.stringify(item, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </div>
      )}

      {result && result.data.length === 0 && (
        <div style={{ padding: '24px', textAlign: 'center', fontSize: '12px', color: 'var(--text-faint)' }}>
          데이터 없음
        </div>
      )}
    </div>
  )
}

export default function PipelinePage() {
  const storedPaperId = usePaperStore((s) => s.paperId)
  const [paperId, setPaperId] = useState(storedPaperId ?? '')
  const [loading, setLoading] = useState<Record<string, boolean>>({})
  const [results, setResults] = useState<Record<string, StageResult>>({})
  const [error, setError] = useState<string | null>(null)

  const fetch_ = async (stage: string, url: string, dataKey: string, label: string) => {
    setLoading((l) => ({ ...l, [stage]: true }))
    setError(null)
    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      const data = json[dataKey] ?? []
      setResults((r) => ({ ...r, [stage]: { label, count: data.length, data } }))
    } catch (e: any) {
      setError(`[${label}] ${e.message}`)
    } finally {
      setLoading((l) => ({ ...l, [stage]: false }))
    }
  }

  const fetchAll = () => {
    if (!paperId.trim()) return
    const id = paperId.trim()
    fetch_('chunks', `${BASE}/papers/${id}/chunks`, 'chunks', 'Ingestion (Chunks)')
    fetch_('threads', `${BASE}/papers/${id}/threads`, 'threads', 'Thread Generation')
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      padding: '32px', fontFamily: 'var(--font-sans)',
    }}>
      <div style={{ maxWidth: '860px', margin: '0 auto' }}>
        {/* 헤더 */}
        <div style={{ marginBottom: '28px' }}>
          <div style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-faint)', letterSpacing: '0.08em', marginBottom: '6px' }}>
            PIPELINE INSPECTOR
          </div>
          <h1 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text)', margin: 0 }}>
            중간 결과 확인
          </h1>
        </div>

        {/* Paper ID 입력 */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px' }}>
          <input
            value={paperId}
            onChange={(e) => setPaperId(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchAll()}
            placeholder="Paper ID"
            style={{
              flex: 1, padding: '8px 12px',
              border: '1px solid var(--border)', borderRadius: '6px',
              fontFamily: 'var(--font-mono)', fontSize: '13px',
              background: 'var(--bg)', color: 'var(--text)',
              outline: 'none',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--accent)')}
            onBlur={(e) => (e.target.style.borderColor = 'var(--border)')}
          />
          <button
            onClick={fetchAll}
            disabled={!paperId.trim()}
            style={{
              padding: '8px 20px', fontSize: '13px', fontWeight: 500,
              border: 'none', borderRadius: '6px',
              background: paperId.trim() ? 'var(--accent)' : 'var(--bg-panel)',
              color: paperId.trim() ? 'var(--accent-fg)' : 'var(--text-faint)',
              cursor: paperId.trim() ? 'pointer' : 'not-allowed',
            }}
          >
            불러오기
          </button>
          {/* 각 단계별 개별 다운로드 */}
          <button
            onClick={() => results.chunks && downloadJson(`chunks_${paperId}.json`, results.chunks.data)}
            disabled={!results.chunks}
            title="Chunks JSON 전체 다운로드"
            style={{
              padding: '8px 14px', fontSize: '12px', fontFamily: 'var(--font-mono)',
              border: '1px solid var(--border)', borderRadius: '6px',
              background: 'var(--bg)', color: results.chunks ? 'var(--text-muted)' : 'var(--text-faint)',
              cursor: results.chunks ? 'pointer' : 'not-allowed',
            }}
          >
            ↓ chunks
          </button>
          <button
            onClick={() => results.threads && downloadJson(`threads_${paperId}.json`, results.threads.data)}
            disabled={!results.threads}
            title="Threads JSON 전체 다운로드"
            style={{
              padding: '8px 14px', fontSize: '12px', fontFamily: 'var(--font-mono)',
              border: '1px solid var(--border)', borderRadius: '6px',
              background: 'var(--bg)', color: results.threads ? 'var(--text-muted)' : 'var(--text-faint)',
              cursor: results.threads ? 'pointer' : 'not-allowed',
            }}
          >
            ↓ threads
          </button>
        </div>

        {error && (
          <div style={{
            marginBottom: '16px', padding: '10px 14px',
            background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '6px',
            fontSize: '12px', fontFamily: 'var(--font-mono)', color: '#b91c1c',
          }}>
            {error}
          </div>
        )}

        {/* 단계별 카드 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <StageCard
            label="Ingestion (Chunks)"
            result={results.chunks ?? null}
            loading={loading.chunks ?? false}
          />
          <StageCard
            label="Thread Generation"
            result={results.threads ?? null}
            loading={loading.threads ?? false}
          />
        </div>
      </div>
    </div>
  )
}
