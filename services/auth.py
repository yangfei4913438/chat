import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from argon2 import PasswordHasher
import jwt

from utils.db import get_db
from utils.query_db import get_user_by_id
from utils.custom_log import log

# 配置 JWT
# 秘钥
SECRET_KEY = os.getenv("SECRET_KEY")
# 算法
ALGORITHM = os.getenv("ALGORITHM")
# Token 过期时间， 7 天
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# 密码加密
pwd_context = PasswordHasher(memory_cost=204800, hash_len=32, salt_len=16)


def get_hash_password(password: str):
    """ 获取加密密码 """
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    """ 验证密码 """
    log.info('password: %s, hashed_password: %s', password, hashed_password)
    try:
        # 成功返回 True
        return pwd_context.verify(hashed_password, password)
    except Exception as exc:
        log.error("密码验证失败: %s", exc)
        return False


def create_token(user_id: str):
    """ 获取 token """
    # 生成 Token 过期时间
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"user_id": user_id}

    expire = datetime.now(tz=timezone.utc) + access_token_expires

    # 添加过期时间
    to_encode.update({"exp": expire})

    # 生成 Token 并返回
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    """ 验证 token """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        if user_id is None:
            log.error("用户 id 不存在")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的凭证"
            )

        # 查看用户是否还在数据库中
        # 如果用户不存在，或者用户被禁用了，则返回 401 错误
        db = next(get_db())
        user = get_user_by_id(db, user_id)
        if not user or not user.is_active:
            log.error("用户不存在或者被禁用了")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的凭证"
            )

        return int(user_id)

    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的凭证"
        ) from exc
