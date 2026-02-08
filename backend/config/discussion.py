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

# Annotation types with descriptions
@dataclass(frozen=True)
class AnnotationTypeConfig:
    id: str
    label: str
    description: str

ANNOTATION_TYPES: Dict[str, AnnotationTypeConfig] = {
    "confusing": AnnotationTypeConfig(
        id="confusing",
        label="Confusing",
        description="Something unclear, ambiguous, or hard to understand",
    ),
    "challenge": AnnotationTypeConfig(
        id="challenge",
        label="Challenge",
        description="Something you disagree with, question, or want to correct",
    ),
    "highlight": AnnotationTypeConfig(
        id="highlight",
        label="Highlight",
        description="A noteworthy point that deserves attention",
    ),
    "connect": AnnotationTypeConfig(
        id="connect",
        label="Connect",
        description="Linking to another concept, experience, or external idea",
    ),
    "probe": AnnotationTypeConfig(
        id="probe",
        label="Probe",
        description="Digging deeper into the issue or asking follow-up questions",
    ),
    "summarize": AnnotationTypeConfig(
        id="summarize",
        label="Summarize",
        description="Synthesizing or summarizing the key points",
    ),
}

# Annotation configuration
ANNOTATION_CONFIG = {
    "max_per_agent": 20,
    "types": list(ANNOTATION_TYPES.keys()),  # derived from ANNOTATION_TYPES
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
