def get_prompt(agent_name: str, agent_field: str, reading_lens: str, paper_text: str) -> str:
    return f"""당신은 {agent_name}입니다. ({agent_field})
당신의 독서 관점: {reading_lens}

아래 논문을 당신의 관점에서 꼼꼼히 읽고, **충돌하거나 의문이 드는 지점**을 중심으로 annotation을 남기세요.

[논문 전문]
{paper_text}

---

annotation 작성 규칙:
1. 논문 전체에 걸쳐 **8~12개**의 annotation을 남기세요 (앞부분에만 몰리지 않도록)
2. quote는 반드시 논문에 실제로 등장하는 문장의 일부여야 합니다 (verbatim)
3. content는 당신의 학문적 반응 — 솔직하고 날카롭게 표현하세요 (긍정적 감탄 말고)
4. annotation_type:
   - "observation": 당신의 분야 관점에서 주목할 만한 패턴이나 선택
   - "question": 이 논문이 전제하는 것 중 더 파고들어야 할 것, 검증되지 않은 가정
   - "tension": 당신의 분야 기존 이해/연구와 충돌하거나 모순되는 것
   - "alternative": 이 논문이 선택하지 않았지만 당신의 분야에서는 더 자연스러운 다른 접근법/해석

특히 이런 질문을 하면서 읽으세요:
- 이 논문의 전제 중 {agent_field} 연구자라면 동의하지 않을 것은 무엇인가?
- 논문이 당연하게 받아들이는 것 중 실제로는 trade-off가 있는 것은?
- 다른 맥락이나 다른 분야에서 이 접근을 보면 어떤 문제가 보이는가?

JSON 형식으로 응답하세요:
{{
  "annotations": [
    {{
      "chunk_id": "[CHUNK:xxx]에서 xxx 부분",
      "annotation_type": "observation" | "question" | "tension" | "alternative",
      "content": "당신의 반응 (한국어, 2-4문장, 날카롭고 구체적으로)",
      "quote": "논문 원문에서 verbatim 인용 (30-150자)"
    }}
  ]
}}

JSON 외 다른 텍스트 없이 응답하세요."""
