def get_prompt(contested_excerpts_text: str, agent_names: str) -> str:
    return f"""You are an academic discussion designer. Goal: a live debate that surfaces socio-cognitive conflict with clear stakes.

Below are paper passages where multiple expert agents ({agent_names}) have responded in genuinely conflicting ways.
Each excerpt has an analyzed conflict_type and key_tension.

[Contested Excerpts and Agent Annotations]
{contested_excerpts_text}

---

## Thread Design Principles

### What makes a good thread
1. **excerpt_index**: the index of the excerpt this thread addresses (E0, E1, ...)
2. **open_question**: the core issue as one sentence (English) — this is the discussion "title", not the first message
   - Must carry stakes: the "why does this matter" must be visible
   - Bad: "What are the pros and cons of this tool?"
   - Good: "If this tool supports design reasoning, how can we tell whether that reasoning belongs to the researcher or the AI?"
3. **seed_messages**: exactly **4 turns** of genuine conflict between agents
   - author is the agent id (not name)
   - each message 2–4 sentences, drawing specifically on the agent's own annotation
   - **every message must include a stakes or implication move** (see patterns below)
   - Structure: A claims → B challenges → A counter-argues → B sharpens or 3rd agent intervenes

### Stakes/Implication Patterns (must use at least one per message)
- **Implication move**: "If this is [X], then we need to rethink [Y]"
- **Stakes move**: "If that reading is right, we must accept [conclusion Z] — which is unacceptable in [my field] because..."
- **Consequence move**: "This isn't an abstract problem — it concretely leads to [specific outcome]"
- **Assumption expose**: "The moment this paper assumes [X], [Y] becomes invisible"

### Conflict-type dialogue structures

**"trade-off"** — each agent defends their side by naming what is gained and lost
- Turn 1: "This choice gains [X] but loses [Y]. In [my field], losing [Y] means [consequence]"
- Turn 2: "The framing that [Y] is a loss already presupposes [Z perspective]. From [W] view, actually..."
- Turn 3: "For [Z perspective] to hold, [premise A] must be true — but in this research..."
- Turn 4: "Then if [premise A] fails, what this paper calls a solution becomes [reframed problem]"

**"interpretive"** — difference in reading leads to difference in conclusions
- Turn 1: "This passage means [X]. If so, the paper's [Y] rests on different grounds than claimed"
- Turn 2: "That reading ignores [Z]. Reading it as [W] yields completely different implications..."
- Turn 3: "Reading it as [W] requires assuming [condition A], but..."
- Turn 4: "Then both readings share the assumption [V] — and that assumption is what's actually at stake"

**"value-based"** — same facts evaluated against different value standards
- Turn 1: "From [value V], this is [evaluation]. If this research neglects [V]..."
- Turn 2: "Putting [V] first makes [other value W] invisible..."
- Turn 3: "Making [W] visible actually reveals a deeper problem the paper hasn't acknowledged..."
- Turn 4: "Then the real question isn't V vs. W — it's whether the paper can justify its choice at all"

**"methodological"** — different research standards affect credibility of conclusions
- Turn 1: "This methodology doesn't meet [criterion X]. As a result, [conclusion Y] is overclaimed"
- Turn 2: "Applying [criterion X] here presupposes [context assumption] — which doesn't fit this research because..."
- Turn 3: "If [criterion X] doesn't apply, what standard does? The paper doesn't say, which means..."
- Turn 4: "Without a stated standard, any reading of the results is equally valid — including the opposite"

### Absolute prohibitions
- Agreement or praise: "I agree", "great point", "exactly", "interesting"
- Resolution: "therefore [conclusion]", "this can be solved by [method]"
- Stakes-free opinion: "From X perspective, Y is important" (without saying why it matters)
- Copying the open_question verbatim as the first seed message
- Two consecutive messages by the same agent

Return 5–7 threads as JSON:
{{
  "threads": [
    {{
      "excerpt_index": "E0",
      "open_question": "Stakes-bearing core issue (English, 1 sentence)",
      "suggested_agent": "agent id who leads this thread",
      "seed_messages": [
        {{"author": "agent-id", "content": "position claim + stakes (English, 2–4 sentences)"}},
        {{"author": "different-agent-id", "content": "direct challenge + counter-stakes (English, 2–4 sentences)"}},
        {{"author": "first-agent-id", "content": "counter-argument — attack the premise or deepen implication (English, 2–4 sentences)"}},
        {{"author": "agent-id", "content": "sharpening or 3rd-agent intervention — surface a deeper problem (English, 2–4 sentences)"}}
      ]
    }}
  ]
}}

Respond with JSON only — no other text."""
