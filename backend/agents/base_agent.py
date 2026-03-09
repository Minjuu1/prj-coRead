from abc import ABC, abstractmethod
from typing import AsyncIterator, List
from openai import AsyncOpenAI
import os

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL = "gpt-4o-mini"


class BaseAgent(ABC):

    @property
    @abstractmethod
    def agent_id(self) -> str: ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    async def stream(
        self,
        user_message: str,
        history: List[dict],          # [{"role": "user"|"assistant", "content": str}]
        thread_context: str = "",     # contestablePoint + openQuestion
    ) -> AsyncIterator[str]:
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        if thread_context:
            messages.append({
                "role": "system",
                "content": f"[토론 맥락]\n{thread_context}",
            })
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        stream = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
