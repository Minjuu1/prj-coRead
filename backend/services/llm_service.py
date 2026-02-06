"""
LLM Service for OpenAI API calls.
"""
import os
import json
from typing import Optional
from openai import AsyncOpenAI


class LLMService:
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        self.model = "gpt-4o"  # Default model

    def _ensure_client(self):
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set")
            self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        json_mode: bool = False,
    ) -> str:
        """Generate a completion from the LLM."""
        self._ensure_client()

        response_format = {"type": "json_object"} if json_mode else {"type": "text"}

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
        )

        return response.choices[0].message.content

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> dict:
        """Generate a JSON response from the LLM."""
        result = await self.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=True,
        )
        return json.loads(result)


# Singleton instance
llm_service = LLMService()
