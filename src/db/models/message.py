from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.base import Base


class Message(Base):
    """消息模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    # user_id can be null for AI messages, or point to the conversation initiator
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) 
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default='text') # e.g., 'text', 'dataframe_csv_path', 'plot_file_path', 'error'
    file_path = Column(String(512), nullable=True) # Relative path for CSV or PNG files
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_from_user = Column(Boolean, nullable=False)

    # Optional: Define relationships if needed later
    # conversation = relationship("Conversation", back_populates="messages")
    # user = relationship("User") 