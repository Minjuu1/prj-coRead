from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List
import json

from agents.meta_agent import get_next_agent

router = APIRouter()


class HistoryMessage(BaseModel):
    role: str      # "user" | "assistant"
    content: str


class MessageBody(BaseModel):
    content: str
    userId: str
    history: List[HistoryMessage] = []
    threadContext: str = ""    # contestablePoint + openQuestion (프론트에서 전달)


@router.post("/{thread_id}/message")
async def send_message(thread_id: str, body: MessageBody):
    """학생 메시지 수신 → 에이전트 응답 SSE 스트리밍"""
    agent = get_next_agent()

    async def generate():
        # 어떤 에이전트가 응답하는지 먼저 알려줌
        yield f"data: {json.dumps({'agent': agent.agent_id})}\n\n"

        async for token in agent.stream(
            user_message=body.content,
            history=[m.model_dump() for m in body.history],
            thread_context=body.threadContext,
        ):
            yield f"data: {json.dumps({'token': token})}\n\n"

        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
