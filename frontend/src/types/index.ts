import type { AgentId } from '../constants/agents';
import type { DiscussionType } from '../constants/discussion';
import type { AnnotationType } from '../constants/annotation';
import type { AgentActionType } from '../constants/actions';

// User
export interface User {
  userId: string;
  createdAt: string;
  documents: string[];
}

// Section
export interface Section {
  sectionId: string;
  title: string;
  content: string;
  order: number;
  subsections?: string[];
}

// Document
export interface Document {
  documentId: string;
  userId: string;
  title: string;
  originalPdfUrl: string;
  parsedContent: {
    sections: Section[];
  };
  threads: string[];
  uploadedAt: string;
  lastAccessedAt: string;
}

// Anchor
export interface Anchor {
  sectionId: string;
  startOffset: number;
  endOffset: number;
  snippetText: string;
}

// Message Reference
export interface MessageReference {
  sectionId: string;
  startOffset: number;
  endOffset: number;
  text: string;
}

// Agent Action (what the agent did in this message)
export interface AgentAction {
  type: AgentActionType;
  query?: string; // for search action
  annotationId?: string; // for recall action
  sectionId?: string; // for reference action
}

// Message
export interface Message {
  messageId: string;
  threadId: string;
  author: 'user' | AgentId;
  content: string;
  references: MessageReference[];
  taggedAgent?: AgentId;
  action?: AgentAction; // what action the agent took
  annotationType?: AnnotationType; // annotation type used in this message
  timestamp: string;
}

// Thread (Comment or Discussion)
export interface Thread {
  threadId: string;
  documentId: string;
  seedId: string;
  threadType: 'comment' | 'discussion';
  discussionType?: DiscussionType;
  tensionPoint: string;
  keywords: string[];
  anchor: Anchor;
  participants: AgentId[];
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

// Annotation
export interface Annotation {
  annotationId: string;
  agentId: AgentId;
  documentId: string;
  type: AnnotationType;
  target: {
    mode: 'text' | 'section';
    text?: string;
    sectionId: string;
    startOffset?: number;
    endOffset?: number;
  };
  relatedSections?: string[];
  reasoning: string;
  createdAt: string;
}

// Discussion Seed
export interface DiscussionSeed {
  seedId: string;
  documentId: string;
  tensionPoint: string;
  discussionType: DiscussionType;
  keywords: string[];
  sourceAnnotationIds: string[];
  overlapLevel: 'exact' | 'paragraph' | 'section' | 'thematic';
  anchor: Anchor;
  createdAt: string;
}

// Interaction Log
export interface InteractionLog {
  logId: string;
  userId: string;
  documentId: string;
  sessionId: string;
  action:
    | 'upload_document'
    | 'view_section'
    | 'click_discussion'
    | 'send_message'
    | 'tag_agent'
    | 'generate_more'
    | 'scroll'
    | 'highlight_text';
  metadata: Record<string, unknown>;
  timestamp: string;
}
