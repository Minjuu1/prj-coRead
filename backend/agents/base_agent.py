from typing import AsyncIterator
from services import llm_service

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


class DynamicAgentInstance:
    """Dynamic agent instantiated from a paper-specific agent config."""

    def __init__(self, agent_config: dict):
        self._id = agent_config["id"]
        self._system_prompt = agent_config.get("system_prompt", "")

    @property
    def agent_id(self) -> str:
        return self._id

    async def stream(
        self,
        user_message: str,
        history: list[dict],
        thread_context: str = "",
    ) -> AsyncIterator[str]:
        messages = [{"role": "system", "content": self._system_prompt}]
        if thread_context:
            messages.append({
                "role": "system",
                "content": f"[토론 맥락]\n{thread_context}",
            })
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        async for token in llm_service.stream(_MODEL, messages):
            yield token
