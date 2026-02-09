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
    # Instrumental - text as resource (extract, apply, organize)
    "extract": AnnotationTypeConfig(
        id="extract", stance="instrumental", label="Extract",
        description="Pulls out key concepts, definitions, or methods that can be reused or built upon",
    ),
    "apply": AnnotationTypeConfig(
        id="apply", stance="instrumental", label="Apply",
        description="Suggests how this idea could be applied in another context or project",
    ),
    "clarify": AnnotationTypeConfig(
        id="clarify", stance="instrumental", label="Clarify",
        description="Adds interpretation to make unclear parts more understandable",
    ),
    "gap": AnnotationTypeConfig(
        id="gap", stance="instrumental", label="Gap",
        description="Points out missing or insufficient information that blocks understanding",
    ),

    # Critical - text as argument (question, evaluate, deconstruct)
    "question": AnnotationTypeConfig(
        id="question", stance="critical", label="Question",
        description="Raises questions about the evidence or logical connections",
    ),
    "challenge": AnnotationTypeConfig(
        id="challenge", stance="critical", label="Challenge",
        description="Points out weaknesses, overgeneralizations, or logical leaps in the argument",
    ),
    "counter": AnnotationTypeConfig(
        id="counter", stance="critical", label="Counter",
        description="Offers alternative explanations or counterexamples the author didn't consider",
    ),
    "assumption": AnnotationTypeConfig(
        id="assumption", stance="critical", label="Assumption",
        description="Reveals unstated premises or ideological biases underlying the argument",
    ),

    # Aesthetic - text as encounter (resonate, connect, imagine)
    "resonate": AnnotationTypeConfig(
        id="resonate", stance="aesthetic", label="Resonate",
        description="Responds to parts that personally resonate or evoke emotional reaction",
    ),
    "remind": AnnotationTypeConfig(
        id="remind", stance="aesthetic", label="Remind",
        description="Shares associations with personal experiences, other texts, or real-world cases",
    ),
    "surprise": AnnotationTypeConfig(
        id="surprise", stance="aesthetic", label="Surprise",
        description="Reacts to parts that broke expectations or opened new perspectives",
    ),
    "imagine": AnnotationTypeConfig(
        id="imagine", stance="aesthetic", label="Imagine",
        description="Extends the idea or imagines possibilities in different contexts",
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
