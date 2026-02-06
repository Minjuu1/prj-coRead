from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Section(BaseModel):
    sectionId: str
    title: str
    content: str
    order: int


class ParsedContent(BaseModel):
    sections: List[Section]


class Document(BaseModel):
    documentId: str
    userId: str
    title: str
    originalPdfUrl: Optional[str] = None
    parsedContent: ParsedContent
    threads: List[str] = []
    uploadedAt: datetime
    lastAccessedAt: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
