from sqlalchemy import Boolean, Column, String, BigInteger, DateTime
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from utils.orm import Base


class UserDB(Base):
    """ 用户表的数据库模型 """
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, unique=True,
                autoincrement=True, comment="用户ID")
    username = Column(String, unique=True, index=True, comment="用户名")
    nickname = Column(String, comment="用户昵称")
    # 因为是可以为空的，所以这里不能设置唯一索引
    email = Column(String, index=True, nullable=True, comment="邮箱")
    hashed_password = Column(String, comment="哈希密码")
    invite_code = Column(String, comment="邀请码")
    is_active = Column(Boolean, default=True, comment="是否激活")
    # 注意：created_at 在创建时设置为当前时间，之后不会更改。
    created_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc), comment="创建时间")
    # 注意：updated_at 在每次更新实体时都会设置为当前时间。
    updated_at = Column(DateTime,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
    # 添加一个“tags”属性, 来引用“TagDB”类
    tags = relationship("TagDB", back_populates="user",
                        cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname,
            "email": self.email,
            "invite_code": self.invite_code,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() + "Z",  # 这里加上了 "Z"，表示 UTC 时间，方便前端处理
            "updated_at": self.updated_at.isoformat() + "Z",  # 这里加上了 "Z"，表示 UTC 时间，方便前端处理
        }
