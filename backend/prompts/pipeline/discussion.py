"""
Phase 3-4: Discussion Generation Prompts
Generate multi-turn discussions between agents based on seeds.
"""
from typing import Dict, Optional

from config.agents import AGENTS
from config.discussion import DISCUSSION_TYPES, get_annotation_types_for_agent


def get_discussion_prompt(
    seed: dict,
    participants: list[str],
    sections: list[dict],
    num_turns: int = 4,
    memory_context: Optional[Dict[str, str]] = None,
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for discussion generation.

    Args:
        memory_context: Dict mapping agent_id -> formatted memory string
    """
    memory_context = memory_context or {}

    # Build participant descriptions with memory
    participant_info = ""
    for agent_id in participants:
        agent = AGENTS[agent_id]
        participant_info += f"\n- {agent.name}: {agent.stance_description}\n"
        # Add agent's memory if available
        if agent_id in memory_context and memory_context[agent_id]:
            participant_info += f"\n{memory_context[agent_id]}\n"

    # Get discussion type guidance
    disc_type = DISCUSSION_TYPES.get(seed.get('discussionType', 'deepening'))
    type_guidance = disc_type.prompt_guidance if disc_type else "Engage thoughtfully with different perspectives"

    # Find relevant section content
    section_title = seed.get('sectionTitle', '')
    relevant_content = ""
    for section in sections:
        if section['title'] == section_title:
            relevant_content = section['content']
            break

    # Build annotation types description - each agent has their own types
    annotation_types_text = ""
    for agent_id in participants:
        agent_types = get_annotation_types_for_agent(agent_id)
        agent_name = AGENTS[agent_id].name
        types_list = "\n".join([f"    - {t.id}: {t.description}" for t in agent_types.values()])
        annotation_types_text += f"\n  {agent_name}:\n{types_list}\n"

    system_prompt = f"""You are simulating an academic discussion between readers with different perspectives.

<Discussion Context>
Tension Point: {seed['tensionPoint']}
Discussion Type: {seed.get('discussionType', 'deepening')}
Type Guidance: {type_guidance}
</Discussion Context>

<Participants>
{participant_info}
</Participants>

<Annotation Types by Agent>
Each agent MUST use only their stance-specific annotation types:
{annotation_types_text}
</Annotation Types by Agent>

<Cross-Reference Guideline>
When responding to another agent's annotation, reinterpret it through your own stance.
For example, if Critical responds to Aesthetic's "resonate", Critical might frame their response as a "question" or "challenge" about the emotional reaction's implications.
</Cross-Reference Guideline>

<Guidelines>
- Each message should be 2-4 sentences, conversational but substantive
- Agents should respond to each other, not just state their views
- Reference specific parts of the text when relevant
- Show genuine intellectual engagement, not just disagreement
- Build on previous messages to deepen the discussion
- Stay focused on the tension point while exploring different angles
- Each agent MUST choose from their own annotation types only
</Guidelines>"""

    # Generate annotation type options per agent for output format
    annotation_options_per_agent = {}
    for agent_id in participants:
        agent_types = get_annotation_types_for_agent(agent_id)
        annotation_options_per_agent[agent_id] = " | ".join(agent_types.keys())

    annotation_options_text = "\n".join([
        f"      - {agent_id}: {options}"
        for agent_id, options in annotation_options_per_agent.items()
    ])

    user_prompt = f"""Generate a {num_turns}-turn discussion about this tension point.

<Anchored Text>
"{seed['snippetText']}"
</Anchored Text>

<Surrounding Context>
{relevant_content[:1500] if relevant_content else 'No additional context available.'}
</Surrounding Context>

<Participants for this discussion>
{', '.join(participants)}
</Participants>

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

<Turn Order Guidelines>
- Start with the agent whose perspective is most directly challenged by the text
- Alternate between agents, ensuring each speaks at least once
- Later messages should build on earlier ones
- End with a message that either synthesizes insights or opens new questions
- Each agent MUST use only their own annotation types

Generate the {num_turns}-turn discussion now."""

    return system_prompt, user_prompt


def get_comment_prompt(
    seed: dict,
    agent_id: str,
    sections: list[dict],
    agent_memory: str = "",
) -> tuple[str, str]:
    """
    Generate a single comment for seeds with only one relevant agent.

    Args:
        agent_memory: Formatted memory string for the agent
    """
    agent = AGENTS[agent_id]

    # Find relevant section content
    section_title = seed.get('sectionTitle', '')
    relevant_content = ""
    for section in sections:
        if section['title'] == section_title:
            relevant_content = section['content']
            break

    # Build annotation types description for this specific agent
    agent_types = get_annotation_types_for_agent(agent_id)
    annotation_types_text = "\n".join([
        f"- {t.id}: {t.description}"
        for t in agent_types.values()
    ])

    # Generate annotation type options for this agent only
    annotation_options = " | ".join(agent_types.keys())

    # Include memory in system prompt if available
    memory_section = f"\n{agent_memory}\n" if agent_memory else ""

    system_prompt = f"""You are a reader with the following perspective:

<Your Reading Stance: {agent.name}>
{agent.stance_description}
</Your Reading Stance>
{memory_section}
<Your Annotation Types>
These are the annotation types that match your reading stance:
{annotation_types_text}
</Your Annotation Types>

You are writing a thoughtful comment about a specific passage in an academic text."""

    user_prompt = f"""Write a comment about this passage from your perspective.

<Passage>
"{seed['snippetText']}"
</Passage>

<Context>
Tension Point: {seed['tensionPoint']}
</Context>

<Surrounding Text>
{relevant_content[:1000] if relevant_content else 'No additional context.'}
</Surrounding Text>

<Output Format>
Return a JSON object:
{{
  "content": "Your comment (3-5 sentences) that engages with this passage from your specific reading perspective",
  "annotationType": "{annotation_options}"
}}
</Output Format>

Write your comment now."""

    return system_prompt, user_prompt
