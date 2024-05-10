from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    """ 用户基础模型 """
    username: str


class UserCreate(UserBase):
    """ 创建用户模型 """
    password: str
    email: str
    invite_code: str


class UserUpdate(UserBase):
    """ 更新用户模型，用于接收用户的更新传参 """
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserLogin(UserBase):
    """ 登录用户模型 """
    password: str


class UserReturn(UserBase):
    """ 返回给用户的数据模型 """
    id: int
    email: Optional[str]
    invite_code: str
    is_active: bool


class LoginReturn(UserReturn):
    """ 登录返回模型 """
    token: str
