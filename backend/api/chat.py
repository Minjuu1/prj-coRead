from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

router = APIRouter()


class MessageBody(BaseModel):
    content: str
    userId: str


async def mock_stream(user_message: str):
    """개발용 mock SSE 스트림 — 실제 에이전트로 교체 예정"""
    words = f"[mock] 네, '{user_message}'에 대해 답변하겠습니다. 이 논문의 핵심 논점은...".split()
    for word in words:
        yield f"data: {json.dumps({'token': word + ' '})}\n\n"
        await asyncio.sleep(0.05)
    yield f"data: {json.dumps({'done': True})}\n\n"


@router.post("/{thread_id}/message")
async def send_message(thread_id: str, body: MessageBody):
    """학생 메시지 수신 → 에이전트 응답 SSE 스트리밍"""
    # TODO: thread 존재 확인 + status == "open" 검증
    # TODO: student Message Firestore 저장
    # TODO: meta_agent로 라우팅 → 실제 에이전트 astream

    return StreamingResponse(
        mock_stream(body.content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
