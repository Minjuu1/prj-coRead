from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class LearnerProfile(BaseModel):
    userId: str
    paperId: str
    threadIds: List[str] = []        # 참여한 thread 목록
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["createdAt"] = self.createdAt.isoformat()
        d["updatedAt"] = self.updatedAt.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "LearnerProfile":
        return cls(**data)
