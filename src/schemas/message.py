from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Base schema for Message attributes
class MessageBase(BaseModel):
    content: str
    # 移除默认值，允许 None 或从数据库映射
    content_type: Optional[str] = None
    file_path: Optional[str] = None
    is_from_user: bool


# Schema for creating a message
# (needs conversation_id, user_id might come from context)
class MessageCreate(MessageBase):
    conversation_id: int
    # Can be set based on context (logged-in user or None for AI)
    user_id: Optional[int] = None


# Schema for reading a message (includes DB-generated fields)
class Message(MessageBase):
    id: int
    conversation_id: int
    user_id: Optional[int]  # Matches the model
    timestamp: datetime

    class Config:
        from_attributes = True  # Enable ORM mode

# Schema for updating a message (less common, but maybe for status?)
# class MessageUpdate(BaseModel):
#     pass # Add fields if message updates are needed 