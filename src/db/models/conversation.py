from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from src.db.base import Base


class Conversation(Base):
    """对话模型"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    title = Column(String(255), nullable=True, default="New Conversation")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.statement_timestamp()
    )

    # Optional: Define relationships if needed later
    # user = relationship("User")
    # messages = relationship(
    #     "Message", 
    #     back_populates="conversation", 
    #     cascade="all, delete-orphan"
    # ) 