from abc import ABC, abstractmethod
from typing import AsyncIterator
from services import llm_service


class BaseAgent(ABC):

    @property
    @abstractmethod
    def agent_id(self) -> str: ...

    @property
    @abstractmethod
    def model_config(self) -> dict:
        """{"provider": "openai"|"anthropic"|"google", "model": str}"""
        ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    async def stream(
        self,
        user_message: str,
        history: list[dict],          # [{"role": "user"|"assistant", "content": str}]
        thread_context: str = "",     # contestablePoint + openQuestion + RAG chunks
    ) -> AsyncIterator[str]:
        messages = [{"role": "system", "content": self.system_prompt}]
        if thread_context:
            messages.append({
                "role": "system",
                "content": f"[토론 맥락]\n{thread_context}",
            })
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        async for token in llm_service.stream(self.model_config, messages):
            yield token
