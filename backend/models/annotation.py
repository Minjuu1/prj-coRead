"""
Visible Annotation Model

First-class entity stored in Firebase and displayed in frontend.
Represents an agent's annotation on the document text, visible to users as a reading layer.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from .thread import AgentId, AnnotationType


class Annotation(BaseModel):
    """
    A visible annotation made by an agent during Phase 1 (Reading).
    Anchored to specific text in the document, displayed as margin notes.
    """
    annotationId: str
    documentId: str
    agentId: AgentId

    # Annotation type from the agent's stance vocabulary
    annotationType: AnnotationType

    # Text anchor (exact position in document)
    sectionId: str
    sectionTitle: str
    startOffset: int
    endOffset: int
    snippetText: str  # The exact quoted text

    # Agent's reasoning (visible as margin note)
    reasoning: str

    createdAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
