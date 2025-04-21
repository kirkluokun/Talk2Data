"""
API路由聚合器，将所有子路由整合起来
"""
from fastapi import APIRouter

from src.api.endpoints import auth, user, chat
from src.core.config import settings

# 创建API路由器
api_router = APIRouter()

# 添加各模块路由
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["auth"]
) 

# 添加用户路由
api_router.include_router(
    user.router,
    prefix="/users",
    tags=["users"]
) 

# 添加聊天路由
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
) 