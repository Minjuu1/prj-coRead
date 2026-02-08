"""
Pipeline Service - Orchestrates the full discussion generation pipeline.
Phase 1: Annotation → Phase 2: Seed Formation → Phase 3-4: Thread Generation
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from config.agents import AGENT_IDS
from services.llm_service import llm_service
from services.firebase_service import firebase_service
from prompts.pipeline.annotation import get_annotation_prompt
from prompts.pipeline.seed_formation import get_seed_formation_prompt
from prompts.pipeline.discussion import get_discussion_prompt, get_comment_prompt


class PipelineService:
    """Orchestrates the full pipeline for generating discussions from a document."""

    async def run_full_pipeline(
        self,
        document_id: str,
        sections: list[dict],
        max_annotations_per_agent: int = 12,
        target_seeds: int = 5,
        turns_per_discussion: int = 4,
    ) -> dict:
        """
        Run the complete pipeline: Annotation → Seed Formation → Thread Generation

        Returns:
            dict with "threads" list ready to be saved
        """
        print(f"[Pipeline] Starting for document {document_id}")

        # Phase 1: Generate annotations from all agents (in parallel)
        print("[Pipeline] Phase 1: Generating annotations...")
        annotations_by_agent = await self._phase1_annotations(
            sections, max_annotations_per_agent
        )

        total_annotations = sum(len(a) for a in annotations_by_agent.values())
        print(f"[Pipeline] Phase 1 complete: {total_annotations} total annotations")

        # Phase 2: Form discussion seeds
        print("[Pipeline] Phase 2: Forming discussion seeds...")
        seeds = await self._phase2_seed_formation(
            annotations_by_agent, sections, target_seeds
        )
        print(f"[Pipeline] Phase 2 complete: {len(seeds)} seeds formed")

        # Phase 3-4: Generate threads for each seed
        print("[Pipeline] Phase 3-4: Generating discussions...")
        threads = await self._phase3_4_thread_generation(
            document_id, seeds, sections, turns_per_discussion
        )
        print(f"[Pipeline] Phase 3-4 complete: {len(threads)} threads generated")

        return {
            "annotations": annotations_by_agent,
            "seeds": seeds,
            "threads": threads,
        }

    async def _phase1_annotations(
        self, sections: list[dict], max_per_agent: int
    ) -> dict[str, list]:
        """Generate annotations from all three agents in parallel."""
        tasks = []
        for agent_id in AGENT_IDS:
            task = self._generate_agent_annotations(agent_id, sections, max_per_agent)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        annotations_by_agent = {}
        for agent_id, result in zip(AGENT_IDS, results):
            if isinstance(result, Exception):
                print(f"[Pipeline] Error generating annotations for {agent_id}: {result}")
                annotations_by_agent[agent_id] = []
            else:
                annotations_by_agent[agent_id] = result

        return annotations_by_agent

    async def _generate_agent_annotations(
        self, agent_id: str, sections: list[dict], max_annotations: int
    ) -> list[dict]:
        """Generate annotations for a single agent."""
        system_prompt, user_prompt = get_annotation_prompt(
            agent_id, sections, max_annotations
        )

        try:
            result = await llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )
            annotations = result.get("annotations", [])

            # Add agent_id to each annotation
            for ann in annotations:
                ann["agentId"] = agent_id

            return annotations
        except Exception as e:
            print(f"[Pipeline] Annotation error for {agent_id}: {e}")
            return []

    async def _phase2_seed_formation(
        self, annotations_by_agent: dict, sections: list[dict], target_count: int
    ) -> list[dict]:
        """Form discussion seeds from annotations."""
        system_prompt, user_prompt = get_seed_formation_prompt(
            annotations_by_agent, sections
        )

        try:
            result = await llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )
            seeds = result.get("seeds", [])

            # Add IDs to seeds
            for i, seed in enumerate(seeds):
                seed["seedId"] = f"seed_{uuid.uuid4().hex[:8]}"

            return seeds[:target_count]
        except Exception as e:
            print(f"[Pipeline] Seed formation error: {e}")
            return []

    async def _phase3_4_thread_generation(
        self,
        document_id: str,
        seeds: list[dict],
        sections: list[dict],
        turns_per_discussion: int,
    ) -> list[dict]:
        """Generate threads (discussions or comments) for each seed."""
        tasks = []
        for seed in seeds:
            task = self._generate_thread_for_seed(
                document_id, seed, sections, turns_per_discussion
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        threads = []
        for seed, result in zip(seeds, results):
            if isinstance(result, Exception):
                print(f"[Pipeline] Thread generation error for seed {seed.get('seedId')}: {result}")
            elif result:
                threads.append(result)

        return threads

    async def _generate_thread_for_seed(
        self,
        document_id: str,
        seed: dict,
        sections: list[dict],
        turns: int,
    ) -> Optional[dict]:
        """Generate a single thread (discussion or comment) for a seed."""
        participants = seed.get("relevantAgents", [])

        # Ensure we have valid participants
        valid_participants = [p for p in participants if p in AGENT_IDS]
        if not valid_participants:
            valid_participants = ["instrumental", "critical"]  # Default fallback

        is_discussion = len(valid_participants) >= 2
        thread_type = "discussion" if is_discussion else "comment"

        # Find section from title
        target_section = None
        for section in sections:
            if section["title"] == seed.get("sectionTitle"):
                target_section = section
                break
        if not target_section and sections:
            target_section = sections[0]

        section_id = target_section["sectionId"] if target_section else "section_0"

        # Compute anchor offset from snippetText
        anchor_info = self._compute_anchor(seed.get("snippetText", ""), target_section)

        try:
            if is_discussion:
                # Generate multi-turn discussion
                system_prompt, user_prompt = get_discussion_prompt(
                    seed, valid_participants, sections, turns
                )
                result = await llm_service.generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.8,
                )
                raw_messages = result.get("messages", [])
            else:
                # Generate single comment
                system_prompt, user_prompt = get_comment_prompt(
                    seed, valid_participants[0], sections
                )
                result = await llm_service.generate_json(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.7,
                )
                raw_messages = [{
                    "author": valid_participants[0],
                    "content": result.get("content", ""),
                    "annotationType": result.get("annotationType"),
                }]

            # Build thread object
            now = datetime.utcnow().isoformat()
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"

            messages = []
            for i, msg in enumerate(raw_messages):
                message = {
                    "messageId": f"msg_{uuid.uuid4().hex[:8]}",
                    "threadId": thread_id,
                    "author": msg["author"],
                    "content": msg["content"],
                    "references": [],
                    "timestamp": now,
                }
                # Add annotationType if present
                if "annotationType" in msg and msg["annotationType"]:
                    message["annotationType"] = msg["annotationType"]
                messages.append(message)

            thread = {
                "threadId": thread_id,
                "documentId": document_id,
                "seedId": seed["seedId"],
                "threadType": thread_type,
                "discussionType": seed.get("discussionType") if is_discussion else None,
                "tensionPoint": seed["tensionPoint"],
                "keywords": seed.get("keywords", []),
                "anchor": {
                    "sectionId": section_id,
                    "startOffset": anchor_info["startOffset"],
                    "endOffset": anchor_info["endOffset"],
                    "snippetText": anchor_info["snippetText"],
                },
                "participants": valid_participants,
                "messages": messages,
                "createdAt": now,
                "updatedAt": now,
            }

            return thread

        except Exception as e:
            print(f"[Pipeline] Thread generation error: {e}")
            return None


    def _compute_anchor(self, snippet_text: str, section: Optional[dict]) -> dict:
        """
        Compute anchor offset by finding snippet text in section content.
        If exact match fails, try to find the first sentence/phrase.
        """
        default = {"startOffset": 0, "endOffset": 100, "snippetText": snippet_text[:100] if snippet_text else ""}

        if not section or not snippet_text:
            return default

        content = section.get("content", "")
        if not content:
            return default

        # Try exact match first
        idx = content.find(snippet_text)
        if idx != -1:
            return {
                "startOffset": idx,
                "endOffset": idx + len(snippet_text),
                "snippetText": snippet_text,
            }

        # Try matching the first sentence (before "..." if present)
        first_part = snippet_text.split("...")[0].strip()
        if first_part and len(first_part) > 20:
            idx = content.find(first_part)
            if idx != -1:
                # Find end of sentence (next period + space or newline)
                end_idx = idx + len(first_part)
                # Extend to end of sentence
                for i in range(end_idx, min(end_idx + 200, len(content))):
                    if content[i] in ".!?" and (i + 1 >= len(content) or content[i + 1] in " \n"):
                        end_idx = i + 1
                        break
                actual_text = content[idx:end_idx]
                return {
                    "startOffset": idx,
                    "endOffset": end_idx,
                    "snippetText": actual_text,
                }

        # Try finding a key phrase (20+ chars that exist in content)
        # Split by common delimiters and find longest match
        phrases = [p.strip() for p in snippet_text.replace("...", "|").split("|") if p.strip()]
        for phrase in phrases:
            if len(phrase) >= 30:
                idx = content.find(phrase)
                if idx != -1:
                    return {
                        "startOffset": idx,
                        "endOffset": idx + len(phrase),
                        "snippetText": phrase,
                    }

        # Last resort: use first 100 chars of section
        snippet_len = min(200, len(content))
        return {
            "startOffset": 0,
            "endOffset": snippet_len,
            "snippetText": content[:snippet_len],
        }


# Singleton instance
pipeline_service = PipelineService()
