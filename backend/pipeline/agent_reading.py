"""
Agent Reading — 각 에이전트가 논문 전체를 읽고 annotation 생성

에이전트별로 LLM을 1회 호출, 5-8개 annotation을 생성.
에이전트들은 asyncio.gather로 병렬 처리.
프롬프트: backend/prompts/pipeline/agent_reading.py
"""
import asyncio
import json
import logging
import re
import uuid
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


def _build_paper_text(chunks: list) -> str:
    """청크 목록 → [CHUNK:id] 태그 달린 논문 텍스트 (전체)."""
    parts = []
    for c in chunks:
        chunk_id = c.get("id", "")
        section = c.get("section", "")
        content = c.get("content", "")
        parts.append(f"[CHUNK:{chunk_id}]\n[Section: {section}]\n{content}")
    return "\n---\n".join(parts)


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _find_chunk_for_quote(quote: str, claimed_id: str, chunks: list) -> Optional[dict]:
    """quote를 포함하는 chunk를 찾아 반환. 없으면 fuzzy 탐색."""
    norm_quote = _normalize(quote)
    chunk_map = {c["id"]: c for c in chunks if "id" in c}

    if claimed_id in chunk_map:
        if norm_quote in _normalize(chunk_map[claimed_id].get("content", "")):
            return chunk_map[claimed_id]

    for chunk in chunks:
        if norm_quote in _normalize(chunk.get("content", "")):
            return chunk

    probe = norm_quote[:80]
    best_chunk, best_ratio = None, 0.0
    for chunk in chunks:
        norm_content = _normalize(chunk.get("content", ""))
        for i in range(0, max(1, len(norm_content) - len(probe)), 15):
            window = norm_content[i:i + len(probe) + 40]
            r = SequenceMatcher(None, probe, window).ratio()
            if r > best_ratio:
                best_ratio = r
                best_chunk = chunk
    if best_ratio >= 0.65:
        return best_chunk

    return None


def _parse_raw(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"```$", "", raw.strip())
    return json.loads(raw).get("annotations", [])


async def _read_for_agent(agent: dict, paper_text: str, chunks: list) -> list:
    from services import llm_service
    from prompts.pipeline.agent_reading import get_prompt

    prompt = get_prompt(
        agent_name=agent["name"],
        agent_field=agent["field"],
        reading_lens=agent["reading_lens"],
        paper_text=paper_text,
    )

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        annotations_raw = _parse_raw(raw)
    except Exception as e:
        logger.warning(f"[agent_reading] agent {agent['id']} failed: {e}")
        return []

    valid_types = {"observation", "question", "tension", "alternative"}
    annotations = []
    for ann in annotations_raw:
        quote = ann.get("quote", "").strip()
        claimed_id = ann.get("chunk_id", "").strip()
        ann_type = ann.get("annotation_type", "observation")

        if not quote or ann_type not in valid_types:
            continue

        matched = _find_chunk_for_quote(quote, claimed_id, chunks)
        if matched is None:
            logger.debug(f"[agent_reading] quote not found, skipping: '{quote[:50]}'")
            continue

        annotations.append({
            "id": str(uuid.uuid4()),
            "agent_id": agent["id"],
            "chunk_id": matched["id"],
            "section": matched.get("section", ""),
            "position": matched.get("position", 0.0),
            "annotation_type": ann_type,
            "content": ann.get("content", "").strip(),
            "quote": quote,
        })

    logger.info(f"[agent_reading] agent {agent['id']}: {len(annotations)} annotations")
    return annotations


async def _read_all_async(agents: list, chunks: list) -> list:
    paper_text = _build_paper_text(chunks)
    results = await asyncio.gather(*[_read_for_agent(a, paper_text, chunks) for a in agents])
    all_annotations = [ann for agent_anns in results for ann in agent_anns]
    logger.info(f"[agent_reading] total {len(all_annotations)} annotations from {len(agents)} agents")
    return all_annotations


def run_agent_reading(agents: list, chunks: list) -> list:
    """Sync wrapper — safe to call from a background thread."""
    return asyncio.run(_read_all_async(agents, chunks))
