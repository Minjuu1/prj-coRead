"""
Phase 2: Cross-Reading Prompts
Each agent reads other agents' annotations and reacts from their own perspective.
Strong reactions (grounded in own annotations) become discussion starters.
"""

from config.agents import AGENTS
from config.discussion import get_annotation_types_for_agent, ANNOTATION_TYPES


def _format_own_annotations(annotations: list[dict]) -> str:
    """Format an agent's own annotations with IDs for reference."""
    if not annotations:
        return "  (no annotations)"
    lines = []
    for ann in annotations:
        ann_id = ann.get("annotationId", "unknown")
        ann_type = ann.get("type", ann.get("annotationType", ""))
        section = ann.get("sectionTitle", "")
        text = ann.get("text", ann.get("snippetText", ""))[:150]
        reasoning = ann.get("reasoning", "")[:150]
        lines.append(f'  [{ann_id}] ({ann_type}, {section}) "{text}"')
        lines.append(f'    → {reasoning}')
    return "\n".join(lines)


def _format_other_annotations(agent_id: str, annotations: list[dict]) -> str:
    """Format another agent's annotations for cross-reading."""
    agent = AGENTS[agent_id]
    agent_types = get_annotation_types_for_agent(agent_id)
    types_desc = ", ".join([f"{t.id}" for t in agent_types.values()])

    lines = [f"### {agent.name} (reads as: {types_desc})"]
    for ann in annotations:
        ann_id = ann.get("annotationId", "unknown")
        ann_type = ann.get("type", ann.get("annotationType", ""))
        section = ann.get("sectionTitle", "")
        text = ann.get("text", ann.get("snippetText", ""))
        reasoning = ann.get("reasoning", "")
        lines.append(f'  [{ann_id}] ({ann_type}, {section})')
        lines.append(f'    Text: "{text}"')
        lines.append(f'    Reasoning: {reasoning}')
        lines.append("")
    return "\n".join(lines)


def get_cross_reading_prompt(
    reacting_agent_id: str,
    other_agents_annotations: dict[str, list[dict]],
    own_annotations: list[dict],
    sections: list[dict],
) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for cross-reading reaction generation.

    Args:
        reacting_agent_id: The agent doing the cross-reading
        other_agents_annotations: {agent_id: [annotations]} for other agents
        own_annotations: The reacting agent's own annotations (with IDs)
        sections: Document sections for reference
    """
    agent = AGENTS[reacting_agent_id]
    agent_types = get_annotation_types_for_agent(reacting_agent_id)
    type_options = " | ".join(agent_types.keys())

    own_annotations_text = _format_own_annotations(own_annotations)

    system_prompt = f"""You are a reader with the following perspective:

<Your Reading Stance: {agent.name}>
{agent.stance_description}
</Your Reading Stance>

<Voice Constraint>
{agent.voice_constraint}
</Voice Constraint>

You have already read this paper and made your own annotations.
Now you are reading annotations made by other readers who have different perspectives.

Your task: React to their annotations FROM YOUR OWN PERSPECTIVE.
When something they noticed connects to your own reading, say so explicitly.

<Your Own Annotations>
{own_annotations_text}
</Your Own Annotations>

<Your Annotation Types>
{chr(10).join([f"- {t.id}: {t.description}" for t in agent_types.values()])}
</Your Annotation Types>"""

    # Format other agents' annotations
    others_text = ""
    for agent_id, annotations in other_agents_annotations.items():
        others_text += "\n" + _format_other_annotations(agent_id, annotations) + "\n"

    # Format relevant sections (only those containing annotations)
    annotated_sections = set()
    for anns in other_agents_annotations.values():
        for ann in anns:
            annotated_sections.add(ann.get("sectionTitle", ""))
    for ann in own_annotations:
        annotated_sections.add(ann.get("sectionTitle", ""))

    MAX_SECTION_CHARS = 2000
    sections_text = ""
    for section in sections:
        if section['title'] in annotated_sections:
            content = section['content']
            if len(content) > MAX_SECTION_CHARS:
                content = content[:MAX_SECTION_CHARS] + "... [truncated]"
            sections_text += f"\n\n## {section['title']}\n{content}"

    user_prompt = f"""Read the following annotations from other readers and react to the ones that genuinely provoke a response from your perspective.

<Other Readers' Annotations>
{others_text}
</Other Readers' Annotations>

<Document (for reference)>
{sections_text}
</Document>

<Guidelines>
- You do NOT need to react to every annotation — skip ones that don't spark anything from your stance
- When reacting, GROUND your response in your own reading:
  - Reference your own annotation by ID when relevant: "As I noted in [ann_xxx], ..."
  - Show what YOUR stance sees that the other reader's stance structurally cannot
  - Explain WHY this matters — what gets missed if we only look through their lens?
- Prioritize reactions where your stance ADDS A DIFFERENT DIMENSION, not just agreement:
  - Strong: "They extracted the method, but I noticed the participants' language carries something the method summary loses" (different dimension)
  - Strong: "They question the sample size, but the framework is still directly usable if scoped to X — here's how" (partial agreement + own ground)
  - Weak: "Interesting point, I noticed something similar" (mere agreement — avoid)
- Each reaction should be 2-4 sentences, in your natural voice
- Use your own annotation types (not the other reader's types)
- You may partially agree, but always show what your angle STILL sees that theirs doesn't cover
</Guidelines>

<Output Format>
Return a JSON object with a "reactions" array:
{{
  "reactions": [
    {{
      "targetAnnotationId": "the annotation ID you're reacting to",
      "targetAgentId": "instrumental | critical | aesthetic",
      "reactionText": "Your reaction (2-4 sentences, in your voice)",
      "reactionAnnotationType": "{type_options}",
      "ownAnnotationRefs": ["ann_xxx", "ann_yyy"]
    }}
  ]
}}

Note: ownAnnotationRefs should list IDs of YOUR OWN annotations that connect to this reaction.
If none of your annotations are relevant, you can leave this empty — but reactions grounded in your own reading are much stronger.
</Output Format>

React to the annotations that genuinely engage your reading stance now."""

    return system_prompt, user_prompt
