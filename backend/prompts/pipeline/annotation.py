"""
Phase 1: Annotation Generation Prompts
Each agent reads the document and generates annotations from their perspective.
"""

from config.agents import AGENTS
from config.discussion import ANNOTATION_TYPES


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


def get_annotation_prompt(agent_id: str, sections: list[dict], max_annotations: int = 15) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for annotation generation.
    """
    system_prompt = get_annotation_system_prompt(agent_id)

    # Format sections for the prompt
    sections_text = ""
    for section in sections:
        sections_text += f"\n\n## {section['title']}\n{section['content']}"

    # Generate annotation types from config
    annotation_types_text = "\n".join([
        f"- {t.id}: {t.description}"
        for t in ANNOTATION_TYPES.values()
    ])

    # Generate section coverage guidance
    section_titles = [s['title'] for s in sections]
    n_sections = len(sections)
    suggested_per_section = max(2, max_annotations // n_sections) if n_sections > 0 else max_annotations
    section_list_text = "\n".join([f"- {title}" for title in section_titles])

    user_prompt = f"""Read the following academic text and generate up to {max_annotations} annotations from your perspective.

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
      "type": "interesting | confusing | disagree | important | question",
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

IMPORTANT: Distribute your annotations across ALL sections, not just one or two.
Aim for approximately {suggested_per_section} annotations per section.
Don't over-focus on a single section - each section likely has interesting points from your perspective.
</Section Coverage>

<Guidelines>
- Generate {max_annotations} diverse annotations spread across different sections
- The "text" field MUST be an exact copy from the document - do not paraphrase
- Each text selection should be 1-3 sentences (not too short, not too long)
- Your reasoning should reflect your specific reading stance
- Look for: assumptions, evidence quality, implications, connections, gaps
</Guidelines>

Generate your annotations now."""

    return system_prompt, user_prompt
