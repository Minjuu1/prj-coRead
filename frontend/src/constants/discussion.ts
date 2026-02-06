export const DISCUSSION_TYPES = {
  position_taking: {
    id: 'position_taking',
    label: 'Position Taking',
    description: 'Agents take opposing stances on a claim',
  },
  deepening: {
    id: 'deepening',
    label: 'Deepening',
    description: 'Agents probe a critical question more deeply',
  },
  connecting: {
    id: 'connecting',
    label: 'Connecting',
    description: 'Agents bring in concrete situations and generalize',
  },
} as const;

export type DiscussionType = keyof typeof DISCUSSION_TYPES;

export const THREAD_CONFIG = {
  minParticipantsForDiscussion: 2,
  defaultTurns: 4,
  additionalTurns: 4,
  maxTurns: 20,
} as const;

export const SEED_CONFIG = {
  targetCount: { min: 5, max: 6 },
  overlapLevels: ['exact', 'paragraph', 'section', 'thematic'] as const,
} as const;
