"""
对话历史API端点

提供对话历史的管理接口，包括：
- 获取用户的所有对话
- 获取特定对话的消息
- 删除对话
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
import os

from src.api import deps
from src.db import crud
from src.db.models.user import User
from src.schemas.conversation import Conversation
from src.schemas.message import Message

# 获取项目根目录 (与 api_workflow.py 保持一致)
current_dir_chat = os.path.dirname(os.path.abspath(__file__))
parent_dir_chat = os.path.dirname(current_dir_chat)
root_dir_chat = os.path.dirname(parent_dir_chat)  # 项目根目录

def convert_absolute_to_relative_path_chat(path, root_dir):
    """将绝对路径转换为相对路径 (chat.py 版本)
    
    Args:
        path: 绝对路径
        root_dir: 项目根目录
        
    Returns:
        str: 转换后的相对路径
    """
    if not path or not isinstance(path, str):
        return path
        
    # 去除路径中可能包含的项目根目录部分
    if path.startswith(root_dir):
        path = path[len(root_dir):].lstrip('/')
    
    # 确保路径不包含 ./output/ 或 ../output/ 前缀
    path = path.replace('./output/', 'output/')
    path = path.replace('../output/', 'output/')
    
    # 处理 output 路径
    if not path.startswith('output/') and 'output/' in path:
        path = path[path.index('output/'):]
        
    return path

# 创建路由器
router = APIRouter()


@router.get("/history", response_model=List[Conversation])
async def get_conversations(
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    获取当前用户的所有对话历史
    
    Args:
        current_user: 当前认证用户
        db: 数据库会话
        
    Returns:
        List[Conversation]: 对话列表
    """
    conversations = await crud.conversation.get_conversations_by_user(
        db=db, 
        user_id=current_user.id
    )
    return conversations


@router.get("/conversation/{conversation_id}", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    获取特定对话的所有消息
    
    Args:
        conversation_id: 对话ID
        current_user: 当前认证用户
        db: 数据库会话
        
    Returns:
        List[Message]: 消息列表
    """
    # 验证对话归属
    conversation = await crud.conversation.get_conversation_by_id(
        db=db, 
        conversation_id=conversation_id, 
        user_id=current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到指定的对话或该对话不属于当前用户"
        )
    
    # 获取消息
    messages = await crud.message.get_messages_by_conversation(
        db=db, 
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    # ---- 修改返回消息的处理 ----
    processed_messages = []
    for msg in messages:
        # 转换路径为相对路径 (仅对 AI 消息且有路径时)
        if not msg.is_from_user and msg.file_path:
            msg.file_path = convert_absolute_to_relative_path_chat(
                msg.file_path, root_dir_chat
            )
        processed_messages.append(msg)
        
    # --- 移除调试日志 ---
    # print(
    #    f"DEBUG: Processed messages being sent to frontend for "
    #    f"conversation {conversation_id}:"
    # )
    # for p_msg in processed_messages:
    #     # 只打印关键字段以方便查看
    #     print(
    #        f"  - ID: {p_msg.id}, User: {p_msg.is_from_user}, "
    #        f"Type: {p_msg.content_type}, Path: {p_msg.file_path}, "
    #        f"Content: {p_msg.content[:50]}..."
    #     )
    # --- 结束移除调试日志 ---
            
    return processed_messages
    # ---- 结束修改 ----


@router.delete("/conversation/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    删除特定对话及其所有消息
    
    Args:
        conversation_id: 对话ID
        current_user: 当前认证用户
        db: 数据库会话
        
    Returns:
        Response: 无内容响应
    """
    # 验证对话归属
    conversation = await crud.conversation.get_conversation_by_id(
        db=db, 
        conversation_id=conversation_id, 
        user_id=current_user.id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到指定的对话或该对话不属于当前用户"
        )
    
    # 删除对话及其消息
    deleted = await crud.conversation.delete_conversation_and_messages(
        db=db, 
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除对话失败"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT) 