"""
Dynamic Agent Generation — 논문 도입부에서 3-4개 분야 에이전트 생성

논문 제목 + 첫 ~3000자를 LLM에 전달 → 이 논문과 관련된 학문 분야 에이전트를 동적으로 생성.
프롬프트: backend/prompts/pipeline/agent_gen.py
"""
import json
import logging
import re
import uuid

logger = logging.getLogger(__name__)

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}
_INTRO_CHARS = 3000


def _build_intro(chunks: list) -> str:
    """앞부분 청크들을 합쳐 도입부 텍스트 구성."""
    parts = []
    total = 0
    for c in chunks:
        content = c.get("content", "")
        section = c.get("section", "")
        parts.append(f"[{section}]\n{content}")
        total += len(content)
        if total >= _INTRO_CHARS:
            break
    return "\n\n".join(parts)


def _parse_raw(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"```$", "", raw.strip())
    return json.loads(raw).get("agents", [])


async def _generate_async(paper_id: str, chunks: list) -> list:
    from services import llm_service
    from prompts.pipeline.agent_gen import get_prompt

    intro = _build_intro(chunks)
    prompt = get_prompt(intro)

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        agents_raw = _parse_raw(raw)
    except Exception as e:
        logger.error(f"[agent_gen] LLM/parse error for {paper_id}: {e}")
        return []

    agents = []
    for i, a in enumerate(agents_raw[:4]):
        agent_id = a.get("id", "").strip()
        if not agent_id:
            continue
        agents.append({
            "id": agent_id,
            "name": a.get("name", agent_id),
            "field": a.get("field", ""),
            "reading_lens": a.get("reading_lens", ""),
            "system_prompt": a.get("system_prompt", ""),
            "color_index": i,
        })

    logger.info(f"[agent_gen] generated {len(agents)} agents for {paper_id}: {[a['id'] for a in agents]}")
    return agents


def generate_agents(paper_id: str, chunks: list) -> list:
    """Sync wrapper — safe to call from a background thread."""
    import asyncio
    return asyncio.run(_generate_async(paper_id, chunks))
