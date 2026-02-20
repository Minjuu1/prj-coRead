# CoRead Implementation Log

Changes and design decisions tracked during development.

---

## 2026-02-20: Annotation Types Redesign (12 → 7)

### Problem
- Original 12 types (4 per stance) had too much overlap
- `extract` sounded mechanical, not like a reading reaction
- Instrumental `apply` overlapped with Aesthetic `imagine`
- Critical `challenge`/`counter` were hard to distinguish from `question`
- `clarify` vs `apply` distinction unclear in practice

### Design Process
- Started from reader reactions: "what do you actually feel when reading?"
- Referenced Paul & Elder's **Elements of Thought** framework:
  - Purpose, Questions, Information, Inferences, Concepts, Implications, Assumptions, Point of View
- Mapped elements to stances for theoretical grounding
- Merged `resonate` + `surprise` → `struck` (both are personal reactions)
- Moved `apply` (context linking) to Aesthetic as `implication` — connecting to other contexts is aesthetic, not instrumental

### Final Types (7 total)

| Stance | Type | Reaction | Elements of Thought |
|--------|------|----------|-------------------|
| **Instrumental** | `note` | "This is key" | Concepts, Information |
| **Instrumental** | `stuck` | "I don't get this" | Questions |
| **Critical** | `question` | "Is this valid?" | Inferences |
| **Critical** | `uncover` | "Hidden premise here" | Assumptions |
| **Critical** | `alternative` | "Another reading is possible" | Point of View |
| **Aesthetic** | `struck` | "This hits me" | Personal response |
| **Aesthetic** | `implication` | "Where does this lead?" | Implications |

### Changes Made
- `backend/config/discussion.py` — Type definitions
- `backend/models/thread.py` — AnnotationType Literal
- `backend/prompts/pipeline/seed_formation.py` — Cross-stance tension examples
- `backend/prompts/pipeline/discussion.py` — Cross-reference guideline
- `frontend/src/constants/annotation.ts` — FE type definitions + ANNOTATION_TYPES_BY_AGENT

### Previous Types (for reference)
```
Instrumental: extract, apply, clarify, gap
Critical: question, challenge, counter, assumption
Aesthetic: resonate, remind, surprise, imagine
```

---

## 2026-02-20: Phase 2 Split into Clustering (2a) + Seed Formation (2b)

### Problem
- Phase 2 was a single LLM call that had to both find overlaps AND generate seeds
- Hard to control seed quality when LLM does everything at once
- No visibility into which annotations were actually related

### Solution
- **Phase 2a (Clustering)**: Deterministic text-proximity grouping via `clustering_service.py`
  - Groups annotations by section + text overlap
  - No LLM needed — pure string matching
  - Output: clusters with multi-agent / single-agent labels
- **Phase 2b (Seed Formation)**: LLM generates seeds per-cluster
  - Each cluster → 0 or 1 seed
  - No hard limit on seed count (driven by cluster quality)
  - Multi-agent clusters MUST produce a seed

### Changes Made
- New file: `backend/services/clustering_service.py`
- `backend/services/pipeline_service.py` — Pipeline flow updated
- `backend/api/pipeline.py` — `targetSeeds` param removed, `clusters` field added
- `backend/prompts/pipeline/seed_formation.py` — Prompt rewritten for cluster input
- `frontend/src/pages/admin/PipelineDashboard.tsx` — Cluster visualization panel

---

## 2026-02-20: Agent Voice Constraints

### Problem
- Agents would narrate their stance ("As a critical reader, I challenge...")
- Annotation reasoning sounded like formal reports, not margin notes

### Solution
- Separated `voice_constraint` field in `AgentConfig`
- Added anti-narration rules per agent
- Annotation prompt: reasoning should read like margin notes, not formal analysis
- Added Conclusion/Abstract deprioritization to reduce redundant annotations

### Changes Made
- `backend/config/agents.py` — `voice_constraint` field added
- `backend/prompts/pipeline/annotation.py` — Voice constraint injection + tone guidance

---

## 2026-02-20: Agent Memory System

### Design
- Per-agent, per-document memory stored in Firebase
- Memory types: AnnotationMemory, ThoughtMemory, InteractionMemory
- Phase 1: annotations stored in memory
- Phase 4: memory formatted and injected into discussion prompts
- After discussion: new thoughts stored back

### Key Files
- `backend/models/memory.py` — Data structures
- `backend/services/memory_service.py` — CRUD + prompt formatting
- `backend/services/pipeline_service.py` — Memory integration points
- `backend/prompts/pipeline/discussion.py` — Memory injection in prompts
