from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.base import Base


class Job(Base):
    """任务状态模型 (对应 Celery Task)"""
    __tablename__ = "jobs"

    id = Column(String(255), primary_key=True, index=True) # Celery Task ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True, index=True) # Link job to a conversation

    query_text = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, index=True) # e.g., PENDING, STARTED, SUCCESS, FAILURE
    progress = Column(Integer, nullable=True) # 0-100
    stage = Column(String(255), nullable=True) # Description of the current stage

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    result_type = Column(String(50), nullable=True) # 'text', 'dataframe_csv_path', etc.
    result_path = Column(String(512), nullable=True) # File path if applicable
    result_content = Column(Text, nullable=True) # Store text result or maybe JSON
    error_message = Column(Text, nullable=True)

    # Optional: Define relationships if needed later
    # user = relationship("User")
    # conversation = relationship("Conversation") 