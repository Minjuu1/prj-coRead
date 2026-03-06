import type { AgentId } from '../constants/agents';
import type { AnnotationType } from '../constants/annotation';

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

// Message
export interface Message {
  messageId: string;
  threadId: string;
  author: 'user' | AgentId;
  content: string;
  references: MessageReference[];
  taggedAgent?: AgentId;
  annotationType?: AnnotationType;
  referencedAnnotationIds?: string[];
  timestamp: string;
}

// Thread (Comment or Discussion)
export interface Thread {
  threadId: string;
  documentId: string;
  sourceReactionId: string;
  sourceAnnotationIds: string[];
  threadType: 'comment' | 'discussion';
  keywords: string[];
  anchor: Anchor;
  participants: AgentId[];
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

// Visible Annotation (anchored to text, visible to users)
export interface VisibleAnnotation {
  annotationId: string;
  documentId: string;
  agentId: AgentId;
  annotationType: AnnotationType;
  sectionId: string;
  sectionTitle: string;
  startOffset: number;
  endOffset: number;
  snippetText: string;
  reasoning: string;
  createdAt: string;
}

// Cross-Reading Reaction
export interface CrossReadingReaction {
  reactionId: string;
  documentId: string;
  reactingAgentId: AgentId;
  targetAnnotationId: string;
  targetAgentId: AgentId;
  targetAnnotationType: AnnotationType;
  reactionText: string;
  reactionAnnotationType: AnnotationType;
  ownAnnotationIds: string[];
  ownAnnotationTexts: string[];
  isStrong: boolean;
  sectionId: string;
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
