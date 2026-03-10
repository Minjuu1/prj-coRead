def get_conflict_analysis_prompt(excerpts_text: str) -> str:
    return f"""당신은 학술 토론의 갈등 구조를 분석하는 전문가입니다.

아래는 여러 전문가 에이전트들이 논문의 같은 구절에 남긴 annotation 묶음입니다.
각 묶음(E0, E1, ...)에 대해, 에이전트들의 반응이 실제로 **의미 있는 충돌**을 포함하는지 분석하세요.

[annotation 묶음]
{excerpts_text}

---

각 excerpt(E0, E1, ...)에 대해 다음을 판단하세요:

**conflict_type**:
- "interpretive" — 같은 구절을 다르게 읽음 (어떤 에이전트는 A로, 다른 에이전트는 B로 해석)
- "trade-off" — 둘 다 맞지만 양립 불가 (효율성 vs. 유연성, 단기 vs. 장기 등)
- "value-based" — 무엇을 중요하게 보느냐가 다름 (실용성 vs. 이론적 엄밀성 등)
- "methodological" — 연구/설계 기준이 다름 (어떤 방법론이 적절한지)
- "none" — 에이전트들이 같은 방향으로 반응하거나 충돌이 없음

**conflict_intensity**:
- "high" — 해석이나 입장이 명확하게 충돌, 토론 가치 높음
- "medium" — 강조하는 바가 다르거나 잠재적 긴장이 있음
- "low" — 미묘한 차이, 토론 유발력 낮음
- "none" — 충돌 없음

**key_tension**: 이 excerpt에서 가장 핵심적인 긴장을 한 문장으로 (한국어)
- conflict_type이 "none"이면 빈 문자열 ""

**tension_pair**: 가장 긴장이 큰 두 에이전트의 id (있을 경우만)

엄격하게 판단하세요 — 에이전트들이 같은 것에 흥미를 보이는 것은 충돌이 아닙니다.
진짜 충돌은 "A는 이것을 문제라고 보지만 B는 이것이 장점이라고 본다" 같은 경우입니다.

모든 excerpt에 대한 분석을 JSON으로 반환하세요:
{{
  "analyses": [
    {{
      "index": "E0",
      "conflict_type": "interpretive" | "trade-off" | "value-based" | "methodological" | "none",
      "conflict_intensity": "high" | "medium" | "low" | "none",
      "key_tension": "핵심 긴장 한 문장 (한국어)",
      "tension_pair": ["agent-id-1", "agent-id-2"]
    }}
  ]
}}

JSON 외 다른 텍스트 없이 응답하세요."""
