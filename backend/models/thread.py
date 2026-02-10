from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime


AgentId = Literal['instrumental', 'critical', 'aesthetic']
ThreadType = Literal['comment', 'discussion']
DiscussionType = Literal['position_taking', 'deepening', 'connecting']
# Stance-specific annotation types:
# - Instrumental: extract, apply, clarify, gap
# - Critical: question, challenge, counter, assumption
# - Aesthetic: resonate, remind, surprise, imagine
AnnotationType = Literal[
    # Instrumental
    'extract', 'apply', 'clarify', 'gap',
    # Critical
    'question', 'challenge', 'counter', 'assumption',
    # Aesthetic
    'resonate', 'remind', 'surprise', 'imagine'
]

# TODO: Enable when implementing memory-based discussions
# AgentActionType = Literal['speak', 'search', 'reference', 'recall']


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


# TODO: Enable when implementing memory-based discussions
# class AgentAction(BaseModel):
#     type: AgentActionType
#     query: Optional[str] = None  # for search action
#     annotationId: Optional[str] = None  # for recall action
#     sectionId: Optional[str] = None  # for reference action


class Message(BaseModel):
    messageId: str
    threadId: str
    author: Literal['user', 'instrumental', 'critical', 'aesthetic']
    content: str
    references: List[MessageReference] = []
    taggedAgent: Optional[AgentId] = None
    # action: Optional[AgentAction] = None  # TODO: Enable for memory-based discussions
    annotationType: Optional[AnnotationType] = None
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
