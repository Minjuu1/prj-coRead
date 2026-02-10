"""
Phase 1: Annotation Generation Prompts
Each agent reads the document and generates annotations from their perspective.
"""

from config.agents import AGENTS
from config.discussion import get_annotation_types_for_agent


def get_annotation_system_prompt(agent_id: str) -> str:
    agent = AGENTS[agent_id]

    return f"""You are a reader with the following perspective:

<Your Reading Stance: {agent.name}>
{agent.stance_description}
</Your Reading Stance>

Your task is to read academic text and identify points that stand out from your perspective.
You will generate annotations - moments where you notice something worth discussing.

For each annotation, you must:
1. Select the EXACT text (a sentence or short passage) that triggered your reaction
2. Categorize your reaction type
3. Explain your reasoning from your specific perspective

CRITICAL: The "text" field must be an EXACT quote from the document - copy it precisely.
This text will be used to locate the annotation in the document."""


def get_annotation_prompt(agent_id: str, sections: list[dict], max_annotations: int = 20) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for annotation generation.
    """
    system_prompt = get_annotation_system_prompt(agent_id)

    # Format sections with approximate word counts for natural distribution
    sections_text = ""
    section_info_lines = []
    for section in sections:
        sections_text += f"\n\n## {section['title']}\n{section['content']}"
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

    user_prompt = f"""Read the following academic text and generate exactly {max_annotations} annotations from your perspective.

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
      "reasoning": "Why this stands out from your perspective (2-3 sentences)"
    }}
  ]
}}
</Output Format>

<Section Coverage>
The document has {n_sections} sections:
{section_list_text}

You should annotate across multiple sections, but distribute NATURALLY based on how much each section matters to your reading stance.
- Longer, more substantive sections deserve more annotations
- Shorter or less relevant sections may have fewer (or even zero)
- It's fine to have 5+ annotations in a rich section and 0-1 in a thin one
- Do NOT force an even split - follow your genuine reactions
</Section Coverage>

<Guidelines>
- You MUST generate exactly {max_annotations} annotations - no fewer
- Use ALL {len(agent_types)} of your annotation types at least once
- The "text" field MUST be an exact copy from the document - do not paraphrase
- Each text selection should be 1-3 sentences (not too short, not too long)
- Your reasoning should reflect your specific reading stance
- Go deep: multiple annotations on the same paragraph are fine if different aspects stand out
</Guidelines>

Generate your {max_annotations} annotations now."""

    return system_prompt, user_prompt
