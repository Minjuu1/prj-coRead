"""
Thread 생성 파이프라인 — 전체 논문 1회 호출

전체 청크를 논문 구조로 조합 → LLM 1회 호출 → contestable points 추출
프롬프트: backend/prompts/pipeline/thread_gen.py

verbatim 검증: LLM이 반환한 quote가 실제로 해당 청크에 있는지 확인 후
없으면 전체 청크에서 fuzzy 탐색 → sourceChunkId + rects 결정 (하이라이팅 보장)
"""
import json
import logging
import re
import uuid
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


# ──────────────────────────────────────────────
# 논문 텍스트 조합
# ──────────────────────────────────────────────

def _build_paper_text(chunks: list) -> str:
    """청크 목록 → [CHUNK:id] 태그 달린 논문 텍스트."""
    parts = []
    for c in chunks:
        chunk_id = c.get("id", "")
        section = c.get("section", "")
        content = c.get("content", "")
        parts.append(f"[CHUNK:{chunk_id}]\n[Section: {section}]\n{content}")
    return "\n---\n".join(parts)


# ──────────────────────────────────────────────
# Verbatim 검증 + chunk 매칭
# ──────────────────────────────────────────────

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def _find_chunk_for_quote(quote: str, claimed_chunk_id: str, chunks: list) -> Optional[dict]:
    """
    1. claimed_chunk_id 청크에서 verbatim 확인 (정규화 후 substring)
    2. 없으면 전체 청크에서 fuzzy 탐색
    3. 매칭 실패 시 None 반환
    """
    norm_quote = _normalize(quote)
    chunk_map = {c["id"]: c for c in chunks if "id" in c}

    # 1. Claimed chunk 직접 확인
    if claimed_chunk_id in chunk_map:
        norm_content = _normalize(chunk_map[claimed_chunk_id].get("content", ""))
        if norm_quote in norm_content:
            return chunk_map[claimed_chunk_id]

    # 2. 전체 청크 substring 탐색
    for chunk in chunks:
        norm_content = _normalize(chunk.get("content", ""))
        if norm_quote in norm_content:
            logger.debug(f"[thread_gen] quote found in chunk {chunk['id']} (not claimed {claimed_chunk_id})")
            return chunk

    # 3. Fuzzy 탐색 (앞 80자 기준)
    probe = norm_quote[:80]
    best_chunk, best_ratio = None, 0.0
    for chunk in chunks:
        norm_content = _normalize(chunk.get("content", ""))
        # 슬라이딩 윈도우
        window_len = len(probe) + 40
        for i in range(0, max(1, len(norm_content) - len(probe)), 15):
            window = norm_content[i:i + window_len]
            r = SequenceMatcher(None, probe, window).ratio()
            if r > best_ratio:
                best_ratio = r
                best_chunk = chunk
    if best_ratio >= 0.65:
        logger.debug(f"[thread_gen] fuzzy match {best_ratio:.2f} for quote '{quote[:40]}'")
        return best_chunk

    logger.warning(f"[thread_gen] no chunk found for quote: '{quote[:60]}'")
    return None


# ──────────────────────────────────────────────
# LLM 호출
# ──────────────────────────────────────────────

async def _extract_points(paper_id: str, chunks: list) -> list:
    from services import llm_service
    from prompts.pipeline.thread_gen import get_prompt

    paper_text = _build_paper_text(chunks)
    prompt = get_prompt(paper_text)

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw)
        points = data.get("points", [])
    except Exception as e:
        logger.error(f"[thread_gen] LLM/parse error for {paper_id}: {e}")
        return []

    threads = []
    for p in points:
        quote = p.get("contestablePoint", "").strip()
        if not quote:
            continue

        claimed_id = p.get("chunkId", "")
        matched_chunk = _find_chunk_for_quote(quote, claimed_id, chunks)

        if matched_chunk is None:
            logger.warning(f"[thread_gen] skipping point — quote not found in any chunk: '{quote[:60]}'")
            continue

        threads.append({
            "id": str(uuid.uuid4()),
            "paperId": paper_id,
            "chunkId": matched_chunk["id"],
            "contestablePoint": quote,
            "significance": p.get("significance", ""),
            "readingA": p.get("readingA", ""),
            "readingB": p.get("readingB", ""),
            "openQuestion": p.get("openQuestion", ""),
            "suggestedAgent": p.get("suggestedAgent", "critical"),
            "seedAnnotationSummaries": [],
            "seedMessages": [],
            "status": "open",
            "chunkRects": matched_chunk.get("rects", []),
            "chunkContent": matched_chunk.get("content", "")[:400],
            "chunkSection": matched_chunk.get("section", ""),
        })

    logger.info(f"[thread_gen] {len(threads)} threads extracted for {paper_id}")
    return threads[:8]


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

async def _generate_async(paper_id: str, chunks: list) -> list:
    candidates = [c for c in chunks if len(c.get("content", "")) > 200]
    return await _extract_points(paper_id, candidates)


def generate_threads(paper_id: str, chunks: list) -> list:
    """Sync wrapper — safe to call from a background thread."""
    import asyncio
    return asyncio.run(_generate_async(paper_id, chunks))
