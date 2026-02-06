from pydantic import BaseModel
from typing import List
from datetime import datetime


class User(BaseModel):
    userId: str
    createdAt: datetime
    documents: List[str] = []

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
