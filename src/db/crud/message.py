from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from src.db.models import Message, Conversation # Import Conversation for checks
from src.schemas import MessageCreate


async def create_message(
    db: AsyncSession, message_in: MessageCreate, user_id: Optional[int] = None
) -> Message:
    """创建一条新消息"""
    # Handle user_id assignment based on message_in or passed argument
    assigned_user_id = (
        message_in.user_id if message_in.user_id is not None else user_id
    )
    # Use model_dump and ensure None values are included
    message_data = message_in.model_dump(
        exclude={'user_id'}, exclude_none=False
    )
    db_message = Message(**message_data, user_id=assigned_user_id)
    db.add(db_message)
    # Removed await db.commit()
    await db.flush() # Flush to get ID/defaults assigned
    await db.refresh(db_message)
    return db_message

async def get_messages_by_conversation(
    db: AsyncSession, conversation_id: int, user_id: int, skip: int = 0, limit: int = 100
) -> List[Message]:
    """获取特定用户对话的所有消息（分页，按时间戳升序）"""
    # 验证对话属于用户
    conv_result = await db.execute(
        select(Conversation.id).where(
            Conversation.id == conversation_id, 
            Conversation.user_id == user_id
        )
    )
    if not conv_result.scalars().first():
        return [] # 如果对话不存在或不属于用户，返回空列表
    
    # 查询消息
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp.asc()) # 按时间戳升序显示消息
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

# Get a single message by ID (less common, but potentially useful)
async def get_message_by_id(db: AsyncSession, message_id: int) -> Optional[Message]:
    """根据ID获取单条消息"""
    result = await db.execute(select(Message).where(Message.id == message_id))
    return result.scalars().first() 