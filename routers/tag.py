from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.tag import TagCreate, TagUpdate
from services.guard import check_token
from services.tag import get_tags, del_tag, create_tag, update_tag, get_tag_by_id
from utils.db import get_db, redis_client, obj_list_from_redis, obj_list_into_redis, obj_get_from_redis, obj_set_into_redis
from utils.custom_log import log
from utils.query_db import check_tag_id

router = APIRouter()


@router.get('/tags')
def get_user_tags(user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 获取对话标签列表 """
    # 先查询内存有没有
    cache = obj_list_from_redis(f"tags:{user_id}")
    # 没有就去数据库查询
    if not cache:
        log.info('从数据库中获取数据')
        tags = get_tags(db, user_id)

        if tags:
            # 转换数据
            tags_dict = [tag.to_dict() for tag in tags]

            log.info("存入 Redis 中: %s", tags_dict)
            obj_list_into_redis(f"tags:{user_id}", tags_dict)

            # 返回数据给用户
            return tags_dict

        return []

    log.info("返回redis缓存数据给用户: %s", cache)
    # 查询到了，直接返回数据给用户
    return cache


@router.delete("/tag/{tag_id}")
def del_user_tag(tag_id: int, user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 删除对话标签 """
    check_exist = check_tag_id(db, tag_id)
    if check_exist:
        log.error("对话标签不存在，返回 404 错误")
        # 返回 404 错误，资源不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话标签不存在"
        )

    # 先删除内存中的数据。
    redis_client.delete(f"tags:{user_id}")
    redis_client.delete(f"tag:{tag_id}")

    # 再删除数据库中的数据
    return del_tag(db, tag_id, user_id)


@router.get("/tag/{tag_id}")
def get_user_tag(tag_id: int, user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 获取对话标签 """
    # 先看缓存有没有
    cache = obj_get_from_redis(f"tag:{tag_id}")
    if not cache:
        # 没有就去数据库查询
        data = get_tag_by_id(db, tag_id, user_id)

        if data:
            log.info('从数据库中获取数据: %s', data)
            # 转换数据
            tag_dict = data.to_dict()
            log.info("存入 Redis 中: %s", tag_dict)
            obj_set_into_redis(f"tag:{tag_id}", tag_dict)
            # 返回数据给用户
            return tag_dict

        return {}

    # 查询到了，直接返回数据给用户
    return cache


@router.post("/tag")
def add_user_tag(tag: TagCreate, user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 添加对话标签 """
    if str(tag.user_id) != str(user_id):
        log.error(f"用户id不匹配，返回 403 错误: {tag.user_id} != {user_id}")
        # 返回 403 错误, 禁止操作别人的数据
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有操作权限"
        )

    # 先删除内存中的列表数据。
    redis_client.delete(f"tags:{user_id}")

    # 再添加数据库中的数据
    return create_tag(db, tag)


@router.put("/tag")
def update_user_tag(tag: TagUpdate, user_id: int = Depends(check_token), db: Session = Depends(get_db)):
    """ 更新对话标签 """
    if str(tag.user_id) != str(user_id):
        log.error("用户id不匹配，返回 403 错误")
        # 返回 403 错误, 禁止操作别人的数据
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有操作权限"
        )

    # 先删除内存中的列表数据。
    redis_client.delete(f"tags:{user_id}")
    redis_client.delete(f"tag:{tag.id}")

    # 再更新数据库中的数据
    return update_tag(db, tag)
