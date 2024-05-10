from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


# 创建数据库模型
Base = declarative_base()


class UserDB(Base):
    """ 用户表的数据库模型 """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String, unique=True, index=True, comment="用户名")
    email = Column(String, unique=True, index=True,
                   nullable=True, comment="邮箱")
    hashed_password = Column(String, comment="哈希密码")
    invite_code = Column(String, comment="邀请码")
    is_active = Column(Boolean, default=True, comment="是否激活")
