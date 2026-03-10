// ============================================================
// Core Types — CoRead
// 원칙: id는 DB 참조용. LLM 컨텍스트에 들어가는 건 항상 텍스트.
// ============================================================

export type AgentId = string   // dynamic per paper (e.g. "computer-scientist")
export type Author = AgentId | 'student'
export type AnnotationType = 'observation' | 'question' | 'tension'
export type PaperStatus = 'processing' | 'ready' | 'error'
export type ThreadStatus = 'locked' | 'open'

// ============================================================
// Paper
// ============================================================

export interface Paper {
  id: string
  title: string
  url: string
  status: PaperStatus
  summary?: string
  uploadedAt: Date
}

// ============================================================
// Chunk
// ============================================================

export interface Chunk {
  id: string
  paperId: string
  content: string
  section: string
  position: number        // 0.0 ~ 1.0 논문 내 상대 위치
  charStart: number
  charEnd: number
  pageStart: number
  pageEnd: number
  linkedChunks: string[]  // cross-reference chunk id 목록 (DB 참조용)
}

// ============================================================
// Annotation
// ============================================================

export interface BoundingRect {
  x1: number
  y1: number
  x2: number
  y2: number
  width: number
  height: number
}

export interface Annotation {
  id: string
  paperId: string
  chunkId: string
  agent: AgentId
  type: AnnotationType

  content: string           // LLM 생성 텍스트 (에이전트 annotation 전문)
  summary: string           // 1-2문장 압축본 → annotation_memory에 들어가는 것

  // 텍스트 anchor — 반드시 논문 원문 기반
  targetText: string        // 논문 원문 exact match (LLM 생성 텍스트 금지)
  targetStart: number
  targetEnd: number

  // PDF 렌더링용 좌표 — Phase 1에서 반드시 저장
  pageNumber: number
  boundingRect: BoundingRect
  rects: BoundingRect[]

  understandingAtTime: string
  createdAt: Date
}

// ============================================================
// RAG Source (채팅 응답에서 참조한 청크)
// ============================================================

export interface GrobidRect {
  page: number
  x1: number
  y1: number
  x2: number
  y2: number
  width: number
  height: number
}

export interface ChunkSource {
  chunkId: string
  section: string
  page: number
  content: string   // preview (200자)
  rects: GrobidRect[]
}

// react-pdf-highlighter-extended 렌더링 형식
// Annotation → PDFHighlight 변환 후 PdfHighlighter에 전달
export interface PDFHighlight {
  id: string                   // = annotation.id (= threadId for click routing)
  position: {
    boundingRect: BoundingRect & { pageNumber: number }
    rects: (BoundingRect & { pageNumber: number })[]
    pageNumber: number
  }
  content: { text: string }    // = annotation.targetText
}

// ============================================================
// Thread
// ============================================================

// ============================================================
// Dynamic Agent (generated per paper)
// ============================================================

export interface DynamicAgent {
  id: string          // slug, e.g. "computer-scientist"
  name: string        // Korean display name
  field: string       // English field name
  reading_lens: string
  system_prompt: string
  color_index: number // 0–7, for color palette
}

export interface AgentAnnotation {
  id: string
  agent_id: string
  chunk_id: string
  section: string
  position: number
  annotation_type: 'observation' | 'question' | 'tension'
  content: string
  quote: string
}

export interface SeedMessage {
  author: AgentId
  content: string
}

export interface Thread {
  id: string
  paperId: string
  chunkId: string
  contestablePoint: string          // 논쟁 지점 텍스트 (verbatim quote)
  openQuestion: string              // authentic question
  status: ThreadStatus
  createdAt: Date

  // 파이프라인 컨텍스트 (에이전트 프롬프트용 — UI 미표시)
  significance?: string
  readingA?: string                 // 두 독해 중 하나 (neither is correct)
  readingB?: string                 // 두 독해 중 하나
  suggestedAgent?: AgentId          // 기본 배정 에이전트

  // Seed 대화 (파이프라인 사전 생성)
  seedMessages?: SeedMessage[]

  // PDF 연동
  chunkRects?: GrobidRect[]
  chunkContent?: string
  chunkSection?: string
}

// ============================================================
// Message
// Firestore 서브컬렉션: threads/{threadId}/messages/{msgId}
// ============================================================

export interface Message {
  id: string
  author: Author
  content: string
  timestamp: Date
}

// ============================================================
// LearnerProfile
// ============================================================

export interface LearnerProfile {
  userId: string
  paperId: string
  threadIds: string[]
  createdAt: Date
  updatedAt: Date
}
