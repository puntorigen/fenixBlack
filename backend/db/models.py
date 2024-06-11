from typing import Optional, List, TypeVar
from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.types import JSON
from pydantic import field_serializer, field_validator
import json

T = TypeVar("T", bound=SQLModel)

"""
class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str
    comments: List[str] = Field(default=[], sa_column=Column(JSON))
    date: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('comments', mode='before')
    def validate_comments(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_serializer('comments')
    def serialize_comments(cls, v):
        return json.dumps(v)

class Scanned(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str
    url: str
    category: str
    data: dict = Field(sa_column=Column(JSON))
    date: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True
"""