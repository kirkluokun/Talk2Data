"""
认证相关API端点实现，包括注册、登录等
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from typing import Any

from src.db.base import get_db
from src.db.crud.user import create_user, get_user_by_email
from src.schemas.user import UserCreate, User
from src.schemas.token import Token
from src.core.config import settings
from src.core.security import verify_password, create_access_token

router = APIRouter()


@router.post("/register", response_model=User)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    注册新用户
    
    Args:
        user_in: 用户注册信息
        db: 数据库会话
        
    Returns:
        User: 创建的用户信息（不含密码）
        
    Raises:
        HTTPException: 用户邮箱已被注册时
    """
    # 检查邮箱是否已被注册
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册"
        )
    
    # 创建新用户
    user = await create_user(db, user_in=user_in)
    
    return user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    获取访问令牌
    
    Args:
        form_data: OAuth2表单数据（用户名、密码）
        db: 数据库会话
        
    Returns:
        Token: 包含访问令牌和令牌类型
        
    Raises:
        HTTPException: 认证失败时
    """
    # 认证用户
    user = await get_user_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    
    # 创建访问令牌，以用户ID作为subject
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},  # 使用用户ID作为subject
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"} 