from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """JWT令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """JWT令牌数据模型"""
    user_id: Optional[int] = None
    email: Optional[str] = None 