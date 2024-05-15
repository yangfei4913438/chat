from sqlalchemy import Column, Boolean, String, ForeignKey, BigInteger, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from utils.orm import Base


class TagDB(Base):
    """ 会话标签表的数据库模型 """
    __tablename__ = "tags"

    id = Column(BigInteger, primary_key=True, unique=True,
                autoincrement=True, comment="标签ID")
    name = Column(String, unique=True, index=True, comment="标签名")
    pin = Column(Boolean, comment="是否置顶")
    # 指定外键
    user_id = Column(BigInteger, ForeignKey('users.id'), comment="用户ID")
    # 注意：created_at 在创建时设置为当前时间，之后不会更改。
    created_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc), comment="创建时间")
    # 注意：updated_at 在每次更新实体时都会设置为当前时间。
    updated_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    # 添加一个“user”属性来引用“UserDB”类
    user = relationship("UserDB", back_populates="tags")
    # 添加一个“messages”属性来引用“MessageDB”类。back_populates 是指定 MessageDB 类中的 tag 属性
    messages = relationship(
        "MessageDB", back_populates="tag", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "pin": self.pin,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() + "Z",  # 这里加上了 "Z"，表示 UTC 时间，方便前端处理
            "updated_at": self.updated_at.isoformat() + "Z",  # 这里加上了 "Z"，表示 UTC 时间，方便前端处理
        }
