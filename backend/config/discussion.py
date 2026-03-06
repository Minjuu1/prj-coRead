from dataclasses import dataclass
from typing import Dict, List

# Thread configuration
THREAD_CONFIG = {
    "min_participants_for_discussion": 2,
    "default_turns": 4,
    "additional_turns": 4,
    "max_turns": 20,
}

# Annotation types with descriptions - stance-specific
# Each stance has its own vocabulary that reflects its relationship to the text
@dataclass(frozen=True)
class AnnotationTypeConfig:
    id: str
    stance: str  # "instrumental" | "critical" | "aesthetic"
    label: str
    description: str

ANNOTATION_TYPES: Dict[str, AnnotationTypeConfig] = {
    # Instrumental - text as resource (concepts, information)
    "note": AnnotationTypeConfig(
        id="note", stance="instrumental", label="Note",
        description="Identifies key concepts, methods, or findings worth retaining — captures what's practically useful or important to understand",
    ),
    "stuck": AnnotationTypeConfig(
        id="stuck", stance="instrumental", label="Stuck",
        description="Flags where understanding breaks down — missing information, unclear explanations, or insufficient detail that blocks comprehension or application",
    ),

    # Critical - text as argument (inferences, assumptions, point of view)
    "question": AnnotationTypeConfig(
        id="question", stance="critical", label="Question",
        description="Probes the evidence, logic, or methodology — challenges whether conclusions follow from the data presented",
    ),
    "uncover": AnnotationTypeConfig(
        id="uncover", stance="critical", label="Uncover",
        description="Surfaces unstated premises, hidden biases, or ideological framings that shape the argument without being made explicit",
    ),
    "alternative": AnnotationTypeConfig(
        id="alternative", stance="critical", label="Alternative",
        description="Offers a different interpretation, counterexample, or point of view the author doesn't consider",
    ),

    # Aesthetic - text as encounter (personal response, implications)
    "struck": AnnotationTypeConfig(
        id="struck", stance="aesthetic", label="Struck",
        description="Responds to what personally resonates, surprises, or moves — evoking memories, emotions, or a shift in perspective",
    ),
    "implication": AnnotationTypeConfig(
        id="implication", stance="aesthetic", label="Implication",
        description="Explores where the idea leads — its consequences, possibilities, or connections to other contexts and experiences",
    ),
}

# Pre-computed mapping for efficient agent-specific lookup
ANNOTATION_TYPES_BY_AGENT: Dict[str, Dict[str, AnnotationTypeConfig]] = {
    agent_id: {k: v for k, v in ANNOTATION_TYPES.items() if v.stance == agent_id}
    for agent_id in ["instrumental", "critical", "aesthetic"]
}

def get_annotation_types_for_agent(agent_id: str) -> Dict[str, AnnotationTypeConfig]:
    """Returns annotation types available for a specific agent/stance."""
    return ANNOTATION_TYPES_BY_AGENT.get(agent_id, {})

def get_all_annotation_type_ids() -> List[str]:
    """Returns all annotation type IDs."""
    return list(ANNOTATION_TYPES.keys())

# Annotation configuration
ANNOTATION_CONFIG = {
    "min_per_agent": 5,
    "max_per_agent": 7,
    "types_per_agent": {
        agent_id: list(types.keys())
        for agent_id, types in ANNOTATION_TYPES_BY_AGENT.items()
    },
}

# Cross-reading configuration
CROSS_READING_CONFIG = {
    "min_reaction_length": 50,  # chars, below = weak
    "require_own_annotation_ref": True,  # must reference own annotations to be strong
}
