from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class Message(BaseModel):
    id: str
    author: Literal["critical", "instrumental", "aesthetic", "student"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(**data)
