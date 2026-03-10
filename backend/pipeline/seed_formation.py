"""
Seed 대화 생성 파이프라인

thread별 에이전트 2-3명이 2-3턴 대화를 미리 생성.
학생이 스레드를 열면 이 대화가 히스토리로 표시됨.
프롬프트: backend/prompts/pipeline/seed_formation.py
"""
import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


async def _generate_seed(thread: dict) -> Optional[list]:
    from services import llm_service
    from prompts.pipeline.seed_formation import get_prompt

    prompt = get_prompt(
        contestable_point=thread.get("contestablePoint", ""),
        significance=thread.get("significance", ""),
        reading_a=thread.get("readingA", ""),
        reading_b=thread.get("readingB", ""),
        open_question=thread.get("openQuestion", ""),
        suggested_agent=thread.get("suggestedAgent", "critical"),
    )

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        messages = data.get("messages", [])

        # 유효한 author만 허용
        valid = {"critical", "instrumental", "aesthetic"}
        messages = [m for m in messages if m.get("author") in valid and m.get("content")]

        if not messages:
            return None
        return messages

    except Exception as e:
        logger.warning(f"[seed_formation] thread {thread.get('id')} skipped: {e}")
        return None


async def _generate_all_async(threads: list) -> list:
    results = await asyncio.gather(*[_generate_seed(t) for t in threads])
    enriched = []
    for thread, seed_messages in zip(threads, results):
        if seed_messages:
            thread = {**thread, "seedMessages": seed_messages}
        enriched.append(thread)

    success = sum(1 for t in enriched if t.get("seedMessages"))
    logger.info(f"[seed_formation] seed messages generated for {success}/{len(threads)} threads")
    return enriched


def generate_seed_messages(threads: list) -> list:
    """Sync wrapper — safe to call from a background thread."""
    return asyncio.run(_generate_all_async(threads))
