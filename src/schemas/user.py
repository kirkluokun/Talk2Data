from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """用户基本信息"""
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False


class UserCreate(UserBase):
    """创建用户时的信息"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """更新用户信息"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserInDBBase(UserBase):
    """存储在数据库中的用户信息"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserInDBBase):
    """包含哈希密码的用户数据模型"""
    hashed_password: str


class User(UserInDBBase):
    """API返回的用户数据模型，不包含敏感信息"""
    pass 