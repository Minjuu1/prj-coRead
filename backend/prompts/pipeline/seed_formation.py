"""
Phase 2: Seed Formation Prompts
Analyze annotations from all agents to find tension points and form discussion seeds.
"""

from config.discussion import ANNOTATION_TYPES_BY_AGENT


def get_seed_formation_prompt(annotations_by_agent: dict, sections: list[dict]) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for seed formation.
    annotations_by_agent: {"instrumental": [...], "critical": [...], "aesthetic": [...]}
    """

    # Build annotation types explanation for each stance
    stance_types_text = ""
    for agent_id, types in ANNOTATION_TYPES_BY_AGENT.items():
        types_list = ", ".join(types.keys())
        stance_types_text += f"- {agent_id.capitalize()}: {types_list}\n"

    system_prompt = f"""You are an expert at identifying productive discussion opportunities in academic reading.

Your task is to analyze annotations from three different reading perspectives and identify "tension points" -
places where different perspectives converge, conflict, or could enrich each other through discussion.

The three perspectives and their annotation vocabularies:

<Stance-Specific Annotation Types>
{stance_types_text}
Note: Each stance has its own annotation vocabulary that reflects how they relate to text.
- Instrumental sees text as a RESOURCE (extract, apply, clarify, gap)
- Critical sees text as an ARGUMENT (question, challenge, counter, assumption)
- Aesthetic sees text as an ENCOUNTER (resonate, remind, surprise, imagine)
</Stance-Specific Annotation Types>

<Finding Cross-Stance Tensions>
Look for productive tensions between different annotation types:
- Instrumental's "extract" vs Critical's "assumption": What one takes for granted, the other questions
- Instrumental's "gap" vs Critical's "challenge": Different reasons for finding something incomplete
- Aesthetic's "resonate" vs Critical's "question": Emotional response meets analytical scrutiny
- Aesthetic's "remind" vs Instrumental's "apply": Personal connection meets practical application
</Finding Cross-Stance Tensions>"""

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
        sections_text += f"\n\n## {section['title']}\n{section['content']}"

    # Count sections for distribution guidance
    section_titles = [s['title'] for s in sections]
    num_sections = len(section_titles)

    user_prompt = f"""Analyze these annotations from three reading perspectives and create discussion seeds.

<Annotations from All Agents>
{annotations_text}
</Annotations>

<Document Sections (for reference)>
{sections_text}
</Document Sections>

<Seed Types>
1. DISCUSSION SEEDS (2+ agents, will become multi-turn discussions):
   - position_taking: Critical vs Instrumental tension - questioning vs understanding
   - deepening: Multiple perspectives probing the same question deeper
   - connecting: Linking ideas across contexts (Aesthetic's specialty)

2. COMMENT SEEDS (1 agent, will become single comments):
   - A notable standalone observation that deserves attention
   - Often Aesthetic's unique connections or Critical's pointed questions
   - Mark with relevantAgents: [single_agent_id]
</Seed Types>

<Distribution Requirements>
MUST include:
- 2-3 multi-agent DISCUSSION seeds (position_taking or deepening)
- 1-2 single-agent COMMENT seeds (preserve unique observations)
- At least 1 connecting seed (Aesthetic-driven)

Section coverage:
- Spread across at least {min(3, num_sections)} different sections
- Don't cluster all seeds in one section
</Distribution Requirements>

<Output Format>
Return a JSON object with a "seeds" array (total 5-7 seeds):
{{
  "seeds": [
    {{
      "tensionPoint": "What makes this a productive discussion/comment point (1-2 sentences)",
      "discussionType": "position_taking | deepening | connecting",
      "snippetText": "EXACT verbatim text from the document for highlighting",
      "sectionTitle": "Section where snippetText appears",
      "relevantAgents": ["agent1", "agent2"] or ["single_agent"] for comments,
      "keywords": ["keyword1", "keyword2", "keyword3"]
    }}
  ]
}}
</Output Format>

<Quality Criteria>
- position_taking: Best when Critical questions something Instrumental accepts (or vice versa)
- deepening: Best when multiple agents notice the same gap/complexity
- connecting: Best when Aesthetic links to experience/context others missed
- Single-agent comments: Preserve if the observation is insightful even without debate
- snippetText MUST be exact copy from document (will be used for text highlighting)
</Quality Criteria>

Generate the seeds now, ensuring you meet the distribution requirements."""

    return system_prompt, user_prompt
