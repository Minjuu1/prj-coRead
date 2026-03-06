"""
Pipeline Service - Orchestrates the full discussion generation pipeline.
Phase 1: Reading (Annotations) → Phase 2: Cross-Reading → Phase 3: Discussion Generation
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional

from config.agents import AGENT_IDS, AGENTS
from config.discussion import CROSS_READING_CONFIG
from services.llm_service import llm_service
from services.firebase_service import firebase_service
from services.memory_service import memory_service
from prompts.pipeline.annotation import get_annotation_prompt
from prompts.pipeline.cross_reading import get_cross_reading_prompt
from prompts.pipeline.discussion import get_discussion_prompt, get_comment_prompt


class PipelineService:
    """Orchestrates the full pipeline for generating discussions from a document."""

    async def run_full_pipeline(
        self,
        document_id: str,
        sections: list[dict],
        annotations_per_agent: int = 7,
        turns_per_discussion: int = 4,
    ) -> dict:
        """
        Run the complete pipeline:
        Phase 1: Reading → Phase 2: Cross-Reading → Phase 3: Discussion Generation
        """
        print(f"[Pipeline] Starting for document {document_id}")

        # Initialize memory for all agents
        memory_service.initialize_for_document(document_id)

        # Phase 1: Generate annotations from all agents (in parallel)
        print("[Pipeline] Phase 1: Reading (generating annotations)...")
        annotations_by_agent = await self._phase1_reading(
            document_id, sections, annotations_per_agent
        )

        total_annotations = sum(len(a) for a in annotations_by_agent.values())
        print(f"[Pipeline] Phase 1 complete: {total_annotations} total annotations")

        # Store visible annotations
        visible_annotations = self._store_visible_annotations(
            document_id, annotations_by_agent, sections
        )
        print(f"[Pipeline] Stored {len(visible_annotations)} visible annotations")

        # Phase 2: Cross-reading (agents react to each other's annotations)
        print("[Pipeline] Phase 2: Cross-reading...")
        all_reactions = await self._phase2_cross_reading(
            document_id, annotations_by_agent, sections
        )
        print(f"[Pipeline] Phase 2 complete: {len(all_reactions)} total reactions")

        # Store reactions
        firebase_service.save_reactions(document_id, all_reactions)

        # Between Phase 2 → 3: Filter by structural quality + select starters
        print("[Pipeline] Filtering: selecting strong reactions...")
        strong_reactions = self._filter_reactions(all_reactions)
        print(f"[Pipeline] Filtering complete: {len(strong_reactions)} strong / {len(all_reactions)} total")

        # Phase 3: Discussion generation from strong connections
        print("[Pipeline] Phase 3: Generating discussions...")
        starters = self._select_discussion_starters(
            strong_reactions, annotations_by_agent
        )
        print(f"[Pipeline] Selected {len(starters)} discussion starters")

        threads = await self._phase3_discussion_generation(
            document_id, starters, annotations_by_agent, sections, turns_per_discussion
        )
        print(f"[Pipeline] Phase 3 complete: {len(threads)} threads generated")

        return {
            "annotations": annotations_by_agent,
            "reactions": all_reactions,
            "strongReactions": strong_reactions,
            "threads": threads,
        }

    # =========================================================================
    # Phase 1: Reading (Annotation Generation)
    # =========================================================================

    async def _phase1_reading(
        self, document_id: str, sections: list[dict], annotations_per_agent: int
    ) -> dict[str, list]:
        """Generate annotations from all three agents in parallel."""
        tasks = []
        for agent_id in AGENT_IDS:
            task = self._generate_agent_annotations(agent_id, sections, annotations_per_agent)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        annotations_by_agent = {}
        for agent_id, result in zip(AGENT_IDS, results):
            if isinstance(result, Exception):
                print(f"[Pipeline] Error generating annotations for {agent_id}: {result}")
                annotations_by_agent[agent_id] = []
            else:
                annotations_by_agent[agent_id] = result
                # Store annotations in agent memory
                if result:
                    memory_service.store_annotations(document_id, agent_id, result)
                    print(f"[Pipeline] Stored {len(result)} annotations in {agent_id}'s memory")

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

            # Add agent_id and annotationId to each annotation
            for ann in annotations:
                ann["agentId"] = agent_id
                ann["annotationId"] = f"ann_{uuid.uuid4().hex[:8]}"

            return annotations
        except Exception as e:
            print(f"[Pipeline] Annotation error for {agent_id}: {e}")
            return []

    def _store_visible_annotations(
        self,
        document_id: str,
        annotations_by_agent: dict[str, list],
        sections: list[dict],
    ) -> list[dict]:
        """Compute offsets and store visible annotations for frontend display."""
        visible = []

        for agent_id, annotations in annotations_by_agent.items():
            for ann in annotations:
                # Find section
                target_section = None
                for section in sections:
                    if section["title"] == ann.get("sectionTitle"):
                        target_section = section
                        break

                # Compute anchor offset
                anchor = self._compute_anchor(ann.get("text", ""), target_section)

                visible_ann = {
                    "annotationId": ann["annotationId"],
                    "documentId": document_id,
                    "agentId": agent_id,
                    "annotationType": ann.get("type", ""),
                    "sectionId": target_section["sectionId"] if target_section else "section_0",
                    "sectionTitle": ann.get("sectionTitle", ""),
                    "startOffset": anchor["startOffset"],
                    "endOffset": anchor["endOffset"],
                    "snippetText": anchor["snippetText"],
                    "reasoning": ann.get("reasoning", ""),
                    "createdAt": datetime.utcnow().isoformat(),
                }
                visible.append(visible_ann)

                # Also update the annotation dict with computed offsets
                ann["startOffset"] = anchor["startOffset"]
                ann["endOffset"] = anchor["endOffset"]
                ann["sectionId"] = visible_ann["sectionId"]
                ann["snippetText"] = anchor["snippetText"]

        # Save to storage
        firebase_service.save_annotations(document_id, visible)
        return visible

    # =========================================================================
    # Phase 2: Cross-Reading
    # =========================================================================

    async def _phase2_cross_reading(
        self,
        document_id: str,
        annotations_by_agent: dict[str, list],
        sections: list[dict],
    ) -> list[dict]:
        """Each agent reads other agents' annotations and reacts."""
        tasks = []
        for agent_id in AGENT_IDS:
            others = {
                aid: anns for aid, anns in annotations_by_agent.items()
                if aid != agent_id
            }
            own = annotations_by_agent.get(agent_id, [])

            task = self._generate_cross_reading_reactions(
                agent_id, others, own, sections, document_id
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_reactions = []
        for agent_id, result in zip(AGENT_IDS, results):
            if isinstance(result, Exception):
                print(f"[Pipeline] Cross-reading error for {agent_id}: {result}")
            else:
                all_reactions.extend(result)

        return all_reactions

    async def _generate_cross_reading_reactions(
        self,
        agent_id: str,
        other_agents_annotations: dict[str, list],
        own_annotations: list[dict],
        sections: list[dict],
        document_id: str,
    ) -> list[dict]:
        """Generate cross-reading reactions for a single agent."""
        system_prompt, user_prompt = get_cross_reading_prompt(
            agent_id, other_agents_annotations, own_annotations, sections
        )

        try:
            result = await llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
            )
            raw_reactions = result.get("reactions", [])

            reactions = []
            for raw in raw_reactions:
                target_ann_id = raw.get("targetAnnotationId", "")
                target_agent_id = raw.get("targetAgentId", "")

                # Find the target annotation
                target_ann = self._find_annotation_by_id(
                    target_ann_id, other_agents_annotations
                )

                # Find own annotations referenced
                own_ref_ids = raw.get("ownAnnotationRefs", [])
                own_ref_texts = []
                for ref_id in own_ref_ids:
                    for own_ann in own_annotations:
                        if own_ann.get("annotationId") == ref_id:
                            own_ref_texts.append(
                                own_ann.get("text", own_ann.get("snippetText", ""))[:100]
                            )
                            break

                reaction = {
                    "reactionId": f"rxn_{uuid.uuid4().hex[:8]}",
                    "documentId": document_id,
                    "reactingAgentId": agent_id,
                    "targetAnnotationId": target_ann_id,
                    "targetAgentId": target_agent_id,
                    "targetAnnotationType": target_ann.get("type", target_ann.get("annotationType", "")) if target_ann else "",
                    "reactionText": raw.get("reactionText", ""),
                    "reactionAnnotationType": raw.get("reactionAnnotationType", ""),
                    "ownAnnotationIds": own_ref_ids,
                    "ownAnnotationTexts": own_ref_texts,
                    "sectionId": target_ann.get("sectionId", "") if target_ann else "",
                    "createdAt": datetime.utcnow().isoformat(),
                }
                reactions.append(reaction)

            print(f"[Pipeline] {agent_id} generated {len(reactions)} cross-reading reactions")
            return reactions

        except Exception as e:
            print(f"[Pipeline] Cross-reading error for {agent_id}: {e}")
            return []

    def _find_annotation_by_id(
        self, annotation_id: str, annotations_by_agent: dict[str, list]
    ) -> Optional[dict]:
        """Find an annotation by ID across all agents."""
        for agent_id, annotations in annotations_by_agent.items():
            for ann in annotations:
                if ann.get("annotationId") == annotation_id:
                    return ann
        return None

    def _filter_reactions(self, reactions: list[dict]) -> list[dict]:
        """
        Filter cross-reading reactions by structural quality.
        This is a BETWEEN-PHASE step (Phase 2 → 3), not part of Phase 2.
        Does NOT mutate the original reactions.
        """
        min_length = CROSS_READING_CONFIG.get("min_reaction_length", 50)
        require_ref = CROSS_READING_CONFIG.get("require_own_annotation_ref", True)

        agreement_phrases = [
            "i agree", "interesting point", "good observation",
            "makes sense", "that's a good", "i see what you mean",
        ]

        strong = []
        for r in reactions:
            has_own_ref = len(r.get("ownAnnotationIds", [])) > 0
            reaction_text = r.get("reactionText", "")
            is_substantive = len(reaction_text) >= min_length
            text_lower = reaction_text.lower().strip()
            is_not_just_agreeing = not any(
                text_lower.startswith(phrase) for phrase in agreement_phrases
            )

            is_strong = is_substantive and is_not_just_agreeing
            if require_ref:
                is_strong = is_strong and has_own_ref

            if is_strong:
                strong.append(r)

        return strong

    # =========================================================================
    # Phase 3: Discussion Generation
    # =========================================================================

    def _select_discussion_starters(
        self,
        strong_reactions: list[dict],
        annotations_by_agent: dict[str, list],
    ) -> list[dict]:
        """Select which strong reactions become discussion starters."""
        starters = []
        used_annotation_ids = set()

        sorted_reactions = sorted(
            strong_reactions,
            key=lambda r: len(r.get("ownAnnotationIds", [])),
            reverse=True,
        )

        for reaction in sorted_reactions:
            target_id = reaction.get("targetAnnotationId", "")
            if target_id in used_annotation_ids:
                continue

            used_annotation_ids.add(target_id)
            for aid in reaction.get("ownAnnotationIds", []):
                used_annotation_ids.add(aid)

            participants = [reaction["reactingAgentId"], reaction["targetAgentId"]]
            third_agent = self._find_relevant_third_agent(
                reaction, annotations_by_agent, participants
            )

            starters.append({
                "reaction": reaction,
                "participants": participants,
                "third_agent": third_agent,
            })

        return starters

    def _find_relevant_third_agent(
        self,
        reaction: dict,
        annotations_by_agent: dict[str, list],
        existing_participants: list[str],
    ) -> Optional[dict]:
        """Check if the third agent has a relevant annotation nearby."""
        third_agents = [a for a in AGENT_IDS if a not in existing_participants]
        if not third_agents:
            return None

        third_agent_id = third_agents[0]
        third_annotations = annotations_by_agent.get(third_agent_id, [])
        reaction_section = reaction.get("sectionId", "")

        for ann in third_annotations:
            if ann.get("sectionId", "") != reaction_section:
                continue

            # Check text proximity
            ann_start = ann.get("startOffset", 0)
            target_start = 0
            for agent_anns in annotations_by_agent.values():
                for a in agent_anns:
                    if a.get("annotationId") == reaction.get("targetAnnotationId"):
                        target_start = a.get("startOffset", 0)
                        break

            if abs(ann_start - target_start) <= 500:
                return {
                    "agent_id": third_agent_id,
                    "annotation": ann,
                }

        return None

    async def _phase3_discussion_generation(
        self,
        document_id: str,
        starters: list[dict],
        annotations_by_agent: dict[str, list],
        sections: list[dict],
        turns_per_discussion: int,
    ) -> list[dict]:
        """Generate threads for each discussion starter."""
        tasks = []
        for starter in starters:
            task = self._generate_thread_from_starter(
                document_id, starter, annotations_by_agent, sections, turns_per_discussion
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        threads = []
        for starter, result in zip(starters, results):
            if isinstance(result, Exception):
                print(f"[Pipeline] Thread generation error: {result}")
            elif result:
                threads.append(result)

        return threads

    async def _generate_thread_from_starter(
        self,
        document_id: str,
        starter: dict,
        annotations_by_agent: dict[str, list],
        sections: list[dict],
        turns: int,
    ) -> Optional[dict]:
        """Generate a single thread from a discussion starter."""
        reaction = starter["reaction"]
        participants = starter["participants"]
        third_agent = starter.get("third_agent")

        # Find the target annotation
        target_annotation = self._find_annotation_by_id(
            reaction["targetAnnotationId"], annotations_by_agent
        )
        if not target_annotation:
            print(f"[Pipeline] Target annotation not found: {reaction['targetAnnotationId']}")
            return None

        # Find own annotations referenced
        own_annotations = []
        reacting_agent_anns = annotations_by_agent.get(reaction["reactingAgentId"], [])
        for ref_id in reaction.get("ownAnnotationIds", []):
            for ann in reacting_agent_anns:
                if ann.get("annotationId") == ref_id:
                    own_annotations.append(ann)
                    break

        # Find target section
        target_section = None
        for section in sections:
            if section["title"] == target_annotation.get("sectionTitle"):
                target_section = section
                break
        if not target_section and sections:
            target_section = sections[0]

        section_id = target_section["sectionId"] if target_section else "section_0"

        # Compute anchor
        anchor_info = self._compute_anchor(
            target_annotation.get("text", target_annotation.get("snippetText", "")),
            target_section,
        )

        # Build memory context
        memory_context = {}
        for agent_id in participants:
            memory_context[agent_id] = memory_service.format_for_prompt(
                document_id, agent_id, section_ids=[section_id],
            )

        # Third agent context
        third_agent_context = None
        if third_agent:
            third_agent_context = {
                "agent_id": third_agent["agent_id"],
                "annotation": third_agent["annotation"],
            }
            if third_agent["agent_id"] not in participants:
                participants = participants + [third_agent["agent_id"]]

        # Source annotation IDs
        source_annotation_ids = [target_annotation["annotationId"]]
        source_annotation_ids.extend(reaction.get("ownAnnotationIds", []))
        if third_agent:
            third_ann = third_agent.get("annotation", {})
            if third_ann.get("annotationId"):
                source_annotation_ids.append(third_ann["annotationId"])

        try:
            system_prompt, user_prompt = get_discussion_prompt(
                reaction=reaction,
                target_annotation=target_annotation,
                own_annotations=own_annotations,
                participants=participants,
                sections=sections,
                num_turns=turns,
                memory_context=memory_context,
                third_agent_context=third_agent_context,
            )

            result = await llm_service.generate_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,
            )
            raw_messages = result.get("messages", [])

            now = datetime.utcnow().isoformat()
            thread_id = f"thread_{uuid.uuid4().hex[:8]}"

            messages = []
            prev_author = None
            for msg in raw_messages:
                message_id = f"msg_{uuid.uuid4().hex[:8]}"
                message = {
                    "messageId": message_id,
                    "threadId": thread_id,
                    "author": msg["author"],
                    "content": msg["content"],
                    "references": [],
                    "timestamp": now,
                }
                if "annotationType" in msg and msg["annotationType"]:
                    message["annotationType"] = msg["annotationType"]
                if "referencedAnnotationIds" in msg:
                    message["referencedAnnotationIds"] = msg["referencedAnnotationIds"]
                messages.append(message)

                memory_service.store_thought(
                    document_id=document_id,
                    agent_id=msg["author"],
                    thread_id=thread_id,
                    message_id=message_id,
                    content=msg["content"],
                    source_reaction_id=reaction["reactionId"],
                    annotation_type=msg.get("annotationType"),
                    responding_to=prev_author,
                    referenced_section_ids=[section_id],
                    referenced_annotation_ids=msg.get("referencedAnnotationIds", []),
                )
                prev_author = msg["author"]

            thread = {
                "threadId": thread_id,
                "documentId": document_id,
                "sourceReactionId": reaction["reactionId"],
                "sourceAnnotationIds": source_annotation_ids,
                "threadType": "discussion",
                "keywords": [],
                "anchor": {
                    "sectionId": section_id,
                    "startOffset": anchor_info["startOffset"],
                    "endOffset": anchor_info["endOffset"],
                    "snippetText": anchor_info["snippetText"],
                },
                "participants": participants,
                "messages": messages,
                "createdAt": now,
                "updatedAt": now,
            }

            return thread

        except Exception as e:
            print(f"[Pipeline] Thread generation error: {e}")
            return None

    # =========================================================================
    # Utility
    # =========================================================================

    def _compute_anchor(self, snippet_text: str, section: Optional[dict]) -> dict:
        """Compute anchor offset by finding snippet text in section content."""
        default = {
            "startOffset": 0,
            "endOffset": 100,
            "snippetText": snippet_text[:100] if snippet_text else "",
        }

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

        # Try matching the first sentence
        first_part = snippet_text.split("...")[0].strip()
        if first_part and len(first_part) > 20:
            idx = content.find(first_part)
            if idx != -1:
                end_idx = idx + len(first_part)
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

        # Try finding a key phrase
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

        # Last resort
        snippet_len = min(200, len(content))
        return {
            "startOffset": 0,
            "endOffset": snippet_len,
            "snippetText": content[:snippet_len],
        }


# Singleton instance
pipeline_service = PipelineService()
