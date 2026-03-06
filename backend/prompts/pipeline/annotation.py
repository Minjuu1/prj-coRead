"""
Phase 1: Annotation Generation Prompts
Each agent reads the document and generates annotations from their perspective.
Annotations are visible to users as a reading layer on the document.
"""

from config.agents import AGENTS
from config.discussion import get_annotation_types_for_agent


def get_annotation_system_prompt(agent_id: str) -> str:
    agent = AGENTS[agent_id]

    return f"""You are a reader with the following perspective:

<Your Reading Stance: {agent.name}>
{agent.stance_description}
</Your Reading Stance>

<Voice Constraint>
{agent.voice_constraint}
</Voice Constraint>

Your task is to read academic text and identify points that stand out from your perspective.
You will generate annotations — moments where you notice something worth sharing with other readers.

Each annotation will be visible alongside the document text as a margin note.
Write your reasoning as you would for a reading companion who wants to understand your perspective.

For each annotation, you must:
1. Select the EXACT text (a sentence or short passage) that triggered your reaction
2. Categorize your reaction type
3. Explain your reasoning in your natural voice

CRITICAL: The "text" field must be an EXACT quote from the document - copy it precisely.
This text will be used to locate and highlight the annotation in the document."""


def get_annotation_prompt(agent_id: str, sections: list[dict], max_annotations: int = 7) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for annotation generation.
    """
    system_prompt = get_annotation_system_prompt(agent_id)

    # Format sections with approximate word counts for natural distribution
    sections_text = ""
    section_info_lines = []
    MAX_SECTION_CHARS = 2000
    for section in sections:
        content = section['content']
        if len(content) > MAX_SECTION_CHARS:
            content = content[:MAX_SECTION_CHARS] + "... [truncated]"
        sections_text += f"\n\n## {section['title']}\n{content}"
        word_count = len(section['content'].split())
        section_info_lines.append(f"- {section['title']} (~{word_count} words)")

    # Generate annotation types for this specific agent
    agent_types = get_annotation_types_for_agent(agent_id)
    annotation_types_text = "\n".join([
        f"- {t.id}: {t.description}"
        for t in agent_types.values()
    ])

    n_sections = len(sections)
    section_list_text = "\n".join(section_info_lines)

    # Generate type options string for this agent
    type_options = " | ".join(agent_types.keys())

    user_prompt = f"""Read the following academic text and generate 5 to 7 annotations from your perspective.

<Document>
{sections_text}
</Document>

<Annotation Types>
{annotation_types_text}
</Annotation Types>

<Output Format>
Return a JSON object with an "annotations" array:
{{
  "annotations": [
    {{
      "type": "{type_options}",
      "sectionTitle": "The section title where this text appears",
      "text": "EXACT quoted text from the document (1-3 sentences)",
      "reasoning": "Why this stands out from your perspective (2-4 sentences)"
    }}
  ]
}}
</Output Format>

<Section Coverage>
The document has {n_sections} sections:
{section_list_text}

Distribute annotations naturally across sections based on what genuinely stands out to you.
- Longer, more substantive sections may deserve more annotations
- Shorter or less relevant sections may have zero
- Prioritize sections with original claims, evidence, or methodological decisions
- Skip Conclusion/Abstract unless they contain genuinely new points
</Section Coverage>

<Guidelines>
- Generate between 5 and 7 annotations. Quality over quantity — each should represent a genuine moment of engagement.
- Use ALL {len(agent_types)} of your annotation types at least once
- The "text" field MUST be an exact copy from the document - do not paraphrase
- Each text selection should be 1-3 sentences
- Multiple annotations on the same paragraph are fine if different aspects stand out
- VOICE: Write reasoning like a margin note — specific, direct, conversational. Do NOT restate the annotation type label.
  BAD: "I question the assumption that 15 participants is sufficient."
  GOOD: "Fifteen participants — for claims this broad? The gap between sample and conclusion feels wide."
</Guidelines>

Generate your annotations now."""

    return system_prompt, user_prompt
