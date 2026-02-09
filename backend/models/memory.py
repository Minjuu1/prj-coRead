"""
Agent Memory Models

Memory system for agents to track annotations, thoughts, and interactions.
Used to provide context for discussion generation and user interactions.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

from .thread import AgentId, AnnotationType


class AnnotationMemory(BaseModel):
    """
    Memory of an annotation made during Phase 1.
    Stores what the agent noticed and why.
    """
    annotationId: str
    agentId: AgentId
    documentId: str
    sectionId: str

    # What was annotated
    targetText: str
    startOffset: int
    endOffset: int

    # Agent's perspective
    annotationType: AnnotationType
    reasoning: str  # Why the agent made this annotation

    # Metadata
    createdAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThoughtMemory(BaseModel):
    """
    Memory of a thought/statement made in a discussion.
    Tracks what the agent said and in what context.
    """
    thoughtId: str
    agentId: AgentId
    documentId: str
    threadId: str
    messageId: str

    # The thought content
    content: str
    annotationType: Optional[AnnotationType] = None

    # Context
    tensionPoint: str  # What was being discussed
    respondingTo: Optional[str] = None  # AgentId or 'user' if responding to someone

    # References made
    referencedSectionIds: List[str] = []
    referencedAnnotationIds: List[str] = []

    # Metadata
    createdAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class InteractionMemory(BaseModel):
    """
    Memory of an interaction with the user.
    Tracks user messages and agent responses.
    """
    interactionId: str
    agentId: AgentId
    documentId: str
    threadId: str

    # User's message
    userMessageId: str
    userContent: str
    wasTagged: bool  # Whether the agent was specifically tagged

    # Agent's response (if any)
    responseMessageId: Optional[str] = None
    responseContent: Optional[str] = None

    # Metadata
    createdAt: datetime
    respondedAt: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentMemory(BaseModel):
    """
    Container for all memory types for an agent on a specific document.
    """
    memoryId: str
    agentId: AgentId
    documentId: str

    # Memory collections
    annotations: List[AnnotationMemory] = []
    thoughts: List[ThoughtMemory] = []
    interactions: List[InteractionMemory] = []

    # Statistics
    totalAnnotations: int = 0
    totalThoughts: int = 0
    totalInteractions: int = 0

    # Metadata
    createdAt: datetime
    updatedAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemorySummary(BaseModel):
    """
    Summarized memory for prompt injection.
    Condensed version of agent's knowledge for LLM context.
    """
    agentId: AgentId
    documentId: str

    # Key annotations (most relevant)
    keyAnnotations: List[dict] = []  # Simplified annotation info

    # Recent thoughts
    recentThoughts: List[str] = []

    # User interaction history
    hasInteractedWithUser: bool = False
    lastUserInteraction: Optional[str] = None

    # Sections the agent has engaged with
    engagedSections: List[str] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
