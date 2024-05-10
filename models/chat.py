from pydantic import BaseModel


class ChatBody(BaseModel):
    """ 对话请求体 """
    # 对话内容
    query: str
