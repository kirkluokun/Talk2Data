"""
用户相关API端点实现
"""
from fastapi import APIRouter, Depends
from typing import Any

from src.db.models.user import User
from src.api.deps import get_current_active_user
from src.schemas.user import User as UserSchema

router = APIRouter()


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    获取当前登录用户信息
    
    Args:
        current_user: 当前认证用户
        
    Returns:
        User: 当前用户信息
    """
    return current_user 