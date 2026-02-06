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
    "interesting": AnnotationTypeConfig(
        id="interesting",
        label="Interesting",
        description="Something that catches your attention or seems noteworthy",
    ),
    "confusing": AnnotationTypeConfig(
        id="confusing",
        label="Confusing",
        description="Something unclear, ambiguous, or hard to understand",
    ),
    "disagree": AnnotationTypeConfig(
        id="disagree",
        label="Disagree",
        description="Something you question, doubt, or would challenge",
    ),
    "important": AnnotationTypeConfig(
        id="important",
        label="Important",
        description="A key point, central argument, or crucial finding",
    ),
    "question": AnnotationTypeConfig(
        id="question",
        label="Question",
        description="A question that arises from reading this",
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
