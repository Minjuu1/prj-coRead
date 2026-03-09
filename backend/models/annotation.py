from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


class BoundingRect(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    width: float
    height: float


class Annotation(BaseModel):
    id: str
    paperId: str
    chunkId: str
    agent: Literal["critical", "instrumental", "aesthetic"]
    type: Literal["observation", "question", "challenge"]

    # LLM 생성 텍스트
    content: str                          # 에이전트 annotation 전문
    summary: str                          # 1-2문장 압축본 → annotation_memory에 들어가는 것

    # 텍스트 anchor — 반드시 논문 원문 기반 (hallucination 방지)
    targetText: str                       # 논문 원문 exact match
    targetStart: int                      # char offset
    targetEnd: int

    # PDF 렌더링용 좌표 — Phase 1에서 반드시 저장
    pageNumber: int
    boundingRect: BoundingRect
    rects: List[BoundingRect]             # 여러 줄에 걸친 경우

    # 생성 시점 컨텍스트
    understandingAtTime: str              # annotation 생성 당시 evolving_understanding 스냅샷
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        d = self.model_dump()
        d["createdAt"] = self.createdAt.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Annotation":
        return cls(**data)
