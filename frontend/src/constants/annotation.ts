// Stance-specific annotation types
// Each stance has its own vocabulary reflecting its relationship to text

export const ANNOTATION_TYPES = {
  // Instrumental - text as resource (concepts, information)
  note: {
    id: 'note',
    stance: 'instrumental',
    label: 'Note',
    description: 'Identifies key concepts, methods, or findings worth retaining — captures what\'s practically useful or important to understand',
  },
  stuck: {
    id: 'stuck',
    stance: 'instrumental',
    label: 'Stuck',
    description: 'Flags where understanding breaks down — missing information, unclear explanations, or insufficient detail that blocks comprehension or application',
  },

  // Critical - text as argument (inferences, assumptions, point of view)
  question: {
    id: 'question',
    stance: 'critical',
    label: 'Question',
    description: 'Probes the evidence, logic, or methodology — challenges whether conclusions follow from the data presented',
  },
  uncover: {
    id: 'uncover',
    stance: 'critical',
    label: 'Uncover',
    description: 'Surfaces unstated premises, hidden biases, or ideological framings that shape the argument without being made explicit',
  },
  alternative: {
    id: 'alternative',
    stance: 'critical',
    label: 'Alternative',
    description: 'Offers a different interpretation, counterexample, or point of view the author doesn\'t consider',
  },

  // Aesthetic - text as encounter (personal response, implications)
  struck: {
    id: 'struck',
    stance: 'aesthetic',
    label: 'Struck',
    description: 'Responds to what personally resonates, surprises, or moves — evoking memories, emotions, or a shift in perspective',
  },
  implication: {
    id: 'implication',
    stance: 'aesthetic',
    label: 'Implication',
    description: 'Explores where the idea leads — its consequences, possibilities, or connections to other contexts and experiences',
  },
} as const;

export type AnnotationType = keyof typeof ANNOTATION_TYPES;
export type AgentId = 'instrumental' | 'critical' | 'aesthetic';

// Pre-computed mapping for efficient agent-specific lookup
export const ANNOTATION_TYPES_BY_AGENT = {
  instrumental: ['note', 'stuck'],
  critical: ['question', 'uncover', 'alternative'],
  aesthetic: ['struck', 'implication'],
} as const;

export function getAnnotationTypesForAgent(agentId: AgentId): AnnotationType[] {
  return ANNOTATION_TYPES_BY_AGENT[agentId] as unknown as AnnotationType[];
}

export const ANNOTATION_CONFIG = {
  maxPerAgent: 20,
  targetModes: ['text', 'section'] as const,
} as const;
