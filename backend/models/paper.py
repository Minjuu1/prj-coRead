from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class Paper(BaseModel):
    id: str
    title: str
    url: str                                      # Firebase Storage URL
    status: Literal["processing", "ready", "error"]
    summary: Optional[str] = None                 # 논문 전체 요약 (Phase 1에서 생성)
    uploadedAt: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["uploadedAt"] = self.uploadedAt.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Paper":
        return cls(**data)
