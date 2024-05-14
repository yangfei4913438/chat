from sqlalchemy import Column, String, ForeignKey, BigInteger, SmallInteger
from sqlalchemy.orm import relationship
from utils.orm import Base


class MessageDB(Base):
    """ 消息表的数据库模型 """
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, unique=True,
                autoincrement=True, comment="消息ID")
    type = Column(String, comment="消息类型")
    content = Column(String, comment="消息内容")
    created_at = Column(String, comment="创建时间")
    sender_type = Column(SmallInteger, comment="发送者类型, 0 为系统消息, 1 为用户消息")
    # 指定外键
    tag_id = Column(BigInteger, ForeignKey('tags.id'), comment="用户ID")
    # 添加一个“tag”属性来引用“TagDB”类
    tag = relationship("TagDB", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "created_at": self.created_at,
            "sender_type": self.sender_type,
            "tag_id": self.tag_id
        }
