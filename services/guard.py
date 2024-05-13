from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from typing import Optional
import os


from services.auth import verify_token
from utils.custom_log import log


async def check_token(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
        # 获取特权角色。传递参数 Role
        Role: Optional[str] = Header(None),
        # 使用特权的情况下，需要自己提供 user_id。传递参数 UserId
        UserId: Optional[str] = Header(None),
):
    """ 校验权限 """
    # 判断角色是否是邀请码角色，拥有邀请码生成权限的角色，可以不用校验token
    if Role == os.getenv("INVITE_CODE_ROLE"):
        log.info("拥有邀请码生成权限，无需校验token，使用自带用户id: %s", UserId)
        if not UserId:
            log.error("特权用户，没有提供 user_id，返回 401 错误")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="这位大老爷，你还没有提供 user_id 啊！"
            )
        # 特权通过，返回用户id
        return str(UserId)

    log.info("没有特权，继续校验token。。。")
    # 其他情况，继续校验 token
    return verify_token(credentials.credentials)
