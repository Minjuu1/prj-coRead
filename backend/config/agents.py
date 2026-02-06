from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class AgentConfig:
    id: str
    name: str
    color: str
    stance_description: str

AGENTS: Dict[str, AgentConfig] = {
    "instrumental": AgentConfig(
        id="instrumental",
        name="Instrumental",
        color="#F59E0B",
        stance_description="""Focused on practical understanding and application.
Reading goals:
- Identifying key concepts and ideas
- Clarifying understanding and interpretation
- Finding unresolved gaps that block comprehension""",
    ),
    "critical": AgentConfig(
        id="critical",
        name="Critical",
        color="#3B82F6",
        stance_description="""Focused on questioning and analyzing.
Reading goals:
- Questioning assumptions
- Questioning evidence or reasoning
- Examining implications or consequences""",
    ),
    "aesthetic": AgentConfig(
        id="aesthetic",
        name="Aesthetic",
        color="#A855F7",
        stance_description="""Focused on connecting and expanding meaning.
Reading goals:
- Connecting the idea to personal experience
- Expanding meaning of idea
- Generating new connections or possibilities""",
    ),
}

AGENT_IDS = list(AGENTS.keys())
