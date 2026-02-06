from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime
import uuid

from services.firebase_service import firebase_service

router = APIRouter(prefix="/threads", tags=["threads"])


AgentId = Literal['instrumental', 'critical', 'aesthetic']


class AnchorResponse(BaseModel):
    sectionId: str
    startOffset: int
    endOffset: int
    snippetText: str


class MessageReferenceResponse(BaseModel):
    sectionId: str
    startOffset: int
    endOffset: int
    text: str


class MessageResponse(BaseModel):
    messageId: str
    threadId: str
    author: Literal['user', 'instrumental', 'critical', 'aesthetic']
    content: str
    references: List[MessageReferenceResponse]
    taggedAgent: Optional[AgentId] = None
    timestamp: str


class ThreadResponse(BaseModel):
    threadId: str
    documentId: str
    seedId: str
    threadType: Literal['comment', 'discussion']
    discussionType: Optional[Literal['position_taking', 'deepening', 'connecting']] = None
    tensionPoint: str
    keywords: List[str]
    anchor: AnchorResponse
    participants: List[AgentId]
    messages: List[MessageResponse]
    createdAt: str
    updatedAt: str


class ThreadListItem(BaseModel):
    threadId: str
    threadType: Literal['comment', 'discussion']
    discussionType: Optional[str] = None
    tensionPoint: str
    participants: List[AgentId]
    messageCount: int
    anchor: AnchorResponse


class SendMessageRequest(BaseModel):
    content: str
    taggedAgent: Optional[AgentId] = None


@router.get("/document/{document_id}", response_model=List[ThreadListItem])
async def get_document_threads(document_id: str):
    """
    Get all threads for a document.
    """
    document = firebase_service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    threads = firebase_service.get_document_threads(document_id)

    return [
        ThreadListItem(
            threadId=t["threadId"],
            threadType=t["threadType"],
            discussionType=t.get("discussionType"),
            tensionPoint=t["tensionPoint"],
            participants=t["participants"],
            messageCount=len(t.get("messages", [])),
            anchor=AnchorResponse(**t["anchor"])
        )
        for t in threads
    ]


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """
    Get thread details.
    """
    thread = firebase_service.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    return ThreadResponse(**thread)


@router.post("/{thread_id}/messages", response_model=MessageResponse)
async def send_message(thread_id: str, request: SendMessageRequest):
    """
    Send a message to a thread.
    """
    thread = firebase_service.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    message = {
        "messageId": f"msg_{uuid.uuid4().hex[:12]}",
        "threadId": thread_id,
        "author": "user",
        "content": request.content,
        "references": [],
        "taggedAgent": request.taggedAgent,
        "timestamp": datetime.utcnow().isoformat()
    }

    firebase_service.add_message_to_thread(thread_id, message)

    return MessageResponse(**message)


@router.post("/{thread_id}/generate-more", response_model=List[MessageResponse])
async def generate_more(thread_id: str):
    """
    Generate additional discussion turns. (Placeholder for Phase 2+)
    """
    thread = firebase_service.get_thread(thread_id)
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Phase 1: Return empty list (no LLM generation yet)
    # Phase 2+: Will implement actual agent discussion generation
    return []
