"""
Cross-Reading Reaction Model

Captures one agent's reaction to another agent's annotation.
Generated during Phase 2 (Cross-Reading).
"""
from pydantic import BaseModel
from typing import List
from datetime import datetime

from .thread import AgentId, AnnotationType


class CrossReadingReaction(BaseModel):
    """
    A reaction from one agent to another agent's annotation.
    Strong reactions (with own annotation references) become discussion starters.
    """
    reactionId: str
    documentId: str

    # Who reacted
    reactingAgentId: AgentId

    # What they reacted to
    targetAnnotationId: str
    targetAgentId: AgentId
    targetAnnotationType: AnnotationType

    # The reaction itself
    reactionText: str  # 2-4 sentences
    reactionAnnotationType: AnnotationType  # Through their own stance lens

    # References to own annotations (key for quality filtering)
    ownAnnotationIds: List[str] = []
    ownAnnotationTexts: List[str] = []

    # Quality signal (computed structurally, not LLM-judged)
    isStrong: bool = False

    # Location context (inherited from target annotation)
    sectionId: str

    createdAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
