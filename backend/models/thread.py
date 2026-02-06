from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


AgentId = Literal['instrumental', 'critical', 'aesthetic']
ThreadType = Literal['comment', 'discussion']
DiscussionType = Literal['position_taking', 'deepening', 'connecting']


class Anchor(BaseModel):
    sectionId: str
    startOffset: int
    endOffset: int
    snippetText: str


class MessageReference(BaseModel):
    sectionId: str
    startOffset: int
    endOffset: int
    text: str


class Message(BaseModel):
    messageId: str
    threadId: str
    author: Literal['user', 'instrumental', 'critical', 'aesthetic']
    content: str
    references: List[MessageReference] = []
    taggedAgent: Optional[AgentId] = None
    timestamp: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Thread(BaseModel):
    threadId: str
    documentId: str
    seedId: str
    threadType: ThreadType
    discussionType: Optional[DiscussionType] = None
    tensionPoint: str
    keywords: List[str] = []
    anchor: Anchor
    participants: List[AgentId]
    messages: List[Message] = []
    createdAt: datetime
    updatedAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
