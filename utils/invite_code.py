import uuid
from utils.db import redis_client


def generate_invitation_code(expire_days: int = 7):
    """ 生成一个邀请码，默认有效期是 7 天 """
    code = str(uuid.uuid4()).replace("-", "")
    # 将邀请码存储在 Redis 中，并设置过期时间
    redis_client.set(code, "active", ex=expire_days * 24 * 60 * 60)
    # 返回邀请码
    return code


def generate_invitation_codes(num: int = 10):
    """ 批量生成邀请码，默认一次生成 10 个 """
    invitation_codes = []
    for _ in range(num):
        # 生成邀请码, 并添加到列表中
        invitation_codes.append(generate_invitation_code())
    # 返回邀请码列表
    return invitation_codes
