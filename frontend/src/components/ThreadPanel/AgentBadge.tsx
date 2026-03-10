import type { AgentId } from '../../types'

const LABEL: Record<AgentId, string> = {
  critical: 'Critical',
  instrumental: 'Instrumental',
  aesthetic: 'Aesthetic',
}

export function AgentBadge({ agent }: { agent: AgentId }) {
  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        fontWeight: 500,
        color: `var(--${agent})`,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}
    >
      {LABEL[agent]}
    </span>
  )
}
