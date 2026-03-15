import { useState } from 'react'
import { useUserStore } from '../stores/userStore'
import { uploadPaper } from '../services/api'

interface UploadModalProps {
  onClose: () => void
  onUploadStarted: (paperId: string) => void
}

export function UploadModal({ onClose, onUploadStarted }: UploadModalProps) {
  const userId = useUserStore((s) => s.userId) ?? 'anonymous'
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || uploading) return
    setUploading(true)
    setError(false)
    try {
      const { paperId } = await uploadPaper(file, userId)
      onUploadStarted(paperId)
      onClose()
    } catch {
      setError(true)
      setUploading(false)
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.4)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 100,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          padding: '32px',
          width: '320px',
          display: 'flex', flexDirection: 'column', gap: '16px',
        }}
      >
        <h3 style={{ fontFamily: 'var(--font-serif)', fontSize: '18px', fontWeight: 600, color: 'var(--text)', margin: 0 }}>
          Upload Paper
        </h3>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <input
            type="file"
            accept=".pdf"
            disabled={uploading}
            onChange={(e) => { setFile(e.target.files?.[0] ?? null); setError(false) }}
            style={{ fontFamily: 'var(--font-sans)', fontSize: '13px', color: 'var(--text)', cursor: 'pointer' }}
          />
          <button
            type="submit"
            disabled={!file || uploading}
            style={{
              background: file && !uploading ? 'var(--accent)' : 'var(--border)',
              color: '#fff',
              border: 'none',
              borderRadius: 'var(--radius)',
              padding: '10px',
              fontSize: '14px',
              fontFamily: 'var(--font-sans)',
              cursor: file && !uploading ? 'pointer' : 'not-allowed',
            }}
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
          {error && (
            <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--critical)', margin: 0, textAlign: 'center' }}>
              Upload failed — please try again
            </p>
          )}
        </form>
        <button
          onClick={onClose}
          style={{
            background: 'none', border: 'none',
            color: 'var(--text-muted)', fontSize: '13px',
            fontFamily: 'var(--font-sans)', cursor: 'pointer', textAlign: 'center',
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
