// Stance-specific annotation types
// Each stance has its own vocabulary reflecting its relationship to text

export const ANNOTATION_TYPES = {
  // Instrumental - text as resource (extract, apply, organize)
  extract: {
    id: 'extract',
    stance: 'instrumental',
    label: 'Extract',
    description: 'Pulls out key concepts, definitions, or methods that can be reused or built upon',
  },
  apply: {
    id: 'apply',
    stance: 'instrumental',
    label: 'Apply',
    description: 'Suggests how this idea could be applied in another context or project',
  },
  clarify: {
    id: 'clarify',
    stance: 'instrumental',
    label: 'Clarify',
    description: 'Adds interpretation to make unclear parts more understandable',
  },
  gap: {
    id: 'gap',
    stance: 'instrumental',
    label: 'Gap',
    description: 'Points out missing or insufficient information that blocks understanding',
  },

  // Critical - text as argument (question, evaluate, deconstruct)
  question: {
    id: 'question',
    stance: 'critical',
    label: 'Question',
    description: 'Raises questions about the evidence or logical connections',
  },
  challenge: {
    id: 'challenge',
    stance: 'critical',
    label: 'Challenge',
    description: 'Points out weaknesses, overgeneralizations, or logical leaps in the argument',
  },
  counter: {
    id: 'counter',
    stance: 'critical',
    label: 'Counter',
    description: 'Offers alternative explanations or counterexamples the author didn\'t consider',
  },
  assumption: {
    id: 'assumption',
    stance: 'critical',
    label: 'Assumption',
    description: 'Reveals unstated premises or ideological biases underlying the argument',
  },

  // Aesthetic - text as encounter (resonate, connect, imagine)
  resonate: {
    id: 'resonate',
    stance: 'aesthetic',
    label: 'Resonate',
    description: 'Responds to parts that personally resonate or evoke emotional reaction',
  },
  remind: {
    id: 'remind',
    stance: 'aesthetic',
    label: 'Remind',
    description: 'Shares associations with personal experiences, other texts, or real-world cases',
  },
  surprise: {
    id: 'surprise',
    stance: 'aesthetic',
    label: 'Surprise',
    description: 'Reacts to parts that broke expectations or opened new perspectives',
  },
  imagine: {
    id: 'imagine',
    stance: 'aesthetic',
    label: 'Imagine',
    description: 'Extends the idea or imagines possibilities in different contexts',
  },
} as const;

export type AnnotationType = keyof typeof ANNOTATION_TYPES;
export type AgentId = 'instrumental' | 'critical' | 'aesthetic';

// Pre-computed mapping for efficient agent-specific lookup
export const ANNOTATION_TYPES_BY_AGENT = {
  instrumental: ['extract', 'apply', 'clarify', 'gap'],
  critical: ['question', 'challenge', 'counter', 'assumption'],
  aesthetic: ['resonate', 'remind', 'surprise', 'imagine'],
} as const;

export function getAnnotationTypesForAgent(agentId: AgentId): AnnotationType[] {
  return ANNOTATION_TYPES_BY_AGENT[agentId] as unknown as AnnotationType[];
}

export const ANNOTATION_CONFIG = {
  maxPerAgent: 20,
  targetModes: ['text', 'section'] as const,
} as const;
