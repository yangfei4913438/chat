import os
import redis
import json
from sqlalchemy import create_engine, orm
from utils.custom_log import log
from utils.orm import Base
from database import *


# 创建数据库模型
engine = create_engine(
    url=os.getenv("POSTGRES_URL"),
    pool_size=20,
    max_overflow=50
)
# 创建数据库会话, 不自动提交，不自动刷新，绑定到 engine
SessionLocal = orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 配置 Redis 连接
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    db=os.getenv("REDIS_DB"),
    password=os.getenv("REDIS_PASSWORD")
)
# 注意： 由于项目时间关系，我就不精细化处理内存数据了，有任何改动，对应 key 的数据会全部清理掉。
# 比如列表的数据变动，我会把整个列表从 redis 清空。不会精细的修改内存数据。


def obj_list_into_redis(list_name: str, list_data: list):
    """ 将列表数据存入 Redis，兼容普通类型的数据 """
    # 先清理旧数据
    redis_client.delete(list_name)
    # 序列化数据
    data = [json.dumps(i) for i in list_data]
    # 存入 Redis
    redis_client.rpush(list_name, *data)


def obj_list_from_redis(list_name: str):
    """ 从 Redis 中获取列表数据 """
    # 获取数据
    data = redis_client.lrange(list_name, 0, -1)
    if not data:
        log.info("Redis 中没有数据: %s", list_name)
        return None
    # 反序列化数据
    return [json.loads(i) for i in data]


def obj_set_into_redis(key: str, value: any):
    """ 将数据存入 Redis """
    # 存入 Redis
    redis_client.set(key, json.dumps(value))


def obj_get_from_redis(key: str):
    """ 从 Redis 中获取数据 """
    # 获取数据
    data = redis_client.get(key)
    if not data:
        log.error("Redis 中没有数据: %s", key)
        return None
    return json.loads(data)


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
