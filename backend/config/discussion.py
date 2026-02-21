from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class DiscussionTypeConfig:
    id: str
    label: str
    description: str
    prompt_guidance: str

DISCUSSION_TYPES: Dict[str, DiscussionTypeConfig] = {
    "position_taking": DiscussionTypeConfig(
        id="position_taking",
        label="Position Taking",
        description="Agents take opposing stances on a claim",
        prompt_guidance="Take a clear stance and engage with opposing views",
    ),
    "deepening": DiscussionTypeConfig(
        id="deepening",
        label="Deepening",
        description="Agents probe a critical question more deeply",
        prompt_guidance="Ask probing questions and explore nuances",
    ),
    "connecting": DiscussionTypeConfig(
        id="connecting",
        label="Connecting",
        description="Agents bring in concrete situations and generalize",
        prompt_guidance="Bring concrete examples and make generalizations",
    ),
}

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
    "max_per_agent": 20,
    "types_per_agent": {
        agent_id: list(types.keys())
        for agent_id, types in ANNOTATION_TYPES_BY_AGENT.items()
    },
}

# Seed configuration
SEED_CONFIG = {
    "target_count_min": 5,
    "target_count_max": 6,
    "overlap_levels": ["exact", "paragraph", "section", "thematic"],
}

# Agent Action Types - actions agents can take during discussion
# TODO: Enable when implementing memory-based discussions
# @dataclass(frozen=True)
# class AgentActionConfig:
#     id: str
#     label: str
#     description: str
#
# AGENT_ACTIONS: Dict[str, AgentActionConfig] = {
#     "speak": AgentActionConfig(
#         id="speak",
#         label="Speak",
#         description="Simply respond in the conversation",
#     ),
#     "search": AgentActionConfig(
#         id="search",
#         label="Search",
#         description="Look up external information to support the discussion",
#     ),
#     "reference": AgentActionConfig(
#         id="reference",
#         label="Reference",
#         description="Quote or reference another part of the document",
#     ),
#     "recall": AgentActionConfig(
#         id="recall",
#         label="Recall",
#         description="Recall a previous annotation from memory",
#     ),
# }
#
# AGENT_ACTION_IDS = list(AGENT_ACTIONS.keys())
