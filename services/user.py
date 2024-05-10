from sqlalchemy.orm import Session
from fastapi import HTTPException

from utils.db import redis_client
from database.user import UserDB
from models.user import UserCreate, UserLogin, UserReturn, UserUpdate
from services.auth import pwd_context, verify_password, create_token
from utils.user import get_user_by_id, get_user_by_username


def create_user(db: Session, user: UserCreate):
    """ 创建用户 """
    # 判断用户的邀请码是否正确
    if redis_client.exists(user.invite_code):
        # 删除邀请码
        redis_client.delete(user.invite_code)
    else:
        # 返回 401 错误
        raise HTTPException(status_code=401, detail="无效的邀请码")

    hashed_password = pwd_context.hash(user.password)
    db_user = UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        invite_code=user.invite_code,
        is_active=True
    )
    # 添加到数据库会话
    db.add(db_user)
    # 提交事务
    db.commit()
    # 确保了返回的用户对象 db_user 包含了数据库中最新插入的用户数据
    db.refresh(db_user)
    # 返回最新的用户数据
    return get_return_user(db_user)


def get_user(db: Session, user_id: int):
    """ 获取用户 """
    # 获取用户
    target_user = get_user_by_id(db, user_id)

    # 如果用户不存在，则返回 404 错误
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 返回用户
    return get_return_user(target_user)


def delete_user(db: Session, user_id: int):
    """ 删除用户 """
    # 获取用户
    target_user = get_user_by_id(db, user_id)

    # 如果用户不存在，则返回 404 错误
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 删除用户
    db.delete(target_user)
    db.commit()
    # 返回删除成功
    return {"ok": "删除成功"}


def update_user(db: Session, user_id: int, user: UserUpdate):
    """ 更新用户 """
    # 获取用户
    target_user = get_user_by_id(db, user_id)

    # 如果用户不存在，则返回 404 错误
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新用户数据
    if user.password:
        target_user.hashed_password = pwd_context.hash(user.password)

    if user.username:
        target_user.username = user.username

    if user.email:
        target_user.email = user.email

    if user.is_active:
        target_user.is_active = user.is_active

    # 提交事务
    db.commit()
    # 确保了返回的用户对象 db_user 包含了数据库中最新插入的用户数据
    db.refresh(target_user)
    # 返回更新后的用户数据
    return get_return_user(target_user)


def user_login(db: Session, user: UserLogin):
    """ 用户登录 """
    # 获取用户
    target_user = get_user_by_username(db, user.username)

    # 如果用户不存在或密码错误，则返回 None
    if not target_user or not verify_password(user.password, target_user.hashed_password):
        return None

    token = create_token(str(target_user.id))

    # 返回用户
    return {
        **get_return_user(target_user).model_dump(),
        "token": token
    }


def get_return_user(user: UserDB):
    """ 获取返回给用户的数据 """
    return UserReturn(
        id=user.id,
        username=user.username,
        email=user.email,
        invite_code=user.invite_code,
        is_active=user.is_active
    )
