export const ANNOTATION_TYPES = {
  // 기존 타입
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
  // 새 타입
  tangent: {
    id: 'tangent',
    label: 'Tangent',
    description: 'Going off on a related but divergent topic',
  },
  correct: {
    id: 'correct',
    label: 'Correct',
    description: 'Correcting a misunderstanding or error',
  },
  connect: {
    id: 'connect',
    label: 'Connect',
    description: 'Linking to another section or external concept',
  },
  search: {
    id: 'search',
    label: 'Search',
    description: 'Need to look up more information',
  },
  example: {
    id: 'example',
    label: 'Example',
    description: 'Providing a concrete example or experience',
  },
  probe: {
    id: 'probe',
    label: 'Probe',
    description: 'Digging deeper into the issue',
  },
  summarize: {
    id: 'summarize',
    label: 'Summarize',
    description: 'Summarizing or synthesizing the discussion so far',
  },
} as const;

export type AnnotationType = keyof typeof ANNOTATION_TYPES;

export const ANNOTATION_CONFIG = {
  maxPerAgent: 20,
  targetModes: ['text', 'section'] as const,
} as const;
