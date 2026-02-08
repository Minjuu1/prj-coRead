export const ANNOTATION_TYPES = {
  confusing: {
    id: 'confusing',
    label: 'Confusing',
    description: 'Something unclear, ambiguous, or hard to understand',
  },
  challenge: {
    id: 'challenge',
    label: 'Challenge',
    description: 'Something you disagree with, question, or want to correct',
  },
  highlight: {
    id: 'highlight',
    label: 'Highlight',
    description: 'A noteworthy point that deserves attention',
  },
  connect: {
    id: 'connect',
    label: 'Connect',
    description: 'Linking to another concept, experience, or external idea',
  },
  probe: {
    id: 'probe',
    label: 'Probe',
    description: 'Digging deeper into the issue or asking follow-up questions',
  },
  summarize: {
    id: 'summarize',
    label: 'Summarize',
    description: 'Synthesizing or summarizing the key points',
  },
} as const;

export type AnnotationType = keyof typeof ANNOTATION_TYPES;

export const ANNOTATION_CONFIG = {
  maxPerAgent: 20,
  targetModes: ['text', 'section'] as const,
} as const;
