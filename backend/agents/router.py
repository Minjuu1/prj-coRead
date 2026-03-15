"""
Router — 사용 가능한 dynamic agents 중에서 LLM-as-a-judge로 최적 에이전트 선택.
"""
from agents.base_agent import DynamicAgentInstance
from services import llm_service

_ROUTING_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


def _build_routing_prompt(agents: list[dict]) -> str:
    agent_list = "\n".join(
        f"- {a['id']}: {a['name']} — {a.get('reading_lens', a.get('field', ''))}"
        for a in agents
    )
    return (
        "You are routing a student's question to the most relevant expert agent.\n"
        f"Available agents:\n{agent_list}\n\n"
        "Based on the student's message and conversation context, pick the most relevant agent.\n"
        "Reply with ONLY the agent id (the part before the colon above). One word, no punctuation."
    )


async def route(
    user_message: str,
    history: list,
    thread_context: str,
    agents: list[dict],
) -> str:
    """학생 메시지와 available agents를 보고 에이전트 ID 반환."""
    if not agents:
        return ""

    valid_ids = {a["id"] for a in agents}
    routing_prompt = _build_routing_prompt(agents)

    context_block = f"Thread context: {thread_context}\n" if thread_context else ""
    history_block = ""
    if history:
        for msg in history[-6:]:
            history_block += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"

    user_content = (
        f"{context_block}"
        f"Conversation history:\n{history_block}"
        f"Student's message: {user_message}"
    )

    try:
        decision = await llm_service.complete(
            _ROUTING_MODEL,
            [
                {"role": "system", "content": routing_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=10,
        )
        decision = decision.strip().lower()
        if decision in valid_ids:
            return decision
        for aid in valid_ids:
            if aid in decision:
                return aid
    except Exception:
        pass

    return agents[0]["id"]


def get_agent(agent_id: str, agents: list[dict]) -> DynamicAgentInstance:
    """agent_id에 맞는 DynamicAgentInstance 반환. 없으면 첫 번째 에이전트."""
    for a in agents:
        if a["id"] == agent_id:
            return DynamicAgentInstance(a)
    return DynamicAgentInstance(agents[0]) if agents else DynamicAgentInstance({"id": agent_id, "system_prompt": ""})
