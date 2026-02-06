export const ANNOTATION_TYPES = {
  interesting: {
    id: 'interesting',
    label: 'Interesting',
    description: 'Something that catches attention',
  },
  confusing: {
    id: 'confusing',
    label: 'Confusing',
    description: 'Something unclear or hard to understand',
  },
  disagree: {
    id: 'disagree',
    label: 'Disagree',
    description: 'Something to question or challenge',
  },
  important: {
    id: 'important',
    label: 'Important',
    description: 'Key point that matters',
  },
  question: {
    id: 'question',
    label: 'Question',
    description: 'A question that arises from reading',
  },
} as const;

export type AnnotationType = keyof typeof ANNOTATION_TYPES;

export const ANNOTATION_CONFIG = {
  maxPerAgent: 20,
  targetModes: ['text', 'section'] as const,
} as const;
