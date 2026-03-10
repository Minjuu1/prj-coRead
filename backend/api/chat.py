from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from agents.router import route, get_agent
from db.vector_store import query as rag_query
from db.firestore import get_chunk

router = APIRouter()


class HistoryMessage(BaseModel):
    role: str      # "user" | "assistant"
    content: str


class MessageBody(BaseModel):
    content: str
    userId: str
    paperId: Optional[str] = None
    agentId: Optional[str] = None   # 지정 시 라우팅 스킵, None이면 LLM-as-a-judge
    history: List[HistoryMessage] = []
    threadContext: str = ""


def _fetch_rag(paper_id: Optional[str], query: str):
    """RAG 검색 → (context_str, sources)."""
    if not paper_id:
        return "", []
    results = rag_query(paper_id, query, n_results=4)
    if not results:
        return "", []

    parts = []
    sources = []
    for r in results:
        section = r.get("section", "")
        content = r.get("content", "")
        page = r.get("pageStart", "?")
        chunk_id = r.get("id", "")
        parts.append(f"[{section}, p.{page}]\n{content}")

        # rects는 Firebase에서 가져옴
        rects = []
        if chunk_id and paper_id:
            chunk = get_chunk(paper_id, chunk_id)
            if chunk:
                rects = chunk.get("rects", [])

        sources.append({
            "chunkId": chunk_id,
            "section": section,
            "page": page,
            "content": content[:200],  # 프리뷰용
            "rects": rects,
        })

    return "\n\n---\n\n".join(parts), sources


@router.post("/{thread_id}/message")
async def send_message(thread_id: str, body: MessageBody):
    """학생 메시지 수신 → RAG 검색 → 에이전트 응답 SSE 스트리밍 (sources 포함)"""
    rag_context, sources = _fetch_rag(body.paperId, body.content)

    combined_context = body.threadContext
    if rag_context:
        combined_context += f"\n\n[Relevant paper excerpts]\n{rag_context}"

    if body.agentId and body.agentId in ("critical", "instrumental", "aesthetic"):
        agent_id = body.agentId
    else:
        agent_id = await route(body.content, [m.model_dump() for m in body.history], combined_context)
    agent = get_agent(agent_id)

    async def generate():
        yield f"data: {json.dumps({'agent': agent.agent_id})}\n\n"

        async for token in agent.stream(
            user_message=body.content,
            history=[m.model_dump() for m in body.history],
            thread_context=combined_context,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"

        yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
