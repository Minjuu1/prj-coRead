from pydantic import BaseModel
from typing import List


class Chunk(BaseModel):
    id: str
    paperId: str
    content: str                  # 텍스트 (LLM 컨텍스트에 들어가는 것)
    section: str                  # 섹션 제목
    position: float               # 논문 내 상대적 위치 (0.0 ~ 1.0)
    charStart: int
    charEnd: int
    pageStart: int
    pageEnd: int
    linkedChunks: List[str] = []  # cross-reference chunk id 목록 (DB 참조용)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(**data)
