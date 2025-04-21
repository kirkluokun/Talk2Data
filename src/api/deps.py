"""
API依赖项实现，包括认证、授权等
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.base import get_db
from src.db.crud.user import get_user_by_email, get_user_by_id
from src.db.models.user import User
from src.core.config import settings
from src.schemas.token import TokenData

# OAuth2密码Bearer流程，指定token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    验证JWT令牌并获取当前用户
    
    Args:
        token: JWT访问令牌
        db: 数据库会话
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 令牌无效或用户不存在时
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 获取用户ID或邮箱
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            email: str = payload.get("email")
            if email is None:
                raise credentials_exception
            token_data = TokenData(email=email)
        else:
            token_data = TokenData(user_id=int(user_id))
            
        # 检查令牌是否过期
        exp = payload.get("exp")
        if exp is not None:
            if datetime.fromtimestamp(exp) < datetime.utcnow():
                raise credentials_exception
                
    except JWTError:
        raise credentials_exception
        
    # 从数据库获取用户
    if token_data.user_id:
        user = await get_user_by_id(db, token_data.user_id)
    elif token_data.email:
        user = await get_user_by_email(db, token_data.email)
    else:
        raise credentials_exception
        
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    验证当前用户是否处于活跃状态
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前活跃用户对象
        
    Raises:
        HTTPException: 用户不活跃时
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    验证当前用户是否为超级管理员
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 当前超级管理员用户
        
    Raises:
        HTTPException: 用户不是超级管理员时
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user 