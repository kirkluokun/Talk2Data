from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update, func
from typing import List, Optional

from src.db.models import Conversation, Message, User # Keep User
from src.db.models.job import Job  # Import Job model
from src.schemas import ConversationCreate, ConversationUpdate


async def create_conversation(db: AsyncSession, conv_in: ConversationCreate, user: User) -> Conversation:
    """创建一个新的对话"""
    # Use model_dump for Pydantic v2 compatibility
    db_conv = Conversation(**conv_in.model_dump(), user_id=user.id)
    db.add(db_conv)
    # Removed await db.commit()
    await db.flush() # Flush to get ID/defaults assigned
    await db.refresh(db_conv)
    return db_conv

async def get_conversation_by_id(db: AsyncSession, conversation_id: int, user_id: int) -> Optional[Conversation]:
    """根据ID获取特定用户的对话"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
    )
    return result.scalars().first()

async def get_conversations_by_user(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
    """获取特定用户的所有对话（分页），按更新时间降序，NULLS LAST。"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        # Order by most recently updated, NULLs last to ensure non-updated items are at the end
        .order_by(Conversation.updated_at.desc().nullslast())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def update_conversation(db: AsyncSession, conversation_id: int, user_id: int, conv_in: ConversationUpdate) -> Optional[Conversation]:
    """更新特定用户的对话（例如，标题），让数据库自动更新 updated_at。"""
    update_data = conv_in.model_dump(exclude_unset=True)
    if not update_data:
        # If no data to update, just return the current conversation
        return await get_conversation_by_id(db, conversation_id, user_id)

    # Remove explicit setting of updated_at. Let the DB handle it via onupdate.
    # update_data['updated_at'] = func.now()

    stmt = (
        update(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .values(**update_data)
        # Remove returning clause to get rowcount attribute on result
        # .returning(Conversation.updated_at) 
    )
    result = await db.execute(stmt)
    # await db.flush() # execute should handle flush for simple update without returning

    # Check if update occurred using rowcount
    if result.rowcount == 0:
        return None # Conversation not found or no update happened

    # Expire the object in the session *before* fetching again to ensure DB state is loaded
    # Use db.get for efficient primary key lookup if the object might be loaded
    cached_conv = await db.get(Conversation, conversation_id)
    if cached_conv:
        # Use db.expire, not await db.expire
        db.expire(cached_conv)

    # Fetch the updated conversation to get all fields including the new updated_at
    # Because we expired it, this fetch should hit the database
    conv = await get_conversation_by_id(db, conversation_id, user_id)
    # Explicitly refresh the object after fetching to be absolutely sure
    if conv:
        await db.refresh(conv)
    return conv


async def delete_conversation_and_messages(db: AsyncSession, conversation_id: int, user_id: int) -> bool:
    """删除特定用户的对话及其所有消息，同时删除关联的 Job 记录"""
    try:
        # 1. Delete associated jobs first to avoid foreign key violation
        await db.execute(delete(Job).where(Job.conversation_id == conversation_id))
        await db.flush() # Flush job deletion
        
        # 2. Delete messages (Optional if cascade is working)
        await db.execute(delete(Message).where(Message.conversation_id == conversation_id))
        await db.flush() # Flush message deletion

        # 3. Delete the conversation
        result = await db.execute(
            delete(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        await db.flush() # Flush conversation deletion
        
        # 4. Commit the transaction to make changes permanent
        await db.commit()
        
        return result.rowcount > 0 # Return True if conversation was deleted
    except Exception as e:
        print(f"Error deleting conversation {conversation_id} for user {user_id}: {e}")
        await db.rollback() # Rollback transaction on error
        return False # Indicate failure 