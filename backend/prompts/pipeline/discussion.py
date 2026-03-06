"""
Phase 3: Discussion Generation Prompts
Generate discussions that grow from cross-reading reactions.
Also includes continuation prompts for user interaction and "generate more".
"""
from typing import Dict, List, Optional

from config.agents import AGENTS
from config.discussion import get_annotation_types_for_agent


def get_discussion_prompt(
    reaction: dict,
    target_annotation: dict,
    own_annotations: list[dict],
    participants: list[str],
    sections: list[dict],
    num_turns: int = 4,
    memory_context: Optional[Dict[str, str]] = None,
    third_agent_context: Optional[dict] = None,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for discussion generation.

    Args:
        reaction: The cross-reading reaction that starts this discussion
        target_annotation: The annotation being reacted to
        own_annotations: The reacting agent's own annotations referenced in the reaction
        participants: Agent IDs participating (reactor + target author)
        sections: Document sections for context
        num_turns: Number of turns to generate
        memory_context: Dict mapping agent_id -> formatted memory string
        third_agent_context: Optional dict with {agent_id, annotation} for a joining agent
    """
    memory_context = memory_context or {}

    reacting_agent_id = reaction.get("reactingAgentId", "")
    target_agent_id = reaction.get("targetAgentId", "")

    # Build "What Happened" context
    target_agent_name = AGENTS[target_agent_id].name if target_agent_id in AGENTS else target_agent_id
    reacting_agent_name = AGENTS[reacting_agent_id].name if reacting_agent_id in AGENTS else reacting_agent_id

    target_ann_type = target_annotation.get("type", target_annotation.get("annotationType", ""))
    target_text = target_annotation.get("text", target_annotation.get("snippetText", ""))
    target_reasoning = target_annotation.get("reasoning", "")

    reaction_text = reaction.get("reactionText", "")
    reaction_ann_type = reaction.get("reactionAnnotationType", "")

    # Build own annotations context
    own_ann_text = ""
    if own_annotations:
        own_ann_lines = []
        for ann in own_annotations:
            ann_type = ann.get("type", ann.get("annotationType", ""))
            ann_text = ann.get("text", ann.get("snippetText", ""))[:200]
            ann_reasoning = ann.get("reasoning", "")[:200]
            own_ann_lines.append(f'  [{ann_type}] "{ann_text}"\n    → {ann_reasoning}')
        own_ann_text = "\n".join(own_ann_lines)

    # Build participant info with memory
    participant_info = ""
    for agent_id in participants:
        agent = AGENTS[agent_id]
        participant_info += f"\n- {agent.name}: {agent.stance_description}\n"
        if agent_id in memory_context and memory_context[agent_id]:
            participant_info += f"\n{memory_context[agent_id]}\n"

    # Build annotation types per participant
    annotation_types_text = _build_annotation_types_text(participants)
    annotation_options_text = _build_annotation_options_text(participants)

    # Find relevant section content
    section_title = target_annotation.get("sectionTitle", "")
    relevant_content = ""
    for section in sections:
        if section['title'] == section_title:
            relevant_content = section['content']
            break

    # Third agent context
    third_agent_section = ""
    if third_agent_context:
        third_id = third_agent_context.get("agent_id", "")
        third_ann = third_agent_context.get("annotation", {})
        third_name = AGENTS[third_id].name if third_id in AGENTS else third_id
        third_ann_type = third_ann.get("type", third_ann.get("annotationType", ""))
        third_text = third_ann.get("text", third_ann.get("snippetText", ""))[:200]
        third_reasoning = third_ann.get("reasoning", "")[:200]
        third_agent_section = f"""
<Additional Context>
{third_name} also has a relevant annotation on nearby text:
[{third_ann_type}] "{third_text}"
Reasoning: {third_reasoning}

{third_name} may join the conversation if their perspective adds something new.
</Additional Context>"""

    system_prompt = f"""You are simulating an academic discussion that emerged naturally from readers responding to each other's annotations.

<What Happened>
{target_agent_name} annotated a passage [{target_ann_type}]: "{target_text}"
Their reasoning: {target_reasoning}

{reacting_agent_name} responded [{reaction_ann_type}]: {reaction_text}
{f"{reacting_agent_name}'s related annotations:" + chr(10) + own_ann_text if own_ann_text else ""}
</What Happened>

<Participants>
{participant_info}
</Participants>

<Annotation Types by Agent>
Each agent MUST use only their stance-specific annotation types:
{annotation_types_text}
</Annotation Types by Agent>

<Stance Loyalty>
Each agent maintains their reading stance throughout. This does NOT mean disagreeing for its own sake — it means each agent continues to attend to what their stance uniquely reveals, even when acknowledging other perspectives. The three stances see fundamentally different dimensions of the text that cannot be collapsed into one view.
</Stance Loyalty>

<Discussion Rules>
- When you partially agree, name what you grant AND what your stance still sees that the agreement doesn't cover. Never agree without adding your own angle's condition or qualification.
- Always ground claims in the actual text — point to specific passages, methods, or language.
- Don't repeat what was already said in the annotations/reaction above — build on it.
- Each message: 2-4 sentences, conversational but substantive.
- Each agent MUST choose from their own annotation types only.
</Discussion Rules>

<Anti-Convergence>
The educational value of this discussion lies in keeping multiple perspectives alive. The conversation must NOT resolve into a single agreed-upon reading. If agents find common ground, they should immediately explore where their stances DIVERGE on the implications. End with genuinely unresolved questions, not a tidy synthesis.
</Anti-Convergence>"""

    user_prompt = f"""Generate a {num_turns}-turn discussion continuing from the cross-reading reaction above.

<Source Text>
"{target_text}"
</Source Text>

<Surrounding Context>
{relevant_content[:1500] if relevant_content else 'No additional context available.'}
</Surrounding Context>
{third_agent_section}
<Output Format>
Return a JSON object with a "messages" array:
{{
  "messages": [
    {{
      "author": "instrumental | critical | aesthetic",
      "content": "The message (2-4 sentences)",
      "annotationType": "must match author's available types (see below)",
      "referencedAnnotationIds": ["ann_xxx"]
    }}
  ]
}}

Available annotationType values by author:
{annotation_options_text}
</Output Format>

<Turn Guidelines>
- The cross-reading reaction is established context. Start from the SECOND beat — don't repeat it.
- Each turn should either: (a) partially agree but add a condition from your own stance, (b) ask a genuine question that exposes what the other stance can't see, or (c) bring new textual evidence that complicates the current direction.
- {f"{AGENTS[third_agent_context['agent_id']].name} should join only if they have something substantive to add." if third_agent_context else ""}
- NEVER end with agreement, summary, or synthesis. End with an unresolved question or a tension that remains genuinely open.
</Turn Guidelines>

Generate the {num_turns}-turn discussion now."""

    return system_prompt, user_prompt


def get_comment_prompt(
    annotation: dict,
    agent_id: str,
    sections: list[dict],
    agent_memory: str = "",
) -> tuple[str, str]:
    """
    Generate a single comment for an annotation with no cross-reading connections.
    Used when an annotation is noteworthy but didn't provoke cross-reading reactions.
    """
    agent = AGENTS[agent_id]

    # Find relevant section content
    section_title = annotation.get('sectionTitle', '')
    relevant_content = ""
    for section in sections:
        if section['title'] == section_title:
            relevant_content = section['content']
            break

    # Build annotation types for this agent
    agent_types = get_annotation_types_for_agent(agent_id)
    annotation_types_text = "\n".join([
        f"- {t.id}: {t.description}"
        for t in agent_types.values()
    ])
    annotation_options = " | ".join(agent_types.keys())

    memory_section = f"\n{agent_memory}\n" if agent_memory else ""

    ann_type = annotation.get("type", annotation.get("annotationType", ""))
    ann_text = annotation.get("text", annotation.get("snippetText", ""))
    ann_reasoning = annotation.get("reasoning", "")

    system_prompt = f"""You are a reader with the following perspective:

<Your Reading Stance: {agent.name}>
{agent.stance_description}
</Your Reading Stance>
{memory_section}
<Your Annotation Types>
{annotation_types_text}
</Your Annotation Types>

You are expanding on an annotation you made while reading."""

    user_prompt = f"""Expand your annotation into a fuller comment.

<Your Annotation>
[{ann_type}] "{ann_text}"
Your initial reasoning: {ann_reasoning}
</Your Annotation>

<Surrounding Text>
{relevant_content[:1000] if relevant_content else 'No additional context.'}
</Surrounding Text>

<Output Format>
Return a JSON object:
{{
  "content": "Your comment (3-5 sentences) expanding on your annotation",
  "annotationType": "{annotation_options}"
}}
</Output Format>

Expand your thinking now."""

    return system_prompt, user_prompt


def _build_participant_info(participants: list[str], memory_context: Dict[str, str]) -> str:
    """Build participant descriptions with optional memory context."""
    info = ""
    for agent_id in participants:
        agent = AGENTS[agent_id]
        info += f"\n- {agent.name}: {agent.stance_description}\n"
        if agent_id in memory_context and memory_context[agent_id]:
            info += f"\n{memory_context[agent_id]}\n"
    return info


def _build_annotation_types_text(participants: list[str]) -> str:
    """Build annotation types description for each participant."""
    text = ""
    for agent_id in participants:
        agent_types = get_annotation_types_for_agent(agent_id)
        agent_name = AGENTS[agent_id].name
        types_list = "\n".join([f"    - {t.id}: {t.description}" for t in agent_types.values()])
        text += f"\n  {agent_name}:\n{types_list}\n"
    return text


def _build_annotation_options_text(participants: list[str]) -> str:
    """Build annotation type options per agent for output format."""
    lines = []
    for agent_id in participants:
        agent_types = get_annotation_types_for_agent(agent_id)
        options = " | ".join(agent_types.keys())
        lines.append(f"      - {agent_id}: {options}")
    return "\n".join(lines)


def _format_messages_for_prompt(messages: List[dict]) -> str:
    """Format existing messages as conversation history for prompts."""
    lines = []
    for msg in messages:
        author = msg.get("author", "unknown")
        content = msg.get("content", "")
        ann_type = msg.get("annotationType", "")
        type_label = f" [{ann_type}]" if ann_type else ""
        lines.append(f"[{author}{type_label}]: {content}")
    return "\n\n".join(lines)


def get_user_response_prompt(
    thread: dict,
    user_message: dict,
    responding_agents: list[str],
    sections: list[dict],
    memory_context: Optional[Dict[str, str]] = None,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for generating agent response(s) to a user message.
    """
    memory_context = memory_context or {}

    participant_info = _build_participant_info(responding_agents, memory_context)
    annotation_types_text = _build_annotation_types_text(responding_agents)
    annotation_options_text = _build_annotation_options_text(responding_agents)

    # Find relevant section content from anchor
    anchor = thread.get("anchor", {})
    section_id = anchor.get("sectionId", "")
    relevant_content = ""
    for section in sections:
        if section.get("sectionId") == section_id:
            relevant_content = section["content"]
            break

    # Format conversation history
    conversation_history = _format_messages_for_prompt(thread.get("messages", []))

    system_prompt = f"""You are simulating readers in an academic discussion. A human reader has joined the conversation.

<Participants>
{participant_info}
</Participants>

<Annotation Types by Agent>
Each agent MUST use only their stance-specific annotation types:
{annotation_types_text}
</Annotation Types by Agent>

<Guidelines>
- Respond directly to the user's message — acknowledge what they said before adding your perspective
- Each response should be 2-4 sentences, conversational but substantive
- Reference specific parts of the text when relevant
- Stay in character as your reading stance — maintain what your stance uniquely sees
- Each agent MUST choose from their own annotation types only
- If the user asks a question, address it from your stance's perspective — show what your angle reveals that others might not
- If you agree with the user or another agent, always add what your stance STILL sees beyond that agreement
</Guidelines>"""

    user_prompt = f"""A user has joined this discussion. Generate {"a response" if len(responding_agents) == 1 else "responses"} from {", ".join(responding_agents)}.

<Anchored Text>
"{anchor.get('snippetText', '')}"
</Anchored Text>

<Surrounding Context>
{relevant_content[:1500] if relevant_content else 'No additional context available.'}
</Surrounding Context>

<Conversation So Far>
{conversation_history}
</Conversation So Far>

<User's Message>
{user_message['content']}
</User's Message>

<Output Format>
Return a JSON object with a "messages" array:
{{
  "messages": [
    {{
      "author": "instrumental | critical | aesthetic",
      "content": "The response (2-4 sentences)",
      "annotationType": "must match author's available types (see below)"
    }}
  ]
}}

Available annotationType values by author:
{annotation_options_text}
</Output Format>

<Response Guidelines>
- {"Respond as " + responding_agents[0] + " only" if len(responding_agents) == 1 else "Each agent responds once, in order: " + ", ".join(responding_agents)}
- Directly engage with what the user said
- Bring your unique reading stance to the response
- Keep it conversational and accessible

Generate {"the response" if len(responding_agents) == 1 else "the responses"} now."""

    return system_prompt, user_prompt


def get_generate_more_prompt(
    thread: dict,
    participants: list[str],
    sections: list[dict],
    num_turns: int = 4,
    memory_context: Optional[Dict[str, str]] = None,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for generating additional discussion turns.
    """
    memory_context = memory_context or {}

    participant_info = _build_participant_info(participants, memory_context)
    annotation_types_text = _build_annotation_types_text(participants)
    annotation_options_text = _build_annotation_options_text(participants)

    # Find relevant section content from anchor
    anchor = thread.get("anchor", {})
    section_id = anchor.get("sectionId", "")
    relevant_content = ""
    for section in sections:
        if section.get("sectionId") == section_id:
            relevant_content = section["content"]
            break

    # Format conversation history
    conversation_history = _format_messages_for_prompt(thread.get("messages", []))

    system_prompt = f"""You are continuing an academic discussion between readers with different perspectives.

<Participants>
{participant_info}
</Participants>

<Annotation Types by Agent>
Each agent MUST use only their stance-specific annotation types:
{annotation_types_text}
</Annotation Types by Agent>

<Guidelines>
- Continue naturally from where the conversation left off
- Each message should be 2-4 sentences, conversational but substantive
- Do NOT repeat points already made — push the discussion into new territory
- Maintain stance loyalty: each agent keeps attending to what their stance uniquely reveals
- If you partially agree, always add your stance's condition or show what it still sees beyond the agreement
- Each agent MUST choose from their own annotation types only
</Guidelines>"""

    user_prompt = f"""Continue this discussion for {num_turns} more turns.

<Anchored Text>
"{anchor.get('snippetText', '')}"
</Anchored Text>

<Surrounding Context>
{relevant_content[:1500] if relevant_content else 'No additional context available.'}
</Surrounding Context>

<Conversation So Far>
{conversation_history}
</Conversation So Far>

<Output Format>
Return a JSON object with a "messages" array:
{{
  "messages": [
    {{
      "author": "instrumental | critical | aesthetic",
      "content": "The message content (2-4 sentences)",
      "annotationType": "must match author's available types (see below)"
    }}
  ]
}}

Available annotationType values by author:
{annotation_options_text}
</Output Format>

<Continuation Guidelines>
- Pick up from the last message naturally
- Alternate between agents, ensuring each speaks
- Explore new angles — don't rehash what's been said
- If agents start converging, introduce a new textual detail or question that reopens the tension
- NEVER end with agreement or synthesis — end with an unresolved question or genuine tension
- Each agent MUST use only their own annotation types

Generate {num_turns} more turns now."""

    return system_prompt, user_prompt
