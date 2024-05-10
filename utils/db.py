import os
import redis
from sqlalchemy import create_engine, orm

from database.user import Base


# 创建数据库模型
engine = create_engine(os.getenv("POSTGRES_URL"))
# 创建数据库会话, 不自动提交，不自动刷新，绑定到 engine
SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 配置 Redis 连接
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    db=os.getenv("REDIS_DB"),
    password=os.getenv("REDIS_PASSWORD")
)


def init_db():
    """ 初始化数据库 """

    # 这个命令会检查所有 Base 的子类，并为每个子类在数据库中创建一个表（如果表不存在的话）。
    # 如果表已经存在，它不会重新创建或修改表结构。
    Base.metadata.create_all(bind=engine)


def get_db():
    """ 获取数据库连接，每次请求时它都会创建一个新的 Session。当请求处理完成后，它会自动关闭这个 Session。 """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
