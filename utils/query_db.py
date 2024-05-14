from sqlalchemy.orm import Session
from database.user import UserDB
from database.tag import TagDB
from database.message import MessageDB
from utils.custom_log import log


def get_tag_by_id(db: Session, tag_id: int, user_id: int):
    """ 从数据库获取标签 """
    return db.query(TagDB).filter(TagDB.id == tag_id, TagDB.user_id == user_id).first()


def get_tags_by_user_id(db: Session, user_id: int):
    """ 从数据库获取标签列表 """
    return db.query(TagDB).filter(TagDB.user_id == user_id).all()


def check_tag_name(db: Session, new_tag_name: str):
    """ 判断标签名称是否可用 """
    # 查询所有同名标签
    existing_tags = db.query(TagDB).filter(TagDB.name == new_tag_name).all()
    # 如果没有同名标签，返回 True
    return not existing_tags


def check_tag_id(db: Session, tag_id: int):
    """ 判断标签是否存在 """
    # 查询所有同名标签
    existing_tags = db.query(TagDB).filter(TagDB.id == tag_id).all()
    # 如果没有同名标签，返回 True
    return not existing_tags


def check_message_id(db: Session, message_id: int):
    """ 判断消息是否存在 """
    # 查询所有同名消息
    existing_messages = db.query(MessageDB).filter(
        MessageDB.id == message_id).all()
    # 如果没有同名消息，返回 True
    return not existing_messages


def check_user_name(db: Session, new_user_name: str):
    """ 判断用户名是否可用 """
    # 查询所有同名用户
    existing_users = db.query(UserDB).filter(
        UserDB.username == new_user_name).all()
    # 如果没有同名用户，返回 True
    return not existing_users


def get_messages_by_user_id(db: Session, user_id: int):
    """ 从数据库获取消息列表 """
    return db.query(MessageDB).join(TagDB, MessageDB.tag_id == TagDB.id).filter(TagDB.user_id == user_id).all()


def get_messages_by_tag_id(db: Session, tag_id: int):
    """ 从数据库获取消息列表 """
    return db.query(MessageDB).filter(MessageDB.tag_id == tag_id).all()


def get_message_by_id(db: Session, message_id: int):
    """ 从数据库获取消息 """
    return db.query(MessageDB).filter(MessageDB.id == message_id).first()


def get_user_by_id(db: Session, user_id: int):
    """ 从数据库获取用户 """
    return db.query(UserDB).filter(UserDB.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    """ 从数据库获取用户 """
    return db.query(UserDB).filter(UserDB.username == username).first()
