from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Base schema for Conversation attributes shared across create and read
class ConversationBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)


# Schema for creating a new conversation
# (might not need user_id here if it comes from auth)
class ConversationCreate(ConversationBase):
    title: Optional[str] = Field("New Conversation", max_length=255)


# Schema for reading a conversation (includes DB-generated fields)
class Conversation(ConversationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None # Match model definition (can be None initially)

    class Config:
        from_attributes = True  # Enable ORM mode


# Schema for updating a conversation (optional fields)
class ConversationUpdate(ConversationBase):
    updated_at: Optional[datetime] = None # Allow explicitly setting updated_at for tests 