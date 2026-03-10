def get_prompt(contested_excerpts_text: str, agent_names: str) -> str:
    return f"""당신은 학술 토론 설계자입니다. 목표: socio-cognitive conflict를 드러내는 살아있는 토론.

아래는 여러 전문가 에이전트({agent_names})가 **실제로 충돌하는 방식으로 반응한** 논문 구절들입니다.
각 excerpt에는 conflict_type과 key_tension이 분석되어 있습니다.

[충돌하는 구절과 에이전트 annotation]
{contested_excerpts_text}

---

## 토론 thread 설계 원칙

### 좋은 thread의 조건
1. **excerpt_index**: 이 thread가 다루는 구절의 인덱스 (E0, E1, ...)
2. **open_question**: thread의 핵심 쟁점을 한 문장으로 (한국어) — 이것은 토론의 "제목"이지 첫 발언이 아님
3. **seed_messages**: 에이전트들이 실제로 충돌하는 **4턴**
   - author는 agent id (이름 아님)
   - 각 발언 2-4문장, 자신의 annotation 내용을 구체적으로 활용
   - 구조: A 주장 → B 반박 → A 재반론 → B 재반박 (또는 제3 에이전트가 개입)

### conflict_type별 토론 구조

**"trade-off"** — 한 에이전트가 한쪽 가치를 방어, 다른 에이전트가 다른 가치를 방어
- 첫 발언: "이 선택은 [X]를 가능하게 하지만, [Y]라는 비용이 있다..."
- 반응: "[Y]를 비용이라고 보지 않는다. [Z] 관점에서는 오히려..."

**"interpretive"** — 첫 에이전트가 독해를 claim, 두 번째가 직접 challenge
- 첫 발언: "이 구절은 [X]를 의미한다 — [field] 관점에서는..."
- 반응: "그 독해는 [Y]를 간과한다. 이 구절이 실제로 말하는 것은..."

**"value-based"** — 에이전트들이 자신이 우선시하는 가치를 명시하며 충돌
- 첫 발언: "[field]에서 가장 중요한 것은 [V]다. 이 구절은..."
- 반응: "[V]보다 [W]가 더 근본적인 문제다. [field] 관점에서..."

**"methodological"** — 연구/설계 기준을 근거로 각자 주장
- 첫 발언: "이 방법론은 [X] 기준을 충족하지 못한다 — 왜냐하면..."
- 반응: "[X] 기준이 여기 적용 가능하다는 가정 자체가 문제다..."

### 절대 금지 (심각한 오류)
- "동의합니다", "좋은 지적이에요", "맞습니다" 등 동의 표현
- "따라서 [결론]", "이 문제는 [방법]으로 해결될 수 있다" 등 해결/결론
- 상대방 관점을 완전히 무시하는 발언 (인정하되 자신의 입장은 끝까지 유지)
- open_question을 첫 seed_message로 그대로 사용

5~7개의 thread를 JSON으로 반환하세요:
{{
  "threads": [
    {{
      "excerpt_index": "E0",
      "open_question": "이 thread의 핵심 쟁점 (한국어, 1문장)",
      "suggested_agent": "이 thread를 주도할 agent id",
      "seed_messages": [
        {{"author": "agent-id", "content": "position claim (한국어, 2-4문장)"}},
        {{"author": "agent-id", "content": "직접 반박 (한국어, 2-4문장)"}},
        {{"author": "agent-id", "content": "재반론 — 상대 반박을 인정하되 입장 유지 (한국어, 2-4문장)"}},
        {{"author": "agent-id", "content": "재반박 또는 제3 관점 개입 (한국어, 2-4문장)"}}
      ]
    }}
  ]
}}

JSON 외 다른 텍스트 없이 응답하세요."""
