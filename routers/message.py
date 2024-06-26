from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from services.guard import check_token
from utils.query_db import get_messages_by_tag_id, check_message_id, check_tag_id
from utils.db import get_db, redis_client, obj_list_from_redis, obj_list_into_redis
from services.message import delMessage, createMessage, updateMessage
from models.message import MessageCreate, MessageUpdate
from utils.custom_log import log

router = APIRouter()


@router.get('/messages/{tag_id}', dependencies=[Depends(check_token)])
def get_messages(tag_id: int, db: Session = Depends(get_db)):
    """ 获取消息列表 """
    # 先查询内存有没有
    cache = obj_list_from_redis(f"messages:{tag_id}")

    if not cache:
        # 没有就去数据库查询
        messages = get_messages_by_tag_id(db, tag_id)

        if messages:
            # 转换数据, 存入内存需要把数据转换一下
            data = [message.to_dict() for message in messages]
            # 存入内存
            obj_list_into_redis(f"messages:{tag_id}", data)
            # 返回数据给用户
            return data

        # 返回数据给用户
        return []

    # 查询到了，直接返回数据给用户
    return cache


@router.delete('/message/{tag_id}/{message_id}', dependencies=[Depends(check_token)])
def del_message(tag_id: int, message_id: int, db: Session = Depends(get_db)):
    """ 删除消息 """
    log.info("删除消息: %d, 数据类型 %s", message_id, type(message_id))
    check_exist = check_message_id(db, message_id)
    if check_exist:
        # 返回 404 错误，资源不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    # 先删除内存中的数据。
    redis_client.delete(f"messages:{tag_id}")

    # 再删除数据库中的数据
    return delMessage(db, message_id)


@router.post('/message', dependencies=[Depends(check_token)])
def add_message(message: MessageCreate, db: Session = Depends(get_db)):
    """ 添加消息 """
    is_null = check_tag_id(db, message.tag_id)
    if is_null:
        log.error("会话不存在，返回 404 错误")
        # 返回 404 错误，资源不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在, 请先创建会话"
        )

    # 先删除内存中的数据。
    redis_client.delete(f"messages:{message.tag_id}")

    # 再创建用户
    return createMessage(db, message)


@router.put('/message', dependencies=[Depends(check_token)])
def update_message(message: MessageUpdate, db: Session = Depends(get_db)):
    """ 更新消息 """
    check_exist = check_message_id(db, message.id)
    if check_exist:
        # 返回 404 错误，资源不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )

    # 先删除内存中的数据。
    redis_client.delete(f"messages:{message.tag_id}")

    # 再更新用户
    return updateMessage(db, message)
