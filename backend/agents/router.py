"""
Router — LLM-as-a-judge로 어느 에이전트가 응답할지 결정.
"""
from agents.base_agent import BaseAgent
from agents.critical import CriticalAgent
from agents.instrumental import InstrumentalAgent
from agents.aesthetic import AestheticAgent
from prompts.routing import ROUTING_PROMPT
from services import llm_service

_agents: dict[str, BaseAgent] = {
    "critical": CriticalAgent(),
    "instrumental": InstrumentalAgent(),
    "aesthetic": AestheticAgent(),
}

# 라우팅은 빠른 응답이 중요하므로 gpt-4o-mini 고정
_ROUTING_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


async def route(user_message: str, history: list, thread_context: str) -> str:
    """학생 메시지와 컨텍스트를 보고 에이전트 ID 반환."""
    context_block = f"Thread context: {thread_context}\n" if thread_context else ""
    history_block = ""
    if history:
        for msg in history[-6:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_block += f"{role}: {content}\n"

    user_content = (
        f"{context_block}"
        f"Conversation history:\n{history_block}"
        f"Student's message: {user_message}"
    )

    try:
        decision = await llm_service.complete(
            _ROUTING_MODEL,
            [
                {"role": "system", "content": ROUTING_PROMPT},
                {"role": "user", "content": user_content},
            ],
            max_tokens=5,
        )
        decision = decision.lower()
        if decision in _agents:
            return decision
        for key in _agents:
            if key in decision:
                return key
        return "critical"
    except Exception:
        return "critical"


def get_agent(agent_id: str) -> BaseAgent:
    return _agents.get(agent_id, _agents["critical"])
