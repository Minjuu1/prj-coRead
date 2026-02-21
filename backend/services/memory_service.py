"""
Agent Memory Service

Manages agent memories across documents and discussions.
Stores annotations, thoughts, and interactions.
Provides context for discussion generation and user interactions.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict

from config.agents import AGENT_IDS
from models.memory import (
    AnnotationMemory,
    ThoughtMemory,
    InteractionMemory,
    AgentMemory,
    MemorySummary,
)
from services.firebase_service import firebase_service


class AgentMemoryService:
    """Service for managing agent memories."""

    def __init__(self):
        # In-memory cache for quick access
        self._memory_cache: Dict[str, Dict[str, AgentMemory]] = {}  # {documentId: {agentId: AgentMemory}}

    def _get_memory_key(self, document_id: str, agent_id: str) -> str:
        """Generate a unique key for agent memory."""
        return f"memory_{document_id}_{agent_id}"

    def _ensure_agent_memory(self, document_id: str, agent_id: str) -> AgentMemory:
        """Ensure agent memory exists for the document, create if not."""
        if document_id not in self._memory_cache:
            self._memory_cache[document_id] = {}

        if agent_id not in self._memory_cache[document_id]:
            # Try to load from storage first
            memory = self._load_memory(document_id, agent_id)
            if memory is None:
                # Create new memory
                now = datetime.utcnow()
                memory = AgentMemory(
                    memoryId=f"memory_{uuid.uuid4().hex[:8]}",
                    agentId=agent_id,
                    documentId=document_id,
                    annotations=[],
                    thoughts=[],
                    interactions=[],
                    createdAt=now,
                    updatedAt=now,
                )
            self._memory_cache[document_id][agent_id] = memory

        return self._memory_cache[document_id][agent_id]

    def _load_memory(self, document_id: str, agent_id: str) -> Optional[AgentMemory]:
        """Load agent memory from storage."""
        memory_data = firebase_service.get_agent_memory(document_id, agent_id)
        if memory_data:
            return AgentMemory(**memory_data)
        return None

    def _save_memory(self, memory: AgentMemory):
        """Save agent memory to storage."""
        firebase_service.save_agent_memory(memory.model_dump())
        # Update cache
        if memory.documentId not in self._memory_cache:
            self._memory_cache[memory.documentId] = {}
        self._memory_cache[memory.documentId][memory.agentId] = memory

    # =========================================================================
    # Annotation Memory Operations
    # =========================================================================

    def store_annotations(
        self,
        document_id: str,
        agent_id: str,
        annotations: List[dict],
    ) -> List[AnnotationMemory]:
        """
        Store annotations from Phase 1 pipeline.
        Called after annotation generation completes.
        """
        memory = self._ensure_agent_memory(document_id, agent_id)
        stored = []

        for ann in annotations:
            annotation_memory = AnnotationMemory(
                annotationId=ann.get("annotationId", f"ann_{uuid.uuid4().hex[:8]}"),
                agentId=agent_id,
                documentId=document_id,
                sectionId=ann.get("sectionId", ""),
                targetText=ann.get("targetText", ann.get("text", "")),
                startOffset=ann.get("startOffset", 0),
                endOffset=ann.get("endOffset", 0),
                annotationType=ann.get("type", ann.get("annotationType", "highlight")),
                reasoning=ann.get("reasoning", ""),
                createdAt=datetime.utcnow(),
            )
            memory.annotations.append(annotation_memory)
            stored.append(annotation_memory)

        memory.totalAnnotations = len(memory.annotations)
        memory.updatedAt = datetime.utcnow()
        self._save_memory(memory)

        return stored

    def get_annotations(
        self,
        document_id: str,
        agent_id: str,
        section_id: Optional[str] = None,
        annotation_type: Optional[str] = None,
    ) -> List[AnnotationMemory]:
        """Get annotations, optionally filtered by section or type."""
        memory = self._ensure_agent_memory(document_id, agent_id)
        annotations = memory.annotations

        if section_id:
            annotations = [a for a in annotations if a.sectionId == section_id]
        if annotation_type:
            annotations = [a for a in annotations if a.annotationType == annotation_type]

        return annotations

    def get_relevant_annotations(
        self,
        document_id: str,
        agent_id: str,
        section_ids: List[str],
        keywords: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[AnnotationMemory]:
        """
        Get annotations most relevant to a discussion context.
        Used for injecting memory into discussion prompts.
        """
        memory = self._ensure_agent_memory(document_id, agent_id)
        annotations = memory.annotations

        # Filter by sections
        if section_ids:
            section_annotations = [a for a in annotations if a.sectionId in section_ids]
        else:
            section_annotations = annotations

        # If we have keywords, score annotations by keyword relevance
        if keywords:
            def score_annotation(ann: AnnotationMemory) -> int:
                score = 0
                text = f"{ann.targetText} {ann.reasoning}".lower()
                for keyword in keywords:
                    if keyword.lower() in text:
                        score += 1
                return score

            section_annotations.sort(key=score_annotation, reverse=True)

        return section_annotations[:limit]

    # =========================================================================
    # Thought Memory Operations
    # =========================================================================

    def store_thought(
        self,
        document_id: str,
        agent_id: str,
        thread_id: str,
        message_id: str,
        content: str,
        tension_point: str,
        annotation_type: Optional[str] = None,
        responding_to: Optional[str] = None,
        referenced_section_ids: Optional[List[str]] = None,
        referenced_annotation_ids: Optional[List[str]] = None,
    ) -> ThoughtMemory:
        """
        Store a thought from a discussion message.
        Called when an agent sends a message in a discussion.
        """
        memory = self._ensure_agent_memory(document_id, agent_id)

        thought = ThoughtMemory(
            thoughtId=f"thought_{uuid.uuid4().hex[:8]}",
            agentId=agent_id,
            documentId=document_id,
            threadId=thread_id,
            messageId=message_id,
            content=content,
            annotationType=annotation_type,
            tensionPoint=tension_point,
            respondingTo=responding_to,
            referencedSectionIds=referenced_section_ids or [],
            referencedAnnotationIds=referenced_annotation_ids or [],
            createdAt=datetime.utcnow(),
        )

        memory.thoughts.append(thought)
        memory.totalThoughts = len(memory.thoughts)
        memory.updatedAt = datetime.utcnow()
        self._save_memory(memory)

        return thought

    def get_thoughts(
        self,
        document_id: str,
        agent_id: str,
        thread_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[ThoughtMemory]:
        """Get recent thoughts, optionally filtered by thread."""
        memory = self._ensure_agent_memory(document_id, agent_id)
        thoughts = memory.thoughts

        if thread_id:
            thoughts = [t for t in thoughts if t.threadId == thread_id]

        # Return most recent
        return sorted(thoughts, key=lambda t: t.createdAt, reverse=True)[:limit]

    # =========================================================================
    # Interaction Memory Operations
    # =========================================================================

    def store_interaction(
        self,
        document_id: str,
        agent_id: str,
        thread_id: str,
        user_message_id: str,
        user_content: str,
        was_tagged: bool,
    ) -> InteractionMemory:
        """
        Store a user interaction.
        Called when a user sends a message that involves an agent.
        """
        memory = self._ensure_agent_memory(document_id, agent_id)

        interaction = InteractionMemory(
            interactionId=f"interaction_{uuid.uuid4().hex[:8]}",
            agentId=agent_id,
            documentId=document_id,
            threadId=thread_id,
            userMessageId=user_message_id,
            userContent=user_content,
            wasTagged=was_tagged,
            createdAt=datetime.utcnow(),
        )

        memory.interactions.append(interaction)
        memory.totalInteractions = len(memory.interactions)
        memory.updatedAt = datetime.utcnow()
        self._save_memory(memory)

        return interaction

    def update_interaction_response(
        self,
        document_id: str,
        agent_id: str,
        interaction_id: str,
        response_message_id: str,
        response_content: str,
    ):
        """Update an interaction with the agent's response."""
        memory = self._ensure_agent_memory(document_id, agent_id)

        for interaction in memory.interactions:
            if interaction.interactionId == interaction_id:
                interaction.responseMessageId = response_message_id
                interaction.responseContent = response_content
                interaction.respondedAt = datetime.utcnow()
                break

        memory.updatedAt = datetime.utcnow()
        self._save_memory(memory)

    # =========================================================================
    # Memory Summary & Prompt Formatting
    # =========================================================================

    def get_memory_summary(
        self,
        document_id: str,
        agent_id: str,
        section_ids: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
    ) -> MemorySummary:
        """
        Get a condensed memory summary for prompt injection.
        """
        memory = self._ensure_agent_memory(document_id, agent_id)

        # Get relevant annotations
        relevant_annotations = self.get_relevant_annotations(
            document_id, agent_id, section_ids or [], keywords, limit=5
        )

        # Format annotations for summary
        key_annotations = [
            {
                "text": ann.targetText[:100] + "..." if len(ann.targetText) > 100 else ann.targetText,
                "type": ann.annotationType,
                "reasoning": ann.reasoning[:100] + "..." if len(ann.reasoning) > 100 else ann.reasoning,
            }
            for ann in relevant_annotations
        ]

        # Get recent thoughts
        recent_thoughts = [t.content for t in self.get_thoughts(document_id, agent_id, limit=3)]

        # Check user interactions
        has_interacted = len(memory.interactions) > 0
        last_interaction = None
        if memory.interactions:
            last = sorted(memory.interactions, key=lambda i: i.createdAt, reverse=True)[0]
            last_interaction = last.userContent

        # Get engaged sections
        engaged_sections = list(set(
            ann.sectionId for ann in memory.annotations
        ))

        return MemorySummary(
            agentId=agent_id,
            documentId=document_id,
            keyAnnotations=key_annotations,
            recentThoughts=recent_thoughts,
            hasInteractedWithUser=has_interacted,
            lastUserInteraction=last_interaction,
            engagedSections=engaged_sections,
        )

    def format_for_prompt(
        self,
        document_id: str,
        agent_id: str,
        section_ids: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Format agent memory as a prompt section.
        Used for injecting memory context into LLM prompts.
        """
        summary = self.get_memory_summary(document_id, agent_id, section_ids, keywords)

        lines = []
        lines.append(f"<Agent Memory: {agent_id}>")

        # Key annotations
        if summary.keyAnnotations:
            lines.append("\n<Your Previous Annotations>")
            for i, ann in enumerate(summary.keyAnnotations, 1):
                lines.append(f"{i}. [{ann['type']}] \"{ann['text']}\"")
                lines.append(f"   Reason: {ann['reasoning']}")
            lines.append("</Your Previous Annotations>")

        # Recent thoughts
        if summary.recentThoughts:
            lines.append("\n<Your Recent Statements>")
            for i, thought in enumerate(summary.recentThoughts, 1):
                lines.append(f"{i}. {thought}")
            lines.append("</Your Recent Statements>")

        # User interactions
        if summary.hasInteractedWithUser:
            lines.append("\n<User Interaction History>")
            lines.append(f"You have interacted with the user before.")
            if summary.lastUserInteraction:
                lines.append(f"Last user message to you: \"{summary.lastUserInteraction}\"")
            lines.append("</User Interaction History>")

        lines.append("</Agent Memory>")

        return "\n".join(lines)

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def initialize_for_document(self, document_id: str):
        """Initialize empty memories for all agents on a document."""
        for agent_id in AGENT_IDS:
            self._ensure_agent_memory(document_id, agent_id)

    def clear_document_memories(self, document_id: str):
        """Clear all agent memories for a document."""
        if document_id in self._memory_cache:
            del self._memory_cache[document_id]
        firebase_service.delete_document_memories(document_id)


# Singleton instance
memory_service = AgentMemoryService()
