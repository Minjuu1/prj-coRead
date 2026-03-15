"""
Cross Reading — 여러 에이전트가 동일한 구절을 인용한 지점 탐색 + conflict analysis

1. agent_reading 결과에서 같은 chunk를 2+ 에이전트가 annotation한 경우를 찾음
2. 에이전트들의 quote를 비교해서 논문 원문 verbatim 구절 추출
3. LLM 배치 호출로 각 contested chunk의 conflict type/intensity 분석
4. 진짜 충돌이 있는 excerpt만 반환 (none/low 필터링)

Output: ContestedExcerpt list — conflict_type, intensity, key_tension 포함
"""
import asyncio
import json
import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Optional

logger = logging.getLogger(__name__)

_MIN_EXCERPT_CHARS = 30
_MAX_EXCERPT_CHARS = 200
_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


# ──────────────────────────────────────────────
# Verbatim excerpt extraction (기존 로직)
# ──────────────────────────────────────────────

def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _find_verbatim_in_content(quote: str, content: str) -> Optional[str]:
    norm_q = _normalize(quote).lower()
    norm_c = _normalize(content).lower()
    raw = _normalize(content)

    idx = norm_c.find(norm_q)
    if idx != -1:
        return raw[idx:idx + len(norm_q)]
    return None


def _longest_common_substring(s1: str, s2: str, min_len: int = 20) -> Optional[str]:
    n1, n2 = _normalize(s1).lower(), _normalize(s2).lower()
    m, n = len(n1), len(n2)
    best_len, best_end = 0, 0
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if n1[i - 1] == n2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > best_len:
                    best_len = dp[i][j]
                    best_end = i
    if best_len < min_len:
        return None
    matched_lower = n1[best_end - best_len:best_end]
    start = _normalize(s1).lower().find(matched_lower)
    if start == -1:
        return None
    return _normalize(s1)[start:start + best_len]


def _pick_best_excerpt(anns: list, chunk_content: str) -> str:
    quotes = [a.get("quote", "").strip() for a in anns if a.get("quote", "").strip()]

    verbatim_quotes = []
    for q in quotes:
        found = _find_verbatim_in_content(q, chunk_content)
        if found and len(found) >= _MIN_EXCERPT_CHARS:
            verbatim_quotes.append(found)

    if not verbatim_quotes:
        return _normalize(chunk_content)[:_MAX_EXCERPT_CHARS]
    if len(verbatim_quotes) == 1:
        return verbatim_quotes[0][:_MAX_EXCERPT_CHARS]

    common = _longest_common_substring(verbatim_quotes[0], verbatim_quotes[1], min_len=_MIN_EXCERPT_CHARS)
    if common and len(common) >= _MIN_EXCERPT_CHARS:
        found = _find_verbatim_in_content(common, chunk_content)
        if found:
            return found[:_MAX_EXCERPT_CHARS]

    return max(verbatim_quotes, key=len)[:_MAX_EXCERPT_CHARS]


# ──────────────────────────────────────────────
# LLM Conflict Analysis
# ──────────────────────────────────────────────

def _build_conflict_analysis_input(candidates: list) -> str:
    """LLM 배치 분석용 텍스트 구성."""
    parts = []
    for i, ce in enumerate(candidates):
        ann_lines = []
        for ann in ce["annotations"]:
            ann_lines.append(
                f"  [{ann['agent_id']} / {ann['annotation_type']}]\n"
                f"  quote: \"{ann.get('quote', '')}\"\n"
                f"  {ann['content']}"
            )
        parts.append(
            f"=== E{i} ===\n"
            f"SECTION: {ce['section']}\n"
            f"EXCERPT: \"{ce['excerpt']}\"\n"
            f"ANNOTATIONS:\n" + "\n\n".join(ann_lines)
        )
    return "\n\n".join(parts)


async def _analyze_conflicts(candidates: list) -> list:
    """LLM 배치 호출로 각 excerpt의 conflict type/intensity 분석."""
    from services import llm_service
    from prompts.pipeline.cross_reading import get_conflict_analysis_prompt

    excerpts_text = _build_conflict_analysis_input(candidates)
    prompt = get_conflict_analysis_prompt(excerpts_text)

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"```$", "", raw.strip())
        analyses = json.loads(raw).get("analyses", [])
    except Exception as e:
        logger.warning(f"[cross_reading] conflict analysis failed: {e} — returning all candidates as medium")
        return [
            {**ce, "conflict_type": "interpretive", "conflict_intensity": "medium",
             "key_tension": "", "tension_pair": []}
            for ce in candidates
        ]

    analysis_map = {a["index"]: a for a in analyses}
    _intensity_order = {"high": 3, "medium": 2, "low": 1, "none": 0}

    enriched = []
    for i, ce in enumerate(candidates):
        analysis = analysis_map.get(f"E{i}", {})
        conflict_type = analysis.get("conflict_type", "none")
        conflict_intensity = analysis.get("conflict_intensity", "none")
        key_tension = analysis.get("key_tension", "")
        tension_pair = analysis.get("tension_pair", [])

        # none / low 제거
        if conflict_intensity in ("none", "low"):
            logger.debug(f"[cross_reading] E{i} filtered out: {conflict_intensity} ({conflict_type})")
            continue

        enriched.append({
            **ce,
            "conflict_type": conflict_type,
            "conflict_intensity": conflict_intensity,
            "key_tension": key_tension,
            "tension_pair": tension_pair,
        })

    enriched.sort(key=lambda x: _intensity_order.get(x["conflict_intensity"], 0), reverse=True)

    logger.info(
        f"[cross_reading] {len(enriched)}/{len(candidates)} excerpts kept after conflict filtering"
    )
    return enriched


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

async def _find_async(annotations: list, chunks: list) -> list:
    chunk_map = {c["id"]: c for c in chunks}
    by_chunk: dict[str, list] = defaultdict(list)
    for ann in annotations:
        by_chunk[ann["chunk_id"]].append(ann)

    candidates = []
    for chunk_id, anns in by_chunk.items():
        agent_ids = list({a["agent_id"] for a in anns})
        if len(agent_ids) < 2:
            continue

        chunk = chunk_map.get(chunk_id, {})
        chunk_content = chunk.get("content", "")
        excerpt = _pick_best_excerpt(anns, chunk_content)

        candidates.append({
            "chunk_id": chunk_id,
            "excerpt": excerpt,
            "section": chunk.get("section", ""),
            "rects": chunk.get("rects", []),
            "content": chunk_content,
            "annotations": anns,
            "agent_ids": agent_ids,
        })

    logger.info(f"[cross_reading] {len(candidates)} candidate excerpts with 2+ agents")

    if not candidates:
        return []

    return await _analyze_conflicts(candidates)


def find_contested_excerpts(annotations: list, chunks: list) -> list:
    """Sync wrapper — safe to call from a background thread."""
    return asyncio.run(_find_async(annotations, chunks))
