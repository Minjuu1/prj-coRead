"""
Phase 3-4: Discussion Generation Prompts
Generate multi-turn discussions between agents based on seeds.
"""

from config.agents import AGENTS
from config.discussion import DISCUSSION_TYPES, ANNOTATION_TYPES


def get_discussion_prompt(
    seed: dict,
    participants: list[str],
    sections: list[dict],
    num_turns: int = 4
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for discussion generation.
    """

    # Build participant descriptions
    participant_info = ""
    for agent_id in participants:
        agent = AGENTS[agent_id]
        participant_info += f"\n- {agent.name}: {agent.stance_description}\n"

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

    # Build annotation types description
    annotation_types_text = "\n".join([
        f"- {t.id}: {t.description}"
        for t in ANNOTATION_TYPES.values()
    ])

    system_prompt = f"""You are simulating an academic discussion between readers with different perspectives.

<Discussion Context>
Tension Point: {seed['tensionPoint']}
Discussion Type: {seed.get('discussionType', 'deepening')}
Type Guidance: {type_guidance}
</Discussion Context>

<Participants>
{participant_info}
</Participants>

<Annotation Types>
Agents can mark their message with one of these types to indicate their stance:
{annotation_types_text}
</Annotation Types>

<Guidelines>
- Each message should be 2-4 sentences, conversational but substantive
- Agents should respond to each other, not just state their views
- Reference specific parts of the text when relevant
- Show genuine intellectual engagement, not just disagreement
- Build on previous messages to deepen the discussion
- Stay focused on the tension point while exploring different angles
- Choose an appropriate annotation type for each message
</Guidelines>"""

    # Generate annotation type options from config
    annotation_options = " | ".join(ANNOTATION_TYPES.keys())

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
      "annotationType": "{annotation_options}"
    }}
  ]
}}
</Output Format>

<Turn Order Guidelines>
- Start with the agent whose perspective is most directly challenged by the text
- Alternate between agents, ensuring each speaks at least once
- Later messages should build on earlier ones
- End with a message that either synthesizes insights or opens new questions
- Choose annotation types that fit each agent's perspective

Generate the {num_turns}-turn discussion now."""

    return system_prompt, user_prompt


def get_comment_prompt(
    seed: dict,
    agent_id: str,
    sections: list[dict],
) -> tuple[str, str]:
    """
    Generate a single comment for seeds with only one relevant agent.
    """
    agent = AGENTS[agent_id]

    # Find relevant section content
    section_title = seed.get('sectionTitle', '')
    relevant_content = ""
    for section in sections:
        if section['title'] == section_title:
            relevant_content = section['content']
            break

    # Build annotation types description
    annotation_types_text = "\n".join([
        f"- {t.id}: {t.description}"
        for t in ANNOTATION_TYPES.values()
    ])

    # Generate annotation type options from config
    annotation_options = " | ".join(ANNOTATION_TYPES.keys())

    system_prompt = f"""You are a reader with the following perspective:

<Your Reading Stance: {agent.name}>
{agent.stance_description}
</Your Reading Stance>

<Annotation Types>
{annotation_types_text}
</Annotation Types>

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
