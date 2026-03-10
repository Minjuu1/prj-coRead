import type { Message } from '../../types'
import { usePaperStore } from '../../stores/paperStore'
import { AgentBadge } from './AgentBadge'

export function MessageBubble({ msg }: { msg: Message }) {
  const agents = usePaperStore((s) => s.agents)
  const isStudent = msg.author === 'student'

  if (isStudent) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '12px' }}>
        <div
          style={{
            maxWidth: '75%',
            background: 'var(--accent)',
            color: 'var(--accent-fg)',
            borderRadius: '12px 12px 2px 12px',
            padding: '10px 14px',
            fontSize: '14px',
            lineHeight: 1.55,
          }}
        >
          {msg.content}
        </div>
      </div>
    )
  }

  const config = agents.find((a) => a.id === msg.author)
  const colorIndex = config?.color_index ?? 0

  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ marginBottom: '4px' }}>
        <AgentBadge agent={msg.author} />
      </div>
      <div
        style={{
          maxWidth: '85%',
          background: `var(--agent-${colorIndex}-bg)`,
          borderRadius: '0 8px 8px 0',
          padding: '10px 14px',
          fontSize: '14px',
          lineHeight: 1.6,
          color: 'var(--text)',
        }}
      >
        {msg.content}
      </div>
    </div>
  )
}
