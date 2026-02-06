export const AGENTS = {
  instrumental: {
    id: 'instrumental',
    name: 'Instrumental',
    color: '#F59E0B',
    colorLight: 'rgba(245, 158, 11, 0.2)',
    description: 'Focused on practical understanding and application',
  },
  critical: {
    id: 'critical',
    name: 'Critical',
    color: '#3B82F6',
    colorLight: 'rgba(59, 130, 246, 0.2)',
    description: 'Focused on questioning and analyzing',
  },
  aesthetic: {
    id: 'aesthetic',
    name: 'Aesthetic',
    color: '#A855F7',
    colorLight: 'rgba(168, 85, 247, 0.2)',
    description: 'Focused on connecting and expanding meaning',
  },
} as const;

export type AgentId = keyof typeof AGENTS;
export const AGENT_IDS = Object.keys(AGENTS) as AgentId[];
