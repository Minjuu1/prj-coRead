from pydantic import BaseModel
from typing import List, Dict, Any


class Chunk(BaseModel):
    id: str
    paperId: str
    content: str                        # 텍스트 (LLM 컨텍스트에 들어가는 것)
    section: str                        # 섹션 제목
    position: float                     # 논문 내 상대적 위치 (0.0 ~ 1.0)
    charStart: int
    charEnd: int
    pageStart: int
    pageEnd: int
    rects: List[Dict[str, Any]] = []    # Grobid 좌표 [{"page", "x", "y", "w", "h"}]
    linkedChunks: List[str] = []        # cross-reference chunk id 목록

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(**data)
