from pydantic import BaseModel
from typing import Literal


class DynamicAgent(BaseModel):
    id: str              # slug, e.g. "computer-scientist"
    name: str            # Korean display name, e.g. "컴퓨터 과학자"
    field: str           # English field name, e.g. "Computer Science"
    reading_lens: str    # How this agent reads — short phrase (Korean)
    system_prompt: str   # Full system prompt for this agent (Korean)
    color_index: int     # 0–7, assigned in order

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "DynamicAgent":
        return cls(**data)


class AgentAnnotation(BaseModel):
    id: str
    agent_id: str
    chunk_id: str
    section: str
    position: float                                              # 0.0–1.0, paper position
    annotation_type: Literal["observation", "question", "tension"]
    content: str                                                 # agent's reaction (Korean)
    quote: str                                                   # verbatim from chunk

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "AgentAnnotation":
        return cls(**data)
