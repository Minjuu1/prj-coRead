"""
Agent Response Service

Handles generating agent responses to user messages and "generate more" turns.
Separated from pipeline_service which handles initial generation.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from config.agents import AGENT_IDS
from services.llm_service import llm_service
from services.firebase_service import firebase_service
from services.memory_service import memory_service
from prompts.pipeline.discussion import get_user_response_prompt, get_generate_more_prompt


class AgentResponseService:
    """Handles agent responses during live discussion interaction."""

    async def generate_response_to_user(
        self,
        thread: dict,
        user_message: dict,
        document_id: str,
        sections: list[dict],
    ) -> List[dict]:
        """
        Generate agent response(s) to a user message.

        Args:
            thread: Full thread dict (with messages already including the user's message)
            user_message: The user's message {content, taggedAgent, messageId}
            document_id: Document ID for memory lookup
            sections: Document sections for context

        Returns:
            List of message dicts ready to save to Firebase
        """
        tagged_agent = user_message.get("taggedAgent")
        participants = thread.get("participants", [])

        # Determine which agents respond
        if tagged_agent and tagged_agent in participants:
            responding_agents = [tagged_agent]
        else:
            responding_agents = [p for p in participants if p in AGENT_IDS]

        if not responding_agents:
            return []

        # Build memory context
        anchor = thread.get("anchor", {})
        section_id = anchor.get("sectionId", "")
        keywords = thread.get("keywords", [])

        memory_context = {}
        for agent_id in responding_agents:
            memory_context[agent_id] = memory_service.format_for_prompt(
                document_id, agent_id,
                section_ids=[section_id] if section_id else [],
                keywords=keywords,
            )

        # Store user interaction in each responding agent's memory
        for agent_id in responding_agents:
            memory_service.store_interaction(
                document_id=document_id,
                agent_id=agent_id,
                thread_id=thread["threadId"],
                user_message_id=user_message.get("messageId", ""),
                user_content=user_message["content"],
                was_tagged=(tagged_agent == agent_id),
            )

        # Generate responses via LLM
        system_prompt, user_prompt = get_user_response_prompt(
            thread=thread,
            user_message=user_message,
            responding_agents=responding_agents,
            sections=sections,
            memory_context=memory_context,
        )

        try:
            result = await llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
            )
            raw_messages = result.get("messages", [])
        except Exception as e:
            print(f"[AgentResponse] LLM error: {e}")
            return []

        # Build message objects and store in memory
        now = datetime.utcnow().isoformat()
        messages = []
        prev_author = "user"

        for msg in raw_messages:
            author = msg.get("author", "")
            if author not in AGENT_IDS:
                continue

            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            message = {
                "messageId": message_id,
                "threadId": thread["threadId"],
                "author": author,
                "content": msg["content"],
                "references": [],
                "timestamp": now,
            }
            if msg.get("annotationType"):
                message["annotationType"] = msg["annotationType"]

            messages.append(message)

            # Store thought in agent memory
            memory_service.store_thought(
                document_id=document_id,
                agent_id=author,
                thread_id=thread["threadId"],
                message_id=message_id,
                content=msg["content"],
                source_reaction_id=thread.get("sourceReactionId", ""),
                annotation_type=msg.get("annotationType"),
                responding_to=prev_author,
                referenced_section_ids=[section_id] if section_id else [],
            )

            # Update interaction with response
            memory_service.update_interaction_response(
                document_id=document_id,
                agent_id=author,
                interaction_id="",  # Latest interaction
                response_message_id=message_id,
                response_content=msg["content"],
            )

            prev_author = author

        return messages

    async def generate_more_turns(
        self,
        thread: dict,
        document_id: str,
        sections: list[dict],
        num_turns: int = 4,
    ) -> List[dict]:
        """
        Generate additional discussion turns.

        Args:
            thread: Full thread dict with existing messages
            document_id: Document ID for memory lookup
            sections: Document sections for context
            num_turns: Number of turns to generate

        Returns:
            List of message dicts ready to save to Firebase
        """
        participants = [p for p in thread.get("participants", []) if p in AGENT_IDS]
        if not participants:
            return []

        # Build memory context
        anchor = thread.get("anchor", {})
        section_id = anchor.get("sectionId", "")
        keywords = thread.get("keywords", [])

        memory_context = {}
        for agent_id in participants:
            memory_context[agent_id] = memory_service.format_for_prompt(
                document_id, agent_id,
                section_ids=[section_id] if section_id else [],
                keywords=keywords,
            )

        # Generate via LLM
        system_prompt, user_prompt = get_generate_more_prompt(
            thread=thread,
            participants=participants,
            sections=sections,
            num_turns=num_turns,
            memory_context=memory_context,
        )

        try:
            result = await llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
            )
            raw_messages = result.get("messages", [])
        except Exception as e:
            print(f"[AgentResponse] Generate more LLM error: {e}")
            return []

        # Build message objects and store in memory
        now = datetime.utcnow().isoformat()
        messages = []
        prev_author = None

        # Get last author from existing messages for continuity
        existing_messages = thread.get("messages", [])
        if existing_messages:
            prev_author = existing_messages[-1].get("author")

        for msg in raw_messages:
            author = msg.get("author", "")
            if author not in AGENT_IDS:
                continue

            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            message = {
                "messageId": message_id,
                "threadId": thread["threadId"],
                "author": author,
                "content": msg["content"],
                "references": [],
                "timestamp": now,
            }
            if msg.get("annotationType"):
                message["annotationType"] = msg["annotationType"]

            messages.append(message)

            # Store thought in agent memory
            memory_service.store_thought(
                document_id=document_id,
                agent_id=author,
                thread_id=thread["threadId"],
                message_id=message_id,
                content=msg["content"],
                source_reaction_id=thread.get("sourceReactionId", ""),
                annotation_type=msg.get("annotationType"),
                responding_to=prev_author,
                referenced_section_ids=[section_id] if section_id else [],
            )

            prev_author = author

        return messages


# Singleton instance
agent_response_service = AgentResponseService()
