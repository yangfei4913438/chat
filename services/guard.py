from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


from services.auth import verify_token


async def check_token(
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """ 校验 token"""
    return verify_token(credentials.credentials)
