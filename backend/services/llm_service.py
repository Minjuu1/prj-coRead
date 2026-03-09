"""
LLM Service — provider-agnostic streaming interface.

model_config: {"provider": "openai"|"anthropic"|"google", "model": str}
messages: OpenAI-format list [{"role": "system"|"user"|"assistant", "content": str}, ...]
"""
import os
from typing import AsyncIterator

# ── OpenAI ──────────────────────────────────────────────────────────────────
from openai import AsyncOpenAI

_openai_client: AsyncOpenAI | None = None

def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


# ── Anthropic ────────────────────────────────────────────────────────────────
from anthropic import AsyncAnthropic

_anthropic_client: AsyncAnthropic | None = None

def _get_anthropic() -> AsyncAnthropic:
    global _anthropic_client
    if _anthropic_client is None:
        _anthropic_client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _anthropic_client


# ── Google ───────────────────────────────────────────────────────────────────
from google import genai as google_genai
from google.genai import types as google_types

_google_client: google_genai.Client | None = None

def _get_google() -> google_genai.Client:
    global _google_client
    if _google_client is None:
        _google_client = google_genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    return _google_client


# ── Shared helpers ────────────────────────────────────────────────────────────

def _extract_system(messages: list[dict]) -> tuple[str, list[dict]]:
    """OpenAI-format messages → (system_prompt, conv_messages)."""
    system = ""
    conv = []
    for m in messages:
        if m["role"] == "system":
            system += m["content"] + "\n"
        else:
            conv.append(m)
    return system.strip(), conv


def _to_google_contents(conv_messages: list[dict]) -> list[dict]:
    """OpenAI conv_messages → Google contents format."""
    result = []
    for m in conv_messages:
        role = "model" if m["role"] == "assistant" else "user"
        result.append({"role": role, "parts": [{"text": m["content"]}]})
    return result


# ── Public API ────────────────────────────────────────────────────────────────

async def stream(model_config: dict, messages: list[dict]) -> AsyncIterator[str]:
    """
    Stream tokens from the specified provider.
    messages는 OpenAI 포맷 (system 포함). provider별 변환은 내부에서 처리.
    """
    provider = model_config["provider"]
    model = model_config["model"]

    if provider == "openai":
        async for token in _stream_openai(model, messages):
            yield token

    elif provider == "anthropic":
        async for token in _stream_anthropic(model, messages):
            yield token

    elif provider == "google":
        async for token in _stream_google(model, messages):
            yield token

    else:
        raise ValueError(f"Unknown provider: {provider}")


async def complete(model_config: dict, messages: list[dict], max_tokens: int = 10) -> str:
    """Non-streaming single completion. 라우팅 등 짧은 응답용."""
    provider = model_config["provider"]
    model = model_config["model"]

    if provider == "openai":
        resp = await _get_openai().chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0,
        )
        return resp.choices[0].message.content.strip()

    elif provider == "anthropic":
        system, conv = _extract_system(messages)
        resp = await _get_anthropic().messages.create(
            model=model,
            system=system,
            messages=conv,
            max_tokens=max_tokens,
        )
        return resp.content[0].text.strip()

    elif provider == "google":
        system, conv = _extract_system(messages)
        contents = _to_google_contents(conv)
        resp = await _get_google().aio.models.generate_content(
            model=model,
            contents=contents,
            config=google_types.GenerateContentConfig(
                system_instruction=system if system else None,
                max_output_tokens=max_tokens,
            ),
        )
        return resp.text.strip()

    else:
        raise ValueError(f"Unknown provider: {provider}")


# ── Provider implementations ──────────────────────────────────────────────────

async def _stream_openai(model: str, messages: list[dict]) -> AsyncIterator[str]:
    stream = await _get_openai().chat.completions.create(
        model=model,
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def _stream_anthropic(model: str, messages: list[dict]) -> AsyncIterator[str]:
    system, conv = _extract_system(messages)
    async with _get_anthropic().messages.stream(
        model=model,
        system=system,
        messages=conv,
        max_tokens=1024,
    ) as s:
        async for text in s.text_stream:
            yield text


async def _stream_google(model: str, messages: list[dict]) -> AsyncIterator[str]:
    system, conv = _extract_system(messages)
    contents = _to_google_contents(conv)
    async for chunk in await _get_google().aio.models.generate_content_stream(
        model=model,
        contents=contents,
        config=google_types.GenerateContentConfig(
            system_instruction=system if system else None,
        ),
    ):
        if chunk.text:
            yield chunk.text
