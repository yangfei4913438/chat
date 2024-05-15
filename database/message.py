from sqlalchemy import Column, String, ForeignKey, BigInteger, SmallInteger, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from utils.orm import Base


class MessageDB(Base):
    """ 消息表的数据库模型 """
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, unique=True,
                autoincrement=True, comment="消息ID")
    type = Column(String, comment="消息类型")
    content = Column(String, comment="消息内容")
    sender_type = Column(SmallInteger, comment="发送者类型, 0 为系统消息, 1 为用户消息")
    # 指定外键
    tag_id = Column(BigInteger, ForeignKey('tags.id'), comment="用户ID")
    # 注意：created_at 在创建时设置为当前时间，之后不会更改。
    created_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc), comment="创建时间")
    # 注意：updated_at 在每次更新实体时都会设置为当前时间。
    updated_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    # 添加一个“tag”属性来引用“TagDB”类
    tag = relationship("TagDB", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "sender_type": self.sender_type,
            "tag_id": self.tag_id,
            "created_at": self.created_at.isoformat() + "Z",  # 这里加上了 "Z"，表示 UTC 时间，方便前端处理
            "updated_at": self.updated_at.isoformat() + "Z",  # 这里加上了 "Z"，表示 UTC 时间，方便前端处理
        }
