"""
Phase 2b: Seed Formation Prompts (Cluster-based)

Takes pre-clustered annotations and generates discussion seeds from each cluster.
Replaces the old single-shot approach with cluster-aware seed generation.
"""

from config.discussion import ANNOTATION_TYPES_BY_AGENT


def get_seed_formation_prompt(clusters: list[dict], sections: list[dict]) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt) for seed formation from clusters.

    Args:
        clusters: Output from clustering_service.cluster_annotations()
        sections: Document sections for context
    """

    # Build annotation types explanation for each stance
    stance_types_text = ""
    for agent_id, types in ANNOTATION_TYPES_BY_AGENT.items():
        types_list = ", ".join(types.keys())
        stance_types_text += f"- {agent_id.capitalize()}: {types_list}\n"

    system_prompt = f"""You are an expert at identifying productive discussion opportunities in academic reading.

You will receive PRE-CLUSTERED annotations - annotations that have already been grouped by text proximity within sections.
Your job is to examine each cluster and decide what kind of discussion seed (if any) it produces.

<Stance-Specific Annotation Types>
{stance_types_text}
- Instrumental sees text as a RESOURCE (extract, apply, clarify, gap)
- Critical sees text as an ARGUMENT (question, challenge, counter, assumption)
- Aesthetic sees text as an ENCOUNTER (resonate, remind, surprise, imagine)
</Stance-Specific Annotation Types>

<Cross-Stance Tensions>
Productive tensions between different annotation types:
- Instrumental "extract" vs Critical "assumption": What one takes for granted, the other questions
- Instrumental "gap" vs Critical "challenge": Different reasons for finding something incomplete
- Aesthetic "resonate" vs Critical "question": Emotional response meets analytical scrutiny
- Aesthetic "remind" vs Instrumental "apply": Personal connection meets practical application
</Cross-Stance Tensions>"""

    # Format clusters
    clusters_text = ""
    for cluster in clusters:
        agents_str = ", ".join(cluster["agents"])
        clusters_text += f"\n### {cluster['clusterId']} [{cluster['sectionTitle']}] ({cluster['overlapType']}, agents: {agents_str})\n"
        for ann in cluster["annotations"]:
            clusters_text += f'  - [{ann["agentId"]}:{ann["type"]}] "{ann["text"][:200]}"\n'
            clusters_text += f'    Reasoning: {ann["reasoning"]}\n'

    # Format sections for reference
    sections_text = ""
    for section in sections:
        sections_text += f"\n\n## {section['title']}\n{section['content']}"

    user_prompt = f"""Generate discussion seeds from these annotation clusters.

<Annotation Clusters>
{clusters_text}
</Annotation Clusters>

<Document (for reference)>
{sections_text}
</Document>

<Rules>
1. MULTI-AGENT clusters (2+ agents on overlapping text) → MUST produce a seed
   - These are the richest: different stances noticed the same passage
   - Discussion type depends on the tension between their annotations

2. SINGLE-AGENT clusters with 2+ annotations → SHOULD produce a seed if insightful
   - One agent noticed multiple things about the same passage
   - Can become a comment seed (single agent exploring depth)

3. STANDALONE annotations (1 agent, 1 annotation) → produce a seed only if the observation is particularly noteworthy
   - Skip generic or surface-level observations
   - Keep ones that are provocative, surprising, or open genuine questions

4. Do NOT merge clusters - each seed maps to exactly one cluster
</Rules>

<Seed Types>
- position_taking: Agents disagree or have fundamentally different readings
- deepening: Multiple perspectives probe the same question/gap from different angles
- connecting: Linking the text to broader contexts, experiences, or implications
</Seed Types>

<Output Format>
Return a JSON object with a "seeds" array:
{{
  "seeds": [
    {{
      "clusterId": "cluster_X (which cluster this seed comes from)",
      "tensionPoint": "What makes this worth discussing (1-2 sentences)",
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
- snippetText MUST be an exact copy from the document (for text highlighting)
- tensionPoint should be specific, not generic ("the methodology" → bad, "whether 15 participants suffice for generalization" → good)
- Every multi-agent cluster MUST get a seed
- Be generous with single-agent seeds - more is better than fewer for research purposes
</Quality Criteria>

Generate seeds now."""

    return system_prompt, user_prompt
