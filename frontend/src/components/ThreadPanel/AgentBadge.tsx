import { usePaperStore } from '../../stores/paperStore'

export function AgentBadge({ agent }: { agent: string }) {
  const agents = usePaperStore((s) => s.agents)
  const config = agents.find((a) => a.id === agent)
  const colorIndex = config?.color_index ?? 0
  const label = config?.name ?? agent

  return (
    <span
      style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '11px',
        fontWeight: 500,
        color: `var(--agent-${colorIndex})`,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}
    >
      {label}
    </span>
  )
}
