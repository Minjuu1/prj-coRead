"""
Phase 2: Seed Formation Prompts
Analyze annotations from all agents to find tension points and form discussion seeds.
"""


def get_seed_formation_prompt(annotations_by_agent: dict, sections: list[dict]) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for seed formation.
    annotations_by_agent: {"instrumental": [...], "critical": [...], "aesthetic": [...]}
    """

    system_prompt = """You are an expert at identifying productive discussion opportunities in academic reading.

Your task is to analyze annotations from three different reading perspectives and identify "tension points" -
places where different perspectives converge, conflict, or could enrich each other through discussion.

The three perspectives are:
- Instrumental: Focused on understanding, key concepts, practical application
- Critical: Focused on questioning assumptions, evidence, logic, implications
- Aesthetic: Focused on personal connections, meaning-making, broader significance"""

    # Format annotations
    annotations_text = ""
    for agent_id, annotations in annotations_by_agent.items():
        annotations_text += f"\n\n### {agent_id.upper()} Annotations:\n"
        for i, ann in enumerate(annotations, 1):
            annotations_text += f"""
{i}. [{ann['type']}] Section: {ann.get('sectionTitle', 'Unknown')}
   Text: "{ann['text']}"
   Reasoning: {ann['reasoning']}
"""

    # Format sections for reference
    sections_text = ""
    for section in sections:
        sections_text += f"\n\n## {section['title']}\n{section['content'][:500]}..."

    user_prompt = f"""Analyze these annotations from three reading perspectives and identify 5-6 discussion seeds.

<Annotations from All Agents>
{annotations_text}
</Annotations>

<Document Sections (for reference)>
{sections_text}
</Document Sections>

<Discussion Types>
- position_taking: Agents can take different stances on a claim or interpretation
- deepening: A point worth exploring more deeply through different lenses
- connecting: An opportunity to link abstract ideas to concrete situations or broader themes
</Discussion Types>

<Output Format>
Return a JSON object with a "seeds" array:
{{
  "seeds": [
    {{
      "tensionPoint": "A clear description of what makes this a productive discussion point (1-2 sentences)",
      "discussionType": "position_taking | deepening | connecting",
      "snippetText": "EXACT text from the document that anchors this discussion (must be verbatim from document)",
      "sectionTitle": "The section where snippetText appears",
      "relevantAgents": ["instrumental", "critical", "aesthetic"],
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ]
}}
</Output Format>

<Guidelines>
- Find points where 2+ agents' annotations overlap or create interesting tension
- Each seed should have clear potential for multi-perspective discussion
- The snippetText MUST be exact text from the document - this will be used for highlighting
- Prefer seeds that could lead to substantive intellectual exchange
- Distribute seeds across different sections when possible
- Include at least one of each discussion type
</Guidelines>

Generate 5-6 discussion seeds now."""

    return system_prompt, user_prompt
