"""
Dynamic Agent Generation — 논문에서 토론 최적화된 에이전트 생성

두 단계 접근:
1. 논문의 contested axes (다르게 읽힐 수 있는 판단 지점) 파악
2. 각 axis에서 다른 입장을 취할 에이전트 선발 (인식론/가치 다양성 보장)

프롬프트: backend/prompts/pipeline/agent_gen.py
"""
import json
import logging
import re

logger = logging.getLogger(__name__)

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}
_INTRO_CHARS = 5000

# Abstract/Intro + Conclusion/Discussion 우선 포함할 섹션 키워드
_PRIORITY_SECTIONS = ("abstract", "introduction", "conclusion", "discussion", "summary", "implications")
_SKIP_SECTIONS = ("references", "acknowledgment", "appendix", "bibliography")


def _build_paper_context(chunks: list) -> str:
    """
    Abstract + Intro + Conclusion/Discussion 섹션 우선 포함.
    총 ~5000자로 논문 전체 스코프를 대표하는 텍스트 구성.
    """
    priority = []
    rest = []

    for c in chunks:
        section = c.get("section", "").lower()
        if any(k in section for k in _SKIP_SECTIONS):
            continue
        entry = (c.get("section", ""), c.get("content", ""))
        if any(k in section for k in _PRIORITY_SECTIONS):
            priority.append(entry)
        else:
            rest.append(entry)

    ordered = priority + rest
    parts = []
    total = 0
    for section, content in ordered:
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

    paper_context = _build_paper_context(chunks)
    prompt = get_prompt(paper_context)

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=3000,
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
            "core_value": a.get("core_value", ""),
            "default_skepticism": a.get("default_skepticism", ""),
            "system_prompt": a.get("system_prompt", ""),
            "color_index": i,
        })

    logger.info(f"[agent_gen] generated {len(agents)} agents for {paper_id}: {[a['id'] for a in agents]}")
    return agents


def generate_agents(paper_id: str, chunks: list) -> list:
    """Sync wrapper — safe to call from a background thread."""
    import asyncio
    return asyncio.run(_generate_async(paper_id, chunks))
