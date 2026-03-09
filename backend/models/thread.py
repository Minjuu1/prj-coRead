from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


class Thread(BaseModel):
    id: str
    paperId: str
    chunkId: str

    # 내용 (텍스트) — id가 아닌 텍스트로 저장
    contestablePoint: str                     # 추출된 논쟁 지점
    seedAnnotationSummaries: List[str]        # annotation summary 텍스트 목록 (id 아님)
    openQuestion: str                         # no predetermined answer — 학생 참여 유도

    status: Literal["locked", "open"] = "locked"
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    # messages는 Firestore 서브컬렉션으로 분리: threads/{threadId}/messages/{msgId}

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["createdAt"] = self.createdAt.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Thread":
        return cls(**data)
