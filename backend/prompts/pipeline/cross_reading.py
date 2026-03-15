def get_conflict_analysis_prompt(excerpts_text: str) -> str:
    return f"""You are an expert at analyzing conflict structure in academic discussions.

Below are annotation clusters left by multiple expert agents on the same passages of a paper.
For each cluster (E0, E1, ...), analyze whether the agents' responses contain **meaningful conflict**.

[Annotation Clusters]
{excerpts_text}

---

For each excerpt (E0, E1, ...), determine the following:

**conflict_type**:
- "interpretive" — agents read the same passage differently (one as A, another as B)
- "trade-off" — both are valid but incompatible (efficiency vs. flexibility, short-term vs. long-term, etc.)
- "value-based" — agents differ in what they consider important (pragmatism vs. theoretical rigor, etc.)
- "methodological" — agents use different research/design standards (what methodology is appropriate)
- "none" — agents respond in the same direction or there is no conflict

**conflict_intensity**:
- "high" — interpretations or positions clearly clash, high discussion value
- "medium" — different emphases or latent tension
- "low" — subtle difference, low potential to spark debate
- "none" — no conflict

**key_tension**: the most central tension in this excerpt in one sentence (English)
- empty string "" if conflict_type is "none"

**tension_pair**: the ids of the two agents with the greatest tension (only if applicable)

Be strict — agents being interested in the same thing is not conflict.
Real conflict means "Agent A sees this as a problem but Agent B sees it as a strength."

Return analysis for all excerpts as JSON:
{{
  "analyses": [
    {{
      "index": "E0",
      "conflict_type": "interpretive" | "trade-off" | "value-based" | "methodological" | "none",
      "conflict_intensity": "high" | "medium" | "low" | "none",
      "key_tension": "core tension in one sentence (English)",
      "tension_pair": ["agent-id-1", "agent-id-2"]
    }}
  ]
}}

Respond with JSON only — no other text."""
