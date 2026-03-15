import { useState } from 'react'
import { useUserStore } from '../stores/userStore'

interface LoginPageProps {
  onSuccess: () => void
}

export default function LoginPage({ onSuccess }: LoginPageProps) {
  const [code, setCode] = useState('')
  const setUserId = useUserStore((s) => s.setUserId)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!code.trim()) return
    setUserId(code.trim())
    onSuccess()
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'var(--bg)',
      }}
    >
      <h1
        style={{
          fontFamily: 'var(--font-serif)',
          fontSize: '28px',
          fontWeight: 600,
          color: 'var(--text)',
          margin: '0 0 8px 0',
        }}
      >
        CoRead
      </h1>
      <p
        style={{
          fontFamily: 'var(--font-sans)',
          fontSize: '14px',
          color: 'var(--text-muted)',
          margin: '0 0 32px 0',
        }}
      >
        Critical reading for academic papers
      </p>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Enter your user ID"
          style={{
            border: '1px solid var(--border)',
            padding: '10px 14px',
            width: '280px',
            borderRadius: 'var(--radius)',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
            background: 'var(--bg)',
            color: 'var(--text)',
            outline: 'none',
            boxSizing: 'border-box',
          }}
        />
        <button
          type="submit"
          disabled={!code.trim()}
          style={{
            background: code.trim() ? '#1a1a1a' : 'var(--border)',
            color: '#ffffff',
            border: 'none',
            borderRadius: 'var(--radius)',
            padding: '12px',
            width: '100%',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
            cursor: code.trim() ? 'pointer' : 'not-allowed',
            transition: 'background 0.15s',
          }}
        >
          Enter
        </button>
      </form>
    </div>
  )
}
