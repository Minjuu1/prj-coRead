AGENT_DESCRIPTIONS = {
    "critical": (
        "schema: 텍스트는 항상 숨겨진 가정을 갖고 있다. "
        "attention: assumption, claim-evidence gap, 논리적 일관성. "
        "goal: 이 주장이 성립하는가, 전제가 무엇인가."
    ),
    "instrumental": (
        "schema: 텍스트는 정보를 추출하기 위한 것. "
        "attention: 핵심 주장, 근거, 적용 가능성. "
        "goal: 텍스트에서 실용적으로 쓸 수 있는 것이 무엇인가."
    ),
    "aesthetic": (
        "schema: 텍스트는 독자와 사회적 맥락 사이의 대화다. "
        "attention: 사회적 함의, 다른 맥락과의 연결, 언어에 담긴 가치관. "
        "goal: 이 텍스트가 더 넓은 맥락에서 어떤 의미인가."
    ),
}


def get_prompt(
    contestable_point: str,
    significance: str,
    reading_a: str,
    reading_b: str,
    open_question: str,
    suggested_agent: str,
) -> str:
    agents = list(AGENT_DESCRIPTIONS.keys())
    # suggested agent leads the conversation
    ordered = [suggested_agent] + [a for a in agents if a != suggested_agent]

    agent_block = "\n".join(
        f"- {agent.upper()}: {AGENT_DESCRIPTIONS[agent]}"
        for agent in ordered
    )

    return f"""You are generating a seed discussion between AI reading agents about a contestable point in an academic paper.

CONTESTABLE POINT (verbatim from paper):
"{contestable_point}"

WHY THIS OPENS DEBATE:
{significance}

TWO READINGS — neither is correct:
Reading A: {reading_a}
Reading B: {reading_b}

OPEN QUESTION FOR READERS:
{open_question}

AGENTS (each has a different interpretive schema):
{agent_block}

Generate a 2-3 turn conversation between these agents about the contestable point.
The conversation should feel like it just started — no preamble, no meta-commentary.
The agents should embody the tension between Reading A and Reading B through their schemas.

Conversation rules:
- Each agent speaks from their schema. They don't just agree — they find where their interpretations diverge.
- No transitional agreement ("good point", "interesting", "I agree but"). Each turn must add friction or build in a direction that creates tension.
- The conversation does NOT resolve. It should end mid-argument or with a sharp question.
- Responses are concise: 2-4 sentences per turn.
- {suggested_agent.upper()} speaks first.

Respond with valid JSON only — no markdown fences:
{{
  "messages": [
    {{"author": "critical" | "instrumental" | "aesthetic", "content": "..."}},
    ...
  ]
}}"""
