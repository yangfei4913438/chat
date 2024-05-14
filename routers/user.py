import os
from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from models.user import UserLogin, UserCreate, UserReturn, LoginReturn, UserUpdate
from services.guard import check_token
from services.user import create_user, user_login, delete_user, get_user, update_user
from utils.db import get_db
from utils.invite_code import generate_invitation_code


router = APIRouter()


@router.get("/invite_code")
def invite_code(role: str):
    """ 获取邀请码 """
    if role == os.getenv("INVITE_CODE_ROLE"):
        return {"invite_code": generate_invitation_code()}
    else:
        # 禁止访问 403
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有操作权限"
        )


@router.post("/register", response_model=UserReturn)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """ 用户注册 """
    return create_user(db, user)


@router.post("/login", response_model=LoginReturn)
def login(user: UserLogin, db: Session = Depends(get_db)):
    """ 用户登录 """
    info = user_login(db, user)
    if not info:
        # 返回 403 错误，没有权限，禁止访问
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的账号或密码",
        )
    # 返回登录信息
    return info


@router.delete("/user/delete")
def del_user(user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 删除用户，自我删除，也就是销户 """
    return delete_user(db, user_id)


@router.get("/user/info")
def get_user_info(user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 获取用户信息 """
    return get_user(db, user_id)


@router.put("/user/update")
def update_user_info(user: UserUpdate, user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 更新用户信息 """
    return update_user(db, user_id, user)
