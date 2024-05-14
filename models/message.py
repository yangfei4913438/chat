from pydantic import BaseModel


class MessageCreate(BaseModel):
    """ 创建消息模型 """
    tag_id: int
    type: str
    content: str
    sender_type: int
    created_at: int


class Message(MessageCreate):
    """ 返回给用户的消息模型 """
    id: int
