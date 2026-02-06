# PRD: CoRead - Multi-Agent Reading Discussion System

## 1. 개요

### 1.1 프로젝트 이름
**CoRead** (Co-Reading with AI Agents)

### 1.2 목적
학부생이 academic reading을 할 때, 다양한 관점(stance)을 가진 AI 에이전트들의 토론을 통해 **비판적 사고와 깊은 이해**를 촉진하는 시스템

### 1.3 타겟 유저
- 아카데믹 리딩이나 deep reading이 아직 어려운 **학부생**
- Reading assignment 맥락에서 사용

### 1.4 핵심 가치
- **다관점 탐색**: 단순 요약이 아닌, 텍스트에 대한 다양한 stance의 토론 제공
- **능동적 참여**: 유저가 토론에 직접 참여하여 자신의 생각 발전
- **맥락적 학습**: 텍스트의 특정 부분에 anchoring된 토론으로 맥락 유지

---

## 2. 에이전트 설계

### 2.1 Stance-Based Personas

| Agent | Stance | 주목하는 것 | 색상 |
|-------|--------|-------------|------|
| **Instrumental** | 실용적/이해 중심 | - Key concept 식별<br>- 이해/해석 명확화<br>- 이해를 위한 gap 발견 | 🟡 노란색 (#F59E0B) |
| **Critical** | 비판적/분석 중심 | - 가정 질문하기<br>- 증거/논리 검토<br>- 함의/결과 검토 | 🔵 파란색 (#3B82F6) |
| **Aesthetic** | 연결적/확장 중심 | - 개인 경험과 연결<br>- 의미 확장<br>- 새로운 연결 생성 | 🟣 자주색 (#A855F7) |

### 2.2 에이전트 메모리 구조
각 에이전트는 **문서 세션 내에서 지속되는 메모리**를 가짐:
```
AgentMemory {
  agentId: string,
  documentId: string,
  references: [{sectionId, text, timestamp}],  // 참조한 텍스트
  thoughts: [{content, discussionId, timestamp}],  // 생각/발언
  participationHistory: [{discussionId, messageIds}]  // 참여 내역
}
```

### 2.3 턴 구성 로직
- **기본**: 각 에이전트가 inner thought 생성 → 가장 "말하고 싶은" 에이전트가 발언
- **태깅 시**: 태그된 에이전트가 즉시 응답
- **유저 참여 시**: 유저 메시지에 대해 관련 에이전트들이 순차 응답

---

## 3. 시스템 파이프라인

### 3.1 전체 파이프라인 개요
```
[PDF 업로드] → [GROBID 파싱] → [Phase 1: Annotation] → [Phase 2: Seed Formation]
                                                              ↓
[UI 렌더링] ← [Phase 4: Discussion Generation] ← [Phase 3: Thread Formation]
```

### 3.2 Phase 1: Initial Annotation (병렬)
각 에이전트가 독립적으로 문서를 읽고 annotation 생성

```
┌─────────────────────────────────────────────────────────────┐
│  Input: 파싱된 문서 (섹션별 텍스트)                          │
│                                                             │
│  🟡 Instrumental    🔵 Critical    🟣 Aesthetic             │
│       ↓                  ↓              ↓                   │
│   [≤20 annotations] [≤20 annotations] [≤20 annotations]     │
│                                                             │
│  각 annotation:                                             │
│  - type: interesting | confusing | disagree |               │
│          important | question                               │
│  - target: text (문장~문단) OR section 전체                  │
│  - related_sections: [] (cross-section인 경우)              │
│  - reasoning: 왜 이걸 annotation 했는지                      │
│                                                             │
│  Output: 총 최대 60개 annotations → 각 에이전트 메모리 저장   │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Phase 2: Seed Formation (순차)
Annotations에서 tension point를 찾아 discussion seed 형성

```
┌─────────────────────────────────────────────────────────────┐
│  Input: 60개 annotations (3 에이전트)                        │
│                                                             │
│  Step 1: Overlap Detection                                  │
│  - Level 1: exact text match                               │
│  - Level 2: same paragraph                                 │
│  - Level 3: same section                                   │
│  - Level 4: thematic similarity (LLM 판단)                  │
│                                                             │
│  Step 2: LLM Clustering & Seed Generation                  │
│  - 겹치는 annotations 그룹핑                                │
│  - 각 그룹에서 tension point 추출                           │
│  - Discussion Type 결정:                                    │
│    • position_taking: 주장에 대해 반대 입장                  │
│    • deepening: 비판적 질문 깊이 파고들기                    │
│    • connecting: 구체적 상황 연결 & 일반화                   │
│                                                             │
│  Output: 5-6개 Discussion Seeds                             │
│  (2개+ 에이전트 겹침 = Discussion / 1개 에이전트 = Comment)   │
└─────────────────────────────────────────────────────────────┘
```

### 3.4 Phase 3: Thread Formation (각 seed별)
각 에이전트가 seed에 참여할지 결정

```
┌─────────────────────────────────────────────────────────────┐
│  Input: Discussion Seed                                     │
│                                                             │
│  각 에이전트:                                                │
│  - 자신의 lens로 seed 검토                                   │
│  - 참여 기준: 자신의 perspective와 관련된 gap/tension인가?   │
│  - 기여할 angle이 있는가?                                    │
│                                                             │
│  Output:                                                    │
│  - 참여 에이전트 목록                                        │
│  - 1명 참여 → Comment (💬 아닌 에이전트 색상 버튼)            │
│  - 2명+ 참여 → Discussion Thread (💬 버튼)                   │
│  - 각 에이전트 메모리 업데이트                               │
└─────────────────────────────────────────────────────────────┘
```

### 3.5 Phase 4: Discussion Generation
참여 에이전트들의 토론 생성

```
┌─────────────────────────────────────────────────────────────┐
│  Input: Discussion Thread (참여 에이전트 + seed)             │
│                                                             │
│  Discussion인 경우 (2명+):                                   │
│  - 4-6턴 토론 생성                                          │
│  - 각 턴마다 메모리 참조 & 업데이트                          │
│  - Discussion Type에 맞는 토론 전개                          │
│                                                             │
│  Comment인 경우 (1명):                                       │
│  - 단일 코멘트 생성                                          │
│  - 메모리 업데이트                                           │
│                                                             │
│  Output: Messages + Updated Agent Memory                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 유저 플로우 (Frontend)

### 4.1 Phase 1 MVP 유저 플로우
```
[유저 ID 입력] → [로그인/가입]
       ↓
[PDF 업로드] → [로딩: "문서 분석 중..."]
       ↓
[파싱 완료] → [뷰어 + Mock 데이터로 Comment/Discussion 표시]
       ↓
[Comment/Discussion 버튼 클릭] → [상세 패널 표시]
```

### 4.2 Phase 2+ 유저 플로우
```
[PDF 업로드] → [로딩: "문서 분석 중..."]
       ↓
[GROBID 파싱 완료]
       ↓
[로딩: "AI가 문서를 읽고 있습니다..." (Phase 1)]
       ↓
[로딩: "토론 주제를 찾고 있습니다..." (Phase 2-3)]
       ↓
[로딩: "토론을 생성하고 있습니다..." (Phase 4)]
       ↓
[뷰어에 Comment/Discussion 버튼 표시]
```

---

## 5. UI/UX 설계

### 5.1 레이아웃 - 초기 상태 (목록 뷰)
```
┌─────────────────────────────────────────────────────────────────┐
│  Header: CoRead | 문서 제목 | [설정]                             │
├───────────────────────────────────────┬─────────────────────────┤
│                                       │                         │
│         Text Viewer (60%)             │   Thread List (40%)     │
│                                       │                         │
│  ┌─────────────────────────────┐      │  ┌───────────────────┐ │
│  │ Introduction                 │      │  │ 💬 학생들의 비판적 │ │
│  │                              │      │  │    분석 어려움     │ │
│  │ Lorem ipsum dolor sit amet,  │      │  │ 🟡🔵🟣 | 4 msgs   │ │
│  │ consectetur adipiscing...    │      │  │ [position_taking]  │ │
│  │                         [💬] │ ←────│──│                   │ │
│  │                              │      │  ├───────────────────┤ │
│  │ Sed do eiusmod tempor...     │      │  │ 💬 방법론적 한계   │ │
│  │                         [🟡] │ ← Comment (Instrumental만)   │ │
│  │                              │      │  │ 🟡🔵 | 3 msgs     │ │
│  │ Ut enim ad minim veniam...   │      │  │ [deepening]        │ │
│  │                         [💬] │      │  ├───────────────────┤ │
│  └─────────────────────────────┘      │  │ 🟣 연결점 발견     │ │
│                                       │  │ [comment] 1 msg    │ │
│  ┌─────────────────────────────┐      │  └───────────────────┘ │
│  │ Methods                      │      │                         │
│  │ ...                     [🔵] │ ← Comment (Critical만)        │
│  └─────────────────────────────┘      │  Legend:                │
│                                       │  💬 Discussion (2+)     │
│                                       │  🟡🔵🟣 Comment (1)     │
└───────────────────────────────────────┴─────────────────────────┘
```

### 5.2 버튼 표시 규칙
| 참여 에이전트 수 | 버튼 | 목록 표시 |
|-----------------|------|----------|
| 1명 (Comment) | 에이전트 색상 (🟡/🔵/🟣) | "[comment]" 라벨 |
| 2명+ (Discussion) | 💬 | 참여 에이전트 아이콘 + Discussion Type |

### 5.3 레이아웃 - Discussion/Comment 선택 후
```
┌─────────────────────────────────────────────────────────────────┐
│  Header: CoRead | 문서 제목 | [설정]                             │
├───────────────────────────────────────┬─────────────────────────┤
│                                       │  [📋 목록]              │
│         Text Viewer (60%)             │                         │
│                                       │  Thread Detail          │
│  ┌─────────────────────────────┐      │  ─────────────────────  │
│  │ Introduction                 │      │  💬 학생들의 비판적    │
│  │                              │      │     분석 어려움        │
│  │ ██████████████████████████   │ ← 하 │  [position_taking]     │
│  │ ██████ (하이라이트) ██████   │ 이라 │                         │
│  │ ██████████████████████████   │ 이트 │  🟡 Instrumental:      │
│  │                         [💬] │      │  "이 연구에서 말하는..." │
│  │                              │      │                         │
│  │ Sed do eiusmod tempor...     │      │  🔵 Critical:          │
│  │                         [🟡] │      │  "그런데 저자가..."     │
│  │                              │      │                         │
│  │ Ut enim ad minim veniam...   │      │  🟣 Aesthetic:          │
│  │                         [💬] │      │  "이 부분을 읽으면서..." │
│  └─────────────────────────────┘      │                         │
│                                       │  ─────────────────────  │
│  ┌─────────────────────────────┐      │  [메시지 입력...]       │
│  │ Methods                      │      │  [@태그] [전송]         │
│  │ ...                     [🔵] │      │                         │
│  └─────────────────────────────┘      │  [Generate More]        │
└───────────────────────────────────────┴─────────────────────────┘
```

### 5.4 인터랙션 플로우
1. **초기 상태**: 
   - 왼쪽: 텍스트 뷰어 (섹션별 + 디스커션 버튼 [💬])
   - 오른쪽: 디스커션 목록 (주제 / 참여 에이전트 아이콘 / 메시지 수)

2. **디스커션 선택 시** (목록 아이템 클릭 OR 텍스트 내 [💬] 버튼 클릭):
   - 해당 텍스트 영역 하이라이트 (노란색 반투명 배경)
   - 오른쪽 패널이 해당 디스커션 상세로 전환
   - 상단에 [📋 목록] 버튼 표시

3. **목록으로 돌아가기**:
   - [📋 목록] 버튼 클릭 시 디스커션 목록으로 복귀
   - 하이라이트 해제

4. **디스커션 목록 아이템 표시 정보**:
   - 주제/seed (1줄 요약)
   - 참여 에이전트 아이콘 (🟡🔵🟣)
   - 메시지 수
   - (선택) level 표시 (global/section)

### 5.5 유저 인증 플로우
```
┌─────────────────────────────────────┐
│                                     │
│     Multi-Agent Reading System      │
│                                     │
│  ┌───────────────────────────────┐  │
│  │  참여자 ID를 입력하세요        │  │
│  │  [____________________]       │  │
│  │                               │  │
│  │         [시작하기]            │  │
│  └───────────────────────────────┘  │
│                                     │
└─────────────────────────────────────┘
```
- ID 입력 후 [시작하기] 클릭
- **ID가 Firebase에 없으면**: 새 유저 자동 생성 → 문서 업로드 화면으로
- **ID가 Firebase에 있으면**: 기존 데이터 로드 → 문서가 있으면 뷰어로, 없으면 업로드 화면으로
- 비밀번호 없음 (연구용)

### 5.6 문서 업로드 플로우
```
[PDF 파일 선택] → [업로드 버튼 클릭]
       ↓
[로딩: "문서 분석 중..." + 스피너]
       ↓
  ┌────┴────┐
  ↓         ↓
[성공]    [실패]
  ↓         ↓
[뷰어로   [에러 메시지 표시]
 자동     - "GROBID 파싱 실패: [상세 사유]"
 이동]    - "지원되지 않는 PDF 형식입니다"
          - [다시 업로드] 버튼
```

### 5.7 하이라이팅 스타일
- **색상**: 노란색 반투명 (`rgba(251, 191, 36, 0.3)` - Tailwind yellow-400)
- **겹침 처리**: Phase 2에서 seed 생성 시 겹치지 않도록 조정 (Phase 1에서는 mock 데이터로 겹침 없음 보장)

### 5.8 메시지 입력 UI
- **Placeholder**: "메시지를 입력하세요... (@로 에이전트 태그)"
- **@ 입력 시**: 자동완성 드롭다운 표시 (Instrumental, Critical, Aesthetic)
- **전송**: [전송] 버튼 클릭으로만 (Enter는 줄바꿈)
- **Generate More**: 텍스트 입력 영역 하단에 위치, 4턴 추가 생성, 생성 중 인터랙션 비활성화

### 5.9 UI 스타일 가이드

#### 디자인 원칙
- **미니멀 & 클린**: 불필요한 장식 요소 배제
- **콘텐츠 중심**: 텍스트 가독성 최우선
- **일관성**: 컴포넌트 스타일 통일

#### 하지 말 것 (DON'T)
- ❌ 그라데이션 배경
- ❌ 과도한 그림자 (drop-shadow)
- ❌ 이모지 남용 (버튼 아이콘 제외)
- ❌ 애니메이션 과다 사용
- ❌ 둥근 모서리 과도하게 (max: rounded-lg)
- ❌ 여러 색상 혼합
- ❌ 장식용 아이콘

#### 할 것 (DO)
- ✅ 플랫 디자인
- ✅ 충분한 여백 (whitespace)
- ✅ 명확한 시각적 계층 (typography로 구분)
- ✅ 단순한 1px 보더
- ✅ 모노톤 + 에이전트 색상만 사용

#### 컬러 팔레트
```
Background:
- Primary: #FFFFFF (white)
- Secondary: #F9FAFB (gray-50)
- Tertiary: #F3F4F6 (gray-100)

Text:
- Primary: #111827 (gray-900)
- Secondary: #6B7280 (gray-500)
- Tertiary: #9CA3AF (gray-400)

Border:
- Default: #E5E7EB (gray-200)
- Hover: #D1D5DB (gray-300)

Agent Colors (accent only):
- Instrumental: #F59E0B (amber-500)
- Critical: #3B82F6 (blue-500)
- Aesthetic: #A855F7 (purple-500)

Highlight:
- Selection: rgba(251, 191, 36, 0.2) (amber-400/20)

Status:
- Error: #EF4444 (red-500)
- Success: #10B981 (green-500)
```

#### 타이포그래피
```
Font Family: Inter (또는 system-ui)

Sizes:
- Title: 20px / font-medium
- Section Header: 16px / font-medium
- Body: 14px / font-normal
- Caption: 12px / font-normal

Line Height:
- Tight: 1.25 (headings)
- Normal: 1.5 (body)
- Relaxed: 1.75 (reading area)
```

#### 컴포넌트 스타일

**버튼**
```css
/* Primary */
background: #111827;
color: white;
padding: 8px 16px;
border-radius: 6px;
font-size: 14px;

/* Secondary */
background: white;
border: 1px solid #E5E7EB;
color: #374151;

/* Ghost (icon button) */
background: transparent;
color: #6B7280;
hover:background: #F3F4F6;
```

**카드/패널**
```css
background: white;
border: 1px solid #E5E7EB;
border-radius: 8px;
padding: 16px;
/* 그림자 최소화 또는 없음 */
```

**입력 필드**
```css
background: white;
border: 1px solid #E5E7EB;
border-radius: 6px;
padding: 10px 12px;
font-size: 14px;
focus:border-color: #9CA3AF;
focus:outline: none;
```

**에이전트 메시지**
```css
/* 메시지 버블 없음, 플랫하게 */
padding: 12px 0;
border-bottom: 1px solid #F3F4F6;

/* 에이전트 이름 옆에 색상 dot만 */
.agent-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--agent-color);
}
```

**Comment/Discussion 버튼 (텍스트 뷰어 마진)**
```css
/* Discussion */
.discussion-btn {
  width: 24px;
  height: 24px;
  background: #F3F4F6;
  border: 1px solid #E5E7EB;
  border-radius: 4px;
  color: #6B7280;
  font-size: 12px;
}

/* Comment - 에이전트 색상 dot */
.comment-btn {
  width: 24px;
  height: 24px;
  background: white;
  border: 1px solid #E5E7EB;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.comment-btn .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--agent-color);
}
```

#### 레이아웃 간격
```
Page padding: 24px
Section gap: 24px
Card padding: 16px
List item gap: 8px
Inline spacing: 8px
```

#### 아이콘
- **라이브러리**: Lucide React (minimal line icons)
- **크기**: 16px (inline), 20px (button)
- **색상**: gray-500 (기본), gray-900 (hover)
- **사용처**: 필수 기능에만 (목록, 전송, 설정 등)

---

## 6. 데이터 구조

### 6.1 User
```typescript
interface User {
  userId: string;          // 실험자 ID (간단 인증)
  createdAt: Timestamp;
  documents: string[];     // documentId 배열
}
```

### 6.2 Document
```typescript
interface Document {
  documentId: string;
  userId: string;
  title: string;
  originalPdfUrl: string;  // Firebase Storage URL
  parsedContent: {
    sections: Section[];
  };
  discussions: string[];   // discussionId 배열
  uploadedAt: Timestamp;
  lastAccessedAt: Timestamp;
}

interface Section {
  sectionId: string;
  title: string;           // "Introduction", "Methods", etc.
  content: string;         // 파싱된 텍스트
  order: number;
}
```

### 6.3 Annotation (Phase 1 파이프라인 출력)
```typescript
interface Annotation {
  annotationId: string;
  agentId: 'instrumental' | 'critical' | 'aesthetic';
  documentId: string;
  
  // Annotation 유형
  type: 'interesting' | 'confusing' | 'disagree' | 'important' | 'question';
  
  // 대상 위치
  target: {
    mode: 'text' | 'section';
    // mode가 'text'일 때 (문장~문단)
    text?: string;           
    sectionId: string;
    startOffset?: number;    // mode가 'text'일 때
    endOffset?: number;
    // mode가 'section'일 때는 sectionId만 사용
  };
  
  // Cross-section 연결 (선택)
  relatedSections?: string[];
  
  // 에이전트의 reasoning
  reasoning: string;
  
  createdAt: Timestamp;
}
```

### 6.4 DiscussionSeed (Phase 2 파이프라인 출력)
```typescript
interface DiscussionSeed {
  seedId: string;
  documentId: string;
  
  // Seed 형성 정보
  tensionPoint: string;      // LLM이 생성한 tension 요약
  discussionType: 'position_taking' | 'deepening' | 'connecting';
  keywords: string[];
  
  // 원본 annotations
  sourceAnnotationIds: string[];
  overlapLevel: 'exact' | 'paragraph' | 'section' | 'thematic';
  
  // Anchor 위치 (UI 표시용)
  anchor: {
    sectionId: string;
    startOffset?: number;
    endOffset?: number;
    snippetText?: string;
  };
  
  createdAt: Timestamp;
}
```

### 6.5 Thread (Phase 3-4 파이프라인 출력)
```typescript
// Comment (1명) 또는 Discussion (2명+)
interface Thread {
  threadId: string;
  documentId: string;
  seedId: string;            // 어떤 seed에서 생성됐는지
  
  // Thread 유형
  threadType: 'comment' | 'discussion';
  
  // Discussion 메타데이터 (seedId로부터 가져옴)
  discussionType?: 'position_taking' | 'deepening' | 'connecting';
  tensionPoint: string;
  keywords: string[];
  
  // Anchoring 정보
  anchor: {
    sectionId: string;
    startOffset: number;   // 섹션 내 plain text 기준 문자 인덱스 (0부터 시작)
    endOffset: number;     
    snippetText: string;   
  };
  
  // 참여 에이전트 (1명이면 comment, 2명+면 discussion)
  participants: ('instrumental' | 'critical' | 'aesthetic')[];
  
  // 메시지
  messages: Message[];
  
  createdAt: Timestamp;
  updatedAt: Timestamp;
}

/*
 * Thread Type 결정:
 * - participants.length === 1 → 'comment' (UI에서 에이전트 색상 버튼)
 * - participants.length >= 2 → 'discussion' (UI에서 💬 버튼)
 *
 * Offset 계산 방식:
 * - 각 섹션의 content (plain text) 기준으로 문자 인덱스 계산
 * - HTML 태그 없이 순수 텍스트만 카운트
 * - 예: section.content = "Hello world" 일 때
 *       "world"를 하이라이트하려면 startOffset=6, endOffset=11
 */
```

### 6.6 Message
```typescript
interface Message {
  messageId: string;
  threadId: string;
  
  author: 'user' | 'instrumental' | 'critical' | 'aesthetic';
  content: string;
  
  // 메시지가 참조하는 텍스트 (있는 경우)
  references: {
    sectionId: string;
    startOffset: number;
    endOffset: number;
    text: string;
  }[];
  
  // 태깅된 에이전트 (있는 경우)
  taggedAgent?: 'instrumental' | 'critical' | 'aesthetic';
  
  timestamp: Timestamp;
}
```

### 6.7 Agent Memory
```typescript
interface AgentMemory {
  memoryId: string;
  agentId: 'instrumental' | 'critical' | 'aesthetic';
  documentId: string;
  
  // Phase 1에서 생성한 annotations
  annotationIds: string[];
  
  // 참조한 텍스트들
  references: {
    sectionId: string;
    text: string;
    context: string;       // 왜 참조했는지
    timestamp: Timestamp;
  }[];
  
  // 생각/발언 기록
  thoughts: {
    content: string;
    threadId: string;
    timestamp: Timestamp;
  }[];
  
  // 참여 결정 기록 (Phase 3)
  joinDecisions: {
    seedId: string;
    decision: 'join' | 'pass';
    reasoning: string;
    contributionAngle?: string;
    timestamp: Timestamp;
  }[];
  
  updatedAt: Timestamp;
}
```

### 6.8 Interaction Log
```typescript
interface InteractionLog {
  logId: string;
  userId: string;
  documentId: string;
  sessionId: string;       // 브라우저 세션
  
  action: 
    | 'upload_document'
    | 'view_section'
    | 'click_discussion'
    | 'send_message'
    | 'tag_agent'
    | 'generate_more'
    | 'scroll'
    | 'highlight_text';
  
  metadata: {
    discussionId?: string;
    sectionId?: string;
    messageContent?: string;
    taggedAgent?: string;
    scrollPosition?: number;
    // ... 액션별 추가 데이터
  };
  
  timestamp: Timestamp;
}
```

---

## 7. 기술 스택

### 7.1 Frontend
- **Framework**: Vite + React + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand (가볍고 간단)
- **Text Viewer**: 커스텀 구현 (GROBID 파싱 결과를 HTML로 렌더링)
  - ⚠️ react-pdf는 하이라이팅/버튼 삽입이 어려워서 사용하지 않음
  - 파싱된 텍스트를 섹션별로 렌더링하는 커스텀 뷰어 구현

### 7.2 Backend
- **Framework**: Python FastAPI
- **PDF Processing**: GROBID (Docker)
  - GPU 불필요, CPU로 충분
  - 실행: `docker run -p 8070:8070 grobid/grobid:0.8.0`
- **LLM**: OpenAI API (GPT-4)

### 7.3 Infrastructure
- **Database**: Firebase Firestore
- **Storage**: Firebase Storage (PDF 파일)
- **Auth**: Firebase Auth (간단 ID 기반) 또는 커스텀
- **Hosting**: 
  - Frontend: Vercel
  - Backend: AWS EC2 / Google Cloud Run / Railway

### 7.4 개발 환경
- **Monorepo 구조** (추천):
  ```
  /project-root
  ├── /frontend          # Vite + React
  ├── /backend           # FastAPI
  ├── /shared            # 공유 타입 정의
  └── docker-compose.yml # GROBID 포함
  ```

### 7.5 Constants & Config (Single Source of Truth)

모든 설정값은 중앙 집중화하여 한 곳에서 수정하면 전체 반영되도록 설계.

#### Frontend Constants 구조
```
/frontend/src/constants/
├── agents.ts          # 에이전트 정의
├── colors.ts          # 컬러 팔레트
├── typography.ts      # 타이포그래피
├── layout.ts          # 레이아웃 간격
├── annotation.ts      # Annotation 타입
├── discussion.ts      # Discussion 타입
└── index.ts           # 통합 export
```

#### agents.ts
```typescript
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
```

#### colors.ts
```typescript
export const COLORS = {
  // Background
  bgPrimary: '#FFFFFF',
  bgSecondary: '#F9FAFB',
  bgTertiary: '#F3F4F6',
  
  // Text
  textPrimary: '#111827',
  textSecondary: '#6B7280',
  textTertiary: '#9CA3AF',
  
  // Border
  borderDefault: '#E5E7EB',
  borderHover: '#D1D5DB',
  
  // Highlight
  highlight: 'rgba(251, 191, 36, 0.2)',
  
  // Status
  error: '#EF4444',
  success: '#10B981',
} as const;
```

#### typography.ts
```typescript
export const TYPOGRAPHY = {
  fontFamily: 'Inter, system-ui, sans-serif',
  
  sizes: {
    title: '20px',
    sectionHeader: '16px',
    body: '14px',
    caption: '12px',
  },
  
  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
  },
  
  lineHeights: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
} as const;
```

#### layout.ts
```typescript
export const LAYOUT = {
  // Page
  pagePadding: 24,
  sectionGap: 24,
  
  // Components
  cardPadding: 16,
  cardBorderRadius: 8,
  
  // Spacing
  listItemGap: 8,
  inlineSpacing: 8,
  
  // Viewer
  viewerWidthPercent: 60,
  panelWidthPercent: 40,
  
  // Buttons
  buttonPadding: '8px 16px',
  buttonBorderRadius: 6,
  iconButtonSize: 24,
} as const;
```

#### annotation.ts
```typescript
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
```

#### discussion.ts
```typescript
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
  minParticipantsForDiscussion: 2,  // 2명 이상이면 discussion, 1명이면 comment
  defaultTurns: 4,
  additionalTurns: 4,  // Generate More 클릭 시
  maxTurns: 20,
} as const;

export const SEED_CONFIG = {
  targetCount: { min: 5, max: 6 },
  overlapLevels: ['exact', 'paragraph', 'section', 'thematic'] as const,
} as const;
```

#### Backend Config 구조
```
/backend/config/
├── agents.py          # 에이전트 정의
├── annotation.py      # Annotation 설정
├── discussion.py      # Discussion 설정
├── prompts.py         # 프롬프트 버전 관리
└── __init__.py
```

#### agents.py (Backend)
```python
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class AgentConfig:
    id: str
    name: str
    color: str
    stance_description: str

AGENTS: Dict[str, AgentConfig] = {
    "instrumental": AgentConfig(
        id="instrumental",
        name="Instrumental",
        color="#F59E0B",
        stance_description="""Focused on practical understanding and application.
Reading goals:
- Identifying key concepts and ideas
- Clarifying understanding and interpretation
- Finding unresolved gaps that block comprehension""",
    ),
    "critical": AgentConfig(
        id="critical",
        name="Critical",
        color="#3B82F6",
        stance_description="""Focused on questioning and analyzing.
Reading goals:
- Questioning assumptions
- Questioning evidence or reasoning
- Examining implications or consequences""",
    ),
    "aesthetic": AgentConfig(
        id="aesthetic",
        name="Aesthetic",
        color="#A855F7",
        stance_description="""Focused on connecting and expanding meaning.
Reading goals:
- Connecting the idea to personal experience
- Expanding meaning of idea
- Generating new connections or possibilities""",
    ),
}

AGENT_IDS = list(AGENTS.keys())
```

#### discussion.py (Backend)
```python
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class DiscussionTypeConfig:
    id: str
    label: str
    description: str
    prompt_guidance: str

DISCUSSION_TYPES = {
    "position_taking": DiscussionTypeConfig(
        id="position_taking",
        label="Position Taking",
        description="Agents take opposing stances on a claim",
        prompt_guidance="Take a clear stance and engage with opposing views",
    ),
    "deepening": DiscussionTypeConfig(
        id="deepening",
        label="Deepening",
        description="Agents probe a critical question more deeply",
        prompt_guidance="Ask probing questions and explore nuances",
    ),
    "connecting": DiscussionTypeConfig(
        id="connecting",
        label="Connecting",
        description="Agents bring in concrete situations and generalize",
        prompt_guidance="Bring concrete examples and make generalizations",
    ),
}

# Thread configuration
THREAD_CONFIG = {
    "min_participants_for_discussion": 2,
    "default_turns": 4,
    "additional_turns": 4,
    "max_turns": 20,
}

# Annotation configuration
ANNOTATION_CONFIG = {
    "max_per_agent": 20,
    "types": ["interesting", "confusing", "disagree", "important", "question"],
}

# Seed configuration  
SEED_CONFIG = {
    "target_count_min": 5,
    "target_count_max": 6,
    "overlap_levels": ["exact", "paragraph", "section", "thematic"],
}
```

#### 사용 예시

**Frontend - 컴포넌트에서 사용**
```tsx
import { AGENTS, AgentId } from '@/constants/agents';
import { COLORS } from '@/constants/colors';

function AgentBadge({ agentId }: { agentId: AgentId }) {
  const agent = AGENTS[agentId];
  
  return (
    <span style={{ 
      color: agent.color,
      backgroundColor: agent.colorLight 
    }}>
      {agent.name}
    </span>
  );
}
```

**Backend - 프롬프트에서 사용**
```python
from config.agents import AGENTS
from config.discussion import DISCUSSION_TYPES

def get_discussion_prompt(agent_id: str, discussion_type: str):
    agent = AGENTS[agent_id]
    disc_type = DISCUSSION_TYPES[discussion_type]
    
    return f"""
<Your Stance>
{agent.stance_description}
</Your Stance>

<Discussion Type: {disc_type.label}>
{disc_type.prompt_guidance}
</Discussion Type>
"""
```

#### 수정 시 체크리스트
설정값 변경 시 확인할 곳:
- [ ] Frontend constants 수정
- [ ] Backend config 수정  
- [ ] 타입 정의 일치 확인
- [ ] Mock 데이터 업데이트 (필요시)

---

## 8. 프롬프트 관리

### 8.1 프롬프트 디렉토리 구조
```
/backend
├── /prompts
│   ├── /agents                    # 에이전트 시스템 프롬프트
│   │   ├── instrumental.py
│   │   ├── critical.py
│   │   └── aesthetic.py
│   ├── /pipeline                  # 파이프라인 단계별 프롬프트
│   │   ├── annotation.py          # Phase 1
│   │   ├── seed_formation.py      # Phase 2
│   │   ├── join_decision.py       # Phase 3
│   │   └── discussion.py          # Phase 4
│   ├── /types.py                  # 프롬프트 파라미터 타입 정의
│   └── /utils.py                  # 공통 유틸
```

### 8.2 프롬프트 타입 정의
```typescript
// /backend/prompts/types.py

interface AgentPromptParams {
  documentTitle: string;
  currentSection: string;
  memory?: string;
  language: string;  // 기본값: "English"
}

interface AnnotationPromptParams {
  text: string;
  agentStance: string;
  maxAnnotations: number;  // 기본값: 20
}

interface SeedFormationParams {
  annotations: Annotation[];
}

interface JoinDecisionParams {
  agentStance: string;
  memory: string;
  seed: DiscussionSeed;
}

interface DiscussionPromptParams {
  seed: DiscussionSeed;
  participants: string[];
  discussionType: string;
  previousMessages: Message[];
  memory: string;
}
```

### 8.3 에이전트 시스템 프롬프트 예시
```python
# /backend/prompts/agents/instrumental.py

def get_instrumental_system_prompt(params: AgentPromptParams) -> str:
    return f"""
<Role>
You are an Instrumental reader - focused on practical understanding and application.
Your reading goals:
- Identifying key concepts and ideas
- Clarifying understanding and interpretation  
- Finding unresolved gaps that block comprehension
</Role>

<Document Context>
Title: {params.document_title}
Current Section: {params.current_section}
</Document Context>

<Memory>
{params.memory if params.memory else 'No prior context.'}
</Memory>

<Language>
Respond in {params.language}.
</Language>
""".strip()
```

### 8.4 파이프라인 프롬프트 예시

#### Phase 1: Annotation
```python
# /backend/prompts/pipeline/annotation.py

def get_annotation_prompt(params: AnnotationPromptParams) -> str:
    return f"""
<Task>
Read the following text and generate up to {params.max_annotations} annotations.
Each annotation should reflect your reading stance: {params.agent_stance}.
</Task>

<Text>
{params.text}
</Text>

<Annotation Types>
- interesting: Something that catches your attention
- confusing: Something unclear or hard to understand
- disagree: Something you question or challenge
- important: Key point that matters
- question: A question that arises from reading
</Annotation Types>

<Output Format>
Return JSON array:
[
  {{
    "type": "interesting | confusing | disagree | important | question",
    "target": {{
      "mode": "text",
      "text": "exact quoted text (sentence to paragraph)",
      "startOffset": number,
      "endOffset": number
    }},
    "reasoning": "Why you annotated this from your stance"
  }}
]
</Output Format>

<Constraints>
- Maximum {params.max_annotations} annotations
- Each target text: 1 sentence to 1 paragraph
- Annotations must reflect {params.agent_stance} perspective
</Constraints>
""".strip()
```

#### Phase 2: Seed Formation
```python
# /backend/prompts/pipeline/seed_formation.py

def get_seed_formation_prompt(params: SeedFormationParams) -> str:
    return f"""
<Task>
Analyze these annotations from 3 different reading perspectives and identify 5-6 discussion seeds.
A seed is a "tension point" where multiple perspectives converge or conflict.
</Task>

<Annotations>
{json.dumps(params.annotations, indent=2)}
</Annotations>

<Instructions>
1. Find overlaps:
   - Exact text match
   - Same paragraph
   - Same section
   - Thematic similarity

2. For each cluster, determine the discussion type:
   - position_taking: Agents can take opposing stances on a claim
   - deepening: A critical question worth probing deeper
   - connecting: Opportunity to link to concrete situations and generalize

<Output Format>
Return JSON array of 5-6 seeds:
[
  {{
    "tensionPoint": "Description of the tension/gap",
    "discussionType": "position_taking | deepening | connecting",
    "sourceAnnotationIds": ["ann_001", "ann_015"],
    "overlapLevel": "exact | paragraph | section | thematic",
    "anchor": {{
      "sectionId": "section_id",
      "startOffset": number,
      "endOffset": number,
      "snippetText": "the anchored text"
    }},
    "keywords": ["keyword1", "keyword2"]
  }}
]
</Output Format>
""".strip()
```

#### Phase 3: Join Decision
```python
# /backend/prompts/pipeline/join_decision.py

def get_join_decision_prompt(params: JoinDecisionParams) -> str:
    return f"""
<Task>
Decide whether to join this discussion based on your reading stance.
</Task>

<Your Stance>
{params.agent_stance}
</Your Stance>

<Your Memory>
{params.memory}
</Your Memory>

<Discussion Seed>
Tension Point: {params.seed.tension_point}
Type: {params.seed.discussion_type}
Keywords: {', '.join(params.seed.keywords)}
</Discussion Seed>

<Decision Criteria>
Join if:
- The tension/gap is relevant to your perspective
- You have something meaningful to contribute
- Your prior annotations touch on this topic

<Output Format>
{{
  "decision": "join | pass",
  "reasoning": "Why you decided this",
  "contributionAngle": "If joining, what angle will you bring?" 
}}
</Output Format>
""".strip()
```

#### Phase 4: Discussion Generation
```python
# /backend/prompts/pipeline/discussion.py

def get_discussion_prompt(params: DiscussionPromptParams) -> str:
    return f"""
<Task>
Continue the discussion as {params.agent_id}. Generate your next response.
</Task>

<Discussion Context>
Type: {params.discussion_type}
Tension Point: {params.seed.tension_point}
Participants: {', '.join(params.participants)}
</Discussion Context>

<Your Memory>
{params.memory}
</Your Memory>

<Previous Messages>
{format_messages(params.previous_messages)}
</Previous Messages>

<Discussion Type Guidelines>
- position_taking: Take a clear stance, engage with opposing views
- deepening: Ask probing questions, explore nuances
- connecting: Bring concrete examples, make generalizations

<Output Format>
{{
  "content": "Your message content",
  "references": [
    {{
      "sectionId": "section_id",
      "text": "quoted text if referencing document"
    }}
  ]
}}
</Output Format>
""".strip()
```

### 8.5 프롬프트 버전 관리
```python
# /backend/prompts/config.py

PROMPT_VERSIONS = {{
    "annotation": "v1.0",
    "seed_formation": "v1.0",
    "join_decision": "v1.0",
    "discussion": "v1.0",
}}

# 실험용: 다른 버전의 프롬프트를 쉽게 전환할 수 있도록
def get_prompt(prompt_type: str, version: str = None):
    version = version or PROMPT_VERSIONS[prompt_type]
    # 버전별 프롬프트 로드 로직
    ...
```

---

## 9. API 설계 (Backend)

### 9.1 유저 관련
```
POST   /api/users/login           # ID로 로그인 (없으면 자동 생성)
GET    /api/users/:id             # 유저 정보 조회
```

### 9.2 문서 관련
```
POST   /api/documents/upload      # PDF 업로드 & 파싱
GET    /api/documents/:id         # 문서 상세 조회
GET    /api/documents/:id/sections # 섹션 목록
DELETE /api/documents/:id         # 문서 삭제
```

**Note**: Phase 1에서는 단일 문서 모드. 유저당 하나의 문서만 유지. 새 문서 업로드 시 기존 문서 대체.

### 9.3 Thread 관련
```
GET    /api/documents/:id/threads         # Thread 목록 (comments + discussions)
GET    /api/threads/:id                   # Thread 상세
POST   /api/threads/:id/messages          # 메시지 전송
POST   /api/threads/:id/generate-more     # 추가 턴 생성 (4턴)
```

### 9.4 파이프라인 관련 (Phase 2+)
```
POST   /api/documents/:id/generate-annotations  # Phase 1: Annotation 생성
POST   /api/documents/:id/generate-seeds        # Phase 2: Seed 형성
POST   /api/documents/:id/generate-threads      # Phase 3-4: Thread 생성
POST   /api/documents/:id/generate-all          # Phase 1-4 전체 실행
```

---

## 10. 개발 로드맵

### Phase 1: MVP (2-3주)
**목표**: PDF 업로드 → 텍스트 뷰어 → Mock 디스커션 표시

- [ ] 프로젝트 셋업 (Vite + FastAPI + Firebase)
- [ ] GROBID Docker 환경 구성
- [ ] PDF 업로드 & 파싱 API
- [ ] 텍스트 뷰어 UI (섹션별 표시)
- [ ] Mock 디스커션 데이터 구조 확정
- [ ] 디스커션 버튼 & 패널 UI
- [ ] 텍스트 하이라이팅 연동
- [ ] Firebase 연동 (저장/로드)
- [ ] 기본 로그 수집

### Phase 2: 디스커션 자동 생성 (3-4주)
**목표**: LLM 파이프라인으로 디스커션 자동 생성

- [ ] 에이전트 시스템 프롬프트 설계
- [ ] "주목 지점" 추출 파이프라인
- [ ] 클러스터링 & seed 생성
- [ ] 디스커션 생성 파이프라인
- [ ] 레벨 분류 로직
- [ ] Anchoring 위치 매핑
- [ ] 에이전트 메모리 시스템

### Phase 3: 유저 인터랙션 (2-3주)
**목표**: 유저가 디스커션에 참여

- [ ] 메시지 전송 기능
- [ ] 에이전트 태깅 (@mention)
- [ ] 에이전트 응답 생성 (턴 로직)
- [ ] "Generate more" 기능
- [ ] 실시간 업데이트 (선택: WebSocket)

### Phase 4: 고급 기능 (선택)
- [ ] 텍스트 드래그 → 새 디스커션
- [ ] 읽기 goal 입력
- [ ] 레벨별 디스커션 모달
- [ ] 진행률 트래킹

---

## 11. 모듈화 설계 원칙

연구 시스템이므로 **파이프라인 교체가 용이**해야 함:

### 11.1 Backend 모듈 구조
```
/backend
├── /api                    # FastAPI 라우터
├── /services
│   ├── pdf_parser.py       # PDF 파싱 (GROBID 래퍼)
│   ├── discussion_generator.py  # 디스커션 생성 오케스트레이터
│   └── agent_service.py    # 에이전트 응답 생성
├── /pipelines              # 교체 가능한 파이프라인들
│   ├── /attention_extraction
│   │   ├── base.py         # 추상 인터페이스
│   │   ├── gpt4_extractor.py
│   │   └── claude_extractor.py  # 나중에 추가 가능
│   ├── /clustering
│   │   ├── base.py
│   │   └── embedding_cluster.py
│   └── /discussion_generation
│       ├── base.py
│       └── multi_agent_discussion.py
├── /agents
│   ├── base_agent.py       # 추상 에이전트
│   ├── instrumental.py
│   ├── critical.py
│   └── aesthetic.py
└── /models                 # Pydantic 모델
```

### 11.2 인터페이스 예시
```python
# /pipelines/attention_extraction/base.py
from abc import ABC, abstractmethod

class AttentionExtractor(ABC):
    @abstractmethod
    async def extract(self, sections: list[Section], agent_type: str) -> list[AttentionPoint]:
        """
        텍스트에서 에이전트 관점의 주목 지점 추출
        """
        pass
```

이렇게 하면 나중에 다른 LLM이나 방식으로 교체할 때 **새 클래스만 구현**하면 됨.

---

## 12. 데이터 흐름 & 병렬 처리

### 12.1 Phase 1 데이터 흐름 (순차)
```
[유저 ID 입력]
      ↓ (순차)
[Firebase에서 유저 조회/생성]
      ↓ (순차)
[PDF 업로드]
      ↓ (순차)
[GROBID 파싱] ─────────────────┐
      ↓ (순차)                  │ 이 전체가 완료되어야
[Firebase에 Document 저장]      │ 다음 단계 가능
      ↓ (순차)                  │
[Mock Discussion 데이터 로드] ──┘
      ↓ (순차)
[뷰어 렌더링]
```

### 12.2 Phase 2+ 데이터 흐름 (파이프라인)
```
[파싱된 텍스트]
      ↓
┌─────┼─────┐
↓     ↓     ↓        ← 3개 에이전트 병렬 처리 가능
[🟡]  [🔵]  [🟣]
주목  주목  주목
지점  지점  지점
추출  추출  추출
└─────┼─────┘
      ↓ (모두 완료 후)
[클러스터링 & Seed 생성]
      ↓ (순차)
┌─────┼─────┐
↓     ↓     ↓        ← Seed별 디스커션 생성 병렬 가능
Seed1 Seed2 Seed3
 ...   ...   ...
└─────┼─────┘
      ↓ (모두 완료 후)
[Anchoring 위치 매핑]
      ↓ (순차)
[Firebase 저장]
```

### 12.3 유저 인터랙션 데이터 흐름
```
[유저 메시지 전송]
      ↓ (순차)
[Firebase에 메시지 저장]
      ↓ (순차)
[에이전트 응답 생성 요청]
      ↓ (순차 - 턴 로직에 따라)
[응답 Firebase 저장 & UI 업데이트]
```

### 12.4 캐싱 & 저장 전략
| 데이터 | 저장 위치 | 캐싱 |
|--------|-----------|------|
| 유저 정보 | Firebase | 세션 중 메모리 |
| 문서 메타데이터 | Firebase | 세션 중 메모리 |
| 파싱된 섹션 | Firebase | 세션 중 메모리 |
| 디스커션 목록 | Firebase | 세션 중 메모리 |
| 메시지 | Firebase | 실시간 동기화 |
| PDF 원본 | Firebase Storage | X |
| 인터랙션 로그 | Firebase | 배치 저장 (5초마다) |

---

## 13. 에러 처리

### 13.1 API 에러 처리
| 에러 상황 | 프론트엔드 동작 |
|-----------|----------------|
| 네트워크 끊김 | Toast: "네트워크 연결을 확인해주세요" + 재시도 버튼 |
| GROBID 파싱 실패 | 상세 에러 메시지 표시 + [다시 업로드] 버튼 |
| Firebase 연결 실패 | Toast: "서버 연결 실패. 잠시 후 다시 시도해주세요" |
| OpenAI API 실패 | Toast: "AI 응답 생성 실패" + [재시도] 버튼 |
| 파일 크기 초과 | Toast: "파일이 너무 큽니다 (최대 10MB)" |
| 지원하지 않는 형식 | Toast: "PDF 파일만 지원됩니다" |

### 13.2 에러 메시지 형식 (개발/프로토타이핑용)
```typescript
interface ErrorResponse {
  error: {
    code: string;           // "GROBID_PARSE_ERROR"
    message: string;        // 유저에게 보여줄 메시지
    details?: string;       // 개발자용 상세 정보 (프로토타이핑 중에는 유저에게도 표시)
    timestamp: string;
  }
}
```

### 13.3 로딩 상태
| 작업 | 로딩 UI |
|------|---------|
| PDF 업로드 & 파싱 | 전체 화면 스피너 + "문서 분석 중..." |
| 디스커션 로드 | 패널 내 스피너 |
| 메시지 전송 | 전송 버튼 비활성화 + 스피너 |
| Generate More | 버튼 비활성화 + "생성 중..." |

---

## 14. 환경 설정

### 14.1 환경 변수
```bash
# Backend (.env)
OPENAI_API_KEY=sk-...
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
GROBID_URL=http://localhost:8070
ENVIRONMENT=development  # development | production

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
```

### 14.2 최소 지원 환경
- **브라우저**: Chrome 90+, Firefox 90+, Safari 14+, Edge 90+
- **화면 크기**: 최소 1024px 너비 (모바일 미지원)
- **PDF 크기**: 최대 10MB, 최대 100페이지

---

## 15. 오픈 질문 / 추후 결정 사항

### 15.1 파이프라인 관련
- [ ] 클러스터링 알고리즘 세부 구현 (embedding 기반? LLM 판단?)
- [ ] Annotation 품질 검증 방법
- [ ] Seed 개수 동적 조절 여부

### 15.2 UX 관련
- [ ] 디스커션 패널 너비 조절 가능 여부
- [ ] 여러 디스커션 동시 열기 가능 여부
- [ ] 디스커션 내 검색 기능 필요 여부

### 15.3 기술적 결정
- [ ] GROBID 파싱 실패 시 fallback (plain text? 다른 파서?)
- [ ] 실시간 업데이트 필요 시 WebSocket vs Polling
- [ ] 긴 문서 처리 전략 (페이지네이션? 가상 스크롤?)

---

## 16. 성공 지표

### 16.1 기술적 지표
- PDF 파싱 성공률 > 90%
- 디스커션 생성 latency < 30초
- 시스템 안정성 (크래시 없이 세션 유지)

### 16.2 연구 지표 (유저 스터디)
- 디스커션 참여율
- 메시지당 평균 길이
- 세션당 체류 시간
- 디스커션 클릭률

---

## Appendix A: Mock 데이터 예시

**에이전트 색상 참조:**
- `instrumental` → 🟡 노란색 (#F59E0B)
- `critical` → 🔵 파란색 (#3B82F6)  
- `aesthetic` → 🟣 자주색 (#A855F7)

### A.1 Thread (Discussion) 예시
```json
{
  "threadId": "thread_001",
  "documentId": "doc_001",
  "seedId": "seed_001",
  "threadType": "discussion",
  "discussionType": "position_taking",
  "tensionPoint": "학생들의 비판적 분석 어려움의 정의가 모호함",
  "keywords": ["critical analysis", "students", "academic reading"],
  "anchor": {
    "sectionId": "section_intro",
    "startOffset": 245,
    "endOffset": 512,
    "snippetText": "Our study reveals that students often struggle with critical analysis of academic texts..."
  },
  "participants": ["instrumental", "critical", "aesthetic"],
  "messages": [
    {
      "messageId": "msg_001",
      "threadId": "thread_001",
      "author": "instrumental",
      "content": "이 연구에서 말하는 '비판적 분석의 어려움'이 구체적으로 어떤 것인지 살펴보면, 저자는 학생들이 텍스트의 표면적 이해에 머무른다고 지적하고 있어요.",
      "references": [
        {
          "sectionId": "section_intro",
          "startOffset": 245,
          "endOffset": 320,
          "text": "Our study reveals that students often struggle with critical analysis"
        }
      ],
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "messageId": "msg_002",
      "threadId": "thread_001",
      "author": "critical",
      "content": "그런데 저자가 '비판적 분석'을 어떻게 정의하고 있는지 명확하지 않은 것 같아요. 이게 방법론적 비판인지, 논리적 분석인지, 아니면 다른 관점에서의 해석인지...",
      "references": [],
      "timestamp": "2024-01-15T10:30:15Z"
    },
    {
      "messageId": "msg_003",
      "threadId": "thread_001",
      "author": "aesthetic",
      "content": "이 부분을 읽으면서 제 경험이 떠올랐는데요, 학부 시절 논문을 읽을 때 '이해했다'고 생각했지만 실제로는 요약만 할 수 있었던 기억이 나요.",
      "references": [],
      "timestamp": "2024-01-15T10:30:30Z"
    },
    {
      "messageId": "msg_004",
      "threadId": "thread_001",
      "author": "instrumental",
      "content": "좋은 포인트예요! 그러면 Methods 섹션에서 저자가 '비판적 분석'을 어떻게 측정했는지 확인해볼 필요가 있겠네요.",
      "references": [],
      "timestamp": "2024-01-15T10:30:45Z"
    }
  ],
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:45Z"
}
```

### A.2 Thread (Comment) 예시
```json
{
  "threadId": "thread_002",
  "documentId": "doc_001",
  "seedId": "seed_002",
  "threadType": "comment",
  "tensionPoint": "샘플 크기의 적절성에 대한 의문",
  "keywords": ["sample size", "methodology"],
  "anchor": {
    "sectionId": "section_methods",
    "startOffset": 156,
    "endOffset": 234,
    "snippetText": "We recruited 15 participants from undergraduate courses..."
  },
  "participants": ["critical"],
  "messages": [
    {
      "messageId": "msg_005",
      "threadId": "thread_002",
      "author": "critical",
      "content": "15명의 참여자로 일반화할 수 있을지 의문이 드네요. 질적 연구라면 충분할 수 있지만, 저자가 주장하는 결론의 범위와 맞는지 확인이 필요해 보여요.",
      "references": [
        {
          "sectionId": "section_methods",
          "startOffset": 156,
          "endOffset": 234,
          "text": "We recruited 15 participants from undergraduate courses"
        }
      ],
      "timestamp": "2024-01-15T10:35:00Z"
    }
  ],
  "createdAt": "2024-01-15T10:35:00Z",
  "updatedAt": "2024-01-15T10:35:00Z"
}
```

### A.3 Annotation 예시
```json
{
  "annotationId": "ann_001",
  "agentId": "instrumental",
  "documentId": "doc_001",
  "type": "confusing",
  "target": {
    "mode": "text",
    "text": "Our study reveals that students often struggle with critical analysis of academic texts",
    "sectionId": "section_intro",
    "startOffset": 245,
    "endOffset": 331
  },
  "relatedSections": ["section_methods"],
  "reasoning": "The term 'critical analysis' is used without clear definition. Need to understand what specific skills or behaviors this refers to.",
  "createdAt": "2024-01-15T10:25:00Z"
}
```

### A.4 DiscussionSeed 예시
```json
{
  "seedId": "seed_001",
  "documentId": "doc_001",
  "tensionPoint": "학생들의 비판적 분석 어려움의 정의가 모호하며, 이에 대한 다양한 해석이 가능함",
  "discussionType": "position_taking",
  "keywords": ["critical analysis", "definition", "students"],
  "sourceAnnotationIds": ["ann_001", "ann_015", "ann_042"],
  "overlapLevel": "paragraph",
  "anchor": {
    "sectionId": "section_intro",
    "startOffset": 245,
    "endOffset": 512,
    "snippetText": "Our study reveals that students often struggle with critical analysis of academic texts..."
  },
  "createdAt": "2024-01-15T10:28:00Z"
}
```

---

## 17. Claude Code 구현 지침

> ⚠️ 이 PRD는 Claude Code가 읽고 구현하기 위한 문서입니다. 
> 개발 중 문제가 생기면 이 PRD를 업데이트하면서 진행하세요.

### 17.0 핵심 설계 원칙: Single Source of Truth (SSOT)

**⚠️ 이 원칙은 모든 구현에 우선 적용됩니다.**

모든 설정값, 상수, 반복되는 값은 반드시 constants/config 파일로 분리하세요.
하드코딩 금지. 같은 값이 2번 이상 나오면 무조건 분리.

#### 분리 대상 (체크리스트)
- [ ] 색상값 (에이전트 색상, UI 색상 등)
- [ ] 에이전트 정의 (ID, 이름, 설명, stance)
- [ ] Annotation/Discussion 타입 정의
- [ ] 숫자 설정값 (max 개수, 턴 수, 파일 크기 제한 등)
- [ ] API 엔드포인트 URL
- [ ] 에러 메시지, 로딩 메시지
- [ ] UI 텍스트 (라벨, placeholder, 버튼 텍스트)
- [ ] 레이아웃 수치 (간격, 비율, 사이즈)
- [ ] 타임아웃, 재시도 횟수 등 설정

#### 올바른 예시
```typescript
// ✅ GOOD - constants에서 가져오기
import { AGENTS } from '@/constants/agents';
import { MESSAGES } from '@/constants/messages';
import { LIMITS } from '@/constants/limits';

<div style={{ color: AGENTS.instrumental.color }}>
  {AGENTS.instrumental.name}
</div>

if (file.size > LIMITS.file.maxSizeMB * 1024 * 1024) {
  showError(MESSAGES.error.fileTooLarge);
}
```

#### 잘못된 예시
```typescript
// ❌ BAD - 하드코딩
<div style={{ color: '#F59E0B' }}>Instrumental</div>

if (file.size > 10 * 1024 * 1024) {
  showError('파일이 너무 큽니다');
}
```

#### 새 기능 구현 시 순서
1. 필요한 상수/설정값 파악
2. constants 파일에 먼저 정의
3. 그 다음 컴포넌트/로직 구현
4. 절대로 매직 넘버나 하드코딩 문자열 사용 금지

### 17.1 프로젝트 초기 설정

**Step 1: 디렉토리 구조 생성**
```bash
mkdir -p coread/{frontend,backend,shared}
cd coread
```

**Step 2: Frontend 초기화**
```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install zustand tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Step 3: Backend 초기화**
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install fastapi uvicorn python-multipart httpx firebase-admin openai pydantic
```

**Step 4: GROBID 실행**
```bash
docker run -d -p 8070:8070 --name grobid grobid/grobid:0.8.0
# 확인: curl http://localhost:8070/api/isalive
```

### 17.2 Phase 1 구현 순서 (MVP)

Claude Code는 다음 순서로 구현하세요:

#### Task 1: Backend - GROBID 연동 (1일)
```
파일: backend/services/pdf_parser.py
목표: PDF 업로드 → GROBID API 호출 → 섹션별 텍스트 추출

테스트 방법:
1. 샘플 PDF로 /api/documents/upload 호출
2. 응답에 sections 배열이 있는지 확인
3. 각 section에 sectionId, title, content, order가 있는지 확인
```

#### Task 2: Backend - Firebase 연동 (0.5일)
```
파일: backend/services/firebase_service.py
목표: Firestore에 Document, Discussion 저장/조회

필요한 환경변수:
- FIREBASE_CREDENTIALS_PATH (서비스 계정 JSON 경로)
```

#### Task 3: Frontend - 텍스트 뷰어 (1일)
```
파일: frontend/src/components/TextViewer.tsx
목표: 
- 섹션별로 텍스트 렌더링
- 디스커션 버튼 [💬] 위치: anchor의 마지막 문장/문단이 끝나는 라인의 오른쪽 마진
- 버튼 클릭 시 onDiscussionClick(discussionId) 콜백

주의: 
- 아직 하이라이팅은 구현하지 않아도 됨
- 스크롤 가능한 컨테이너로 구현
- 버튼은 텍스트 영역 바깥 마진에 위치 (텍스트 흐름 방해 X)
```

#### Task 4: Frontend - 디스커션 목록 패널 (0.5일)
```
파일: frontend/src/components/DiscussionList.tsx
목표:
- 디스커션 목록 표시 (주제, 에이전트 아이콘, 메시지 수)
- 클릭 시 onSelect(discussionId) 콜백
```

#### Task 5: Frontend - 디스커션 상세 패널 (1일)
```
파일: frontend/src/components/DiscussionDetail.tsx
목표:
- 메시지 목록 표시 (에이전트별 색상 구분)
- "목록으로" 버튼
- (Phase 1에서는 메시지 입력 UI만, 실제 전송은 Phase 3)
```

#### Task 6: Mock 데이터 & 통합 (0.5일)
```
파일: frontend/src/data/mockDiscussions.ts
목표:
- Appendix A의 Mock 데이터 형식으로 2-3개 디스커션 생성
- 전체 플로우 테스트
```

### 17.3 파일별 구현 가이드

#### backend/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MARDS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite 기본 포트
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from api import documents, discussions
app.include_router(documents.router, prefix="/api/documents")
app.include_router(discussions.router, prefix="/api/discussions")
```

#### backend/api/documents.py
```python
from fastapi import APIRouter, UploadFile, File
from services.pdf_parser import parse_pdf
from services.firebase_service import save_document

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...), user_id: str = ""):
    # 1. PDF를 GROBID로 파싱
    # 2. Firebase에 저장
    # 3. documentId 반환
    pass

@router.get("/{document_id}")
async def get_document(document_id: str):
    pass

@router.get("/{document_id}/sections")
async def get_sections(document_id: str):
    pass
```

#### frontend/src/App.tsx (기본 구조)
```tsx
import { useState } from 'react'
import { TextViewer } from './components/TextViewer'
import { DiscussionList } from './components/DiscussionList'
import { DiscussionDetail } from './components/DiscussionDetail'

function App() {
  const [selectedDiscussionId, setSelectedDiscussionId] = useState<string | null>(null)
  
  return (
    <div className="flex h-screen">
      {/* Left: Text Viewer (60%) */}
      <div className="w-3/5 overflow-auto border-r">
        <TextViewer 
          onDiscussionClick={(id) => setSelectedDiscussionId(id)}
          highlightedDiscussionId={selectedDiscussionId}
        />
      </div>
      
      {/* Right: Discussion Panel (40%) */}
      <div className="w-2/5 overflow-auto">
        {selectedDiscussionId ? (
          <DiscussionDetail 
            discussionId={selectedDiscussionId}
            onBack={() => setSelectedDiscussionId(null)}
          />
        ) : (
          <DiscussionList 
            onSelect={(id) => setSelectedDiscussionId(id)}
          />
        )}
      </div>
    </div>
  )
}
```

### 17.4 디버깅 & PRD 업데이트 규칙

1. **구현 중 PRD와 다른 결정을 했다면**: 
   - PRD의 해당 섹션을 업데이트
   - 변경 이유를 주석으로 기록

2. **새로운 데이터 필드가 필요하다면**:
   - Section 5 (데이터 구조)에 추가
   - 관련 API도 Section 7에 업데이트

3. **Phase 1에서 예상치 못한 기술적 문제**:
   - Section 10 (오픈 질문)에 기록
   - 임시 해결책과 함께 문서화

### 17.5 테스트 체크리스트 (Phase 1 완료 기준)

- [ ] PDF 업로드 시 GROBID 파싱 성공
- [ ] 파싱된 섹션이 텍스트 뷰어에 표시됨
- [ ] 디스커션 버튼이 적절한 위치에 표시됨
- [ ] 디스커션 목록에서 mock 데이터가 보임
- [ ] 디스커션 클릭 시 상세 패널로 전환됨
- [ ] "목록으로" 버튼 작동
- [ ] Firebase에 데이터 저장/조회 성공
- [ ] 기본 인터랙션 로그가 Firebase에 저장됨

---

*이 PRD는 살아있는 문서입니다. 개발 진행에 따라 지속적으로 업데이트됩니다.*

*마지막 수정: 2025-02-02*
