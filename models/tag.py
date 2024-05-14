from pydantic import BaseModel
from typing import Optional


class TagCreate(BaseModel):
    """ 标签模型 """
    name: str
    pin: bool
    user_id: int


class Tag(TagCreate):
    """ 返回给用户的标签模型 """
    id: int


class TagUpdate(BaseModel):
    """ 更新标签模型 """
    id: int
    user_id: int
    name: Optional[str] = None
    pin: Optional[bool] = None
