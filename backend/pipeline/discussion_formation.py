"""
Discussion Formation — cross-agent contested excerpts에서 토론 thread 생성

cross_reading 결과(ContestedExcerpt list)를 입력으로 받아 LLM에 전달.
chunk_id와 verbatim excerpt는 LLM 출력에 의존하지 않고 contested_excerpt에서 직접 사용.
→ chunk_id mismatch, excerpt 요약/수정 문제 원천 차단.

프롬프트: backend/prompts/pipeline/discussion_formation.py
"""
import json
import logging
import re
import uuid

logger = logging.getLogger(__name__)

_MODEL = {"provider": "openai", "model": "gpt-4o-mini"}


def _build_prompt_text(contested_excerpts: list) -> str:
    """
    LLM 입력 텍스트 구성.
    각 contested excerpt를 인덱스(E0, E1, ...)로 식별 + conflict analysis 결과 포함.
    LLM이 chunk_id를 직접 출력하지 않게 함.
    """
    parts = []
    for i, ce in enumerate(contested_excerpts):
        conflict_type = ce.get("conflict_type", "")
        conflict_intensity = ce.get("conflict_intensity", "")
        key_tension = ce.get("key_tension", "")
        tension_pair = ce.get("tension_pair", [])

        ann_lines = []
        for ann in ce["annotations"]:
            ann_lines.append(
                f"  [{ann['agent_id']} / {ann['annotation_type']}]\n"
                f"  quote: \"{ann.get('quote', '')}\"\n"
                f"  {ann['content']}"
            )

        conflict_info = ""
        if conflict_type and conflict_type != "none":
            conflict_info = (
                f"CONFLICT_TYPE: {conflict_type} ({conflict_intensity})\n"
                f"KEY_TENSION: {key_tension}\n"
            )
            if tension_pair:
                conflict_info += f"TENSION_PAIR: {' vs '.join(tension_pair)}\n"

        parts.append(
            f"=== EXCERPT E{i} ===\n"
            f"SECTION: {ce['section']}\n"
            f"EXCERPT: \"{ce['excerpt']}\"\n"
            + conflict_info +
            f"ANNOTATIONS:\n" + "\n\n".join(ann_lines)
        )
    return "\n\n".join(parts)


def _parse_raw(raw: str) -> list:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"```$", "", raw.strip())
    return json.loads(raw).get("threads", [])


async def _form_async(
    paper_id: str,
    contested_excerpts: list,
    agents: list,
) -> list:
    from services import llm_service
    from prompts.pipeline.discussion_formation import get_prompt

    if not contested_excerpts:
        logger.warning(f"[discussion_formation] no contested excerpts for {paper_id}")
        return []

    agent_names = ", ".join(f"{a['name']}({a['id']})" for a in agents)
    prompt_text = _build_prompt_text(contested_excerpts)
    prompt = get_prompt(prompt_text, agent_names)

    try:
        raw = await llm_service.complete(
            _MODEL,
            [{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        threads_raw = _parse_raw(raw)
    except Exception as e:
        logger.error(f"[discussion_formation] LLM/parse error for {paper_id}: {e}")
        return []

    valid_agent_ids = {a["id"] for a in agents}

    # excerpt_index → contested_excerpt 매핑
    excerpt_map = {f"E{i}": ce for i, ce in enumerate(contested_excerpts)}

    threads = []
    for t in threads_raw[:7]:
        excerpt_index = t.get("excerpt_index", "").strip()
        open_q = t.get("open_question", "").strip()

        if not open_q:
            continue

        seed_messages = [
            m for m in t.get("seed_messages", [])
            if m.get("author") in valid_agent_ids and m.get("content")
        ]
        if not seed_messages:
            continue

        # chunk_id와 excerpt는 LLM 출력 대신 contested_excerpt에서 직접 가져옴
        ce = excerpt_map.get(excerpt_index)
        if ce is None:
            # fallback: excerpt_index가 없거나 잘못됐을 때 첫 번째 excerpt 사용
            ce = contested_excerpts[0] if contested_excerpts else {}

        threads.append({
            "id": str(uuid.uuid4()),
            "paperId": paper_id,
            "chunkId": ce.get("chunk_id", ""),
            "contestablePoint": ce.get("excerpt", ""),   # 항상 verbatim 원문
            "openQuestion": open_q,
            "suggestedAgent": t.get("suggested_agent", seed_messages[0]["author"]),
            "seedAnnotationSummaries": [],
            "seedMessages": seed_messages,
            "status": "open",
            "chunkRects": ce.get("rects", []),           # 항상 올바른 rects
            "chunkContent": ce.get("content", "")[:400],
            "chunkSection": ce.get("section", ""),
            "conflictType": ce.get("conflict_type", ""),
        })

    logger.info(f"[discussion_formation] {len(threads)} threads formed for {paper_id}")
    return threads


def form_discussions(
    paper_id: str,
    contested_excerpts: list,
    agents: list,
) -> list:
    """Sync wrapper — safe to call from a background thread."""
    import asyncio
    return asyncio.run(_form_async(paper_id, contested_excerpts, agents))
