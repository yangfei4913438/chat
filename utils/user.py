from database.user import UserDB
from sqlalchemy.orm import Session


def get_user_by_id(db: Session, user_id: int):
    """ 从数据库获取用户 """
    return db.query(UserDB).filter(UserDB.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    """ 从数据库获取用户 """
    return db.query(UserDB).filter(UserDB.username == username).first()
