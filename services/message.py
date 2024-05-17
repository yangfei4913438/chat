from sqlalchemy.orm import Session
from utils.query_db import get_message_by_id, get_messages_by_tag_id
from models.message import MessageCreate, Message, MessageUpdate
from database.message import MessageDB
from fastapi import HTTPException
from typing import List


def createMessage(db: Session, message: MessageCreate):
    """ 创建消息 """
    message_db = MessageDB(
        type=message.type,
        content=message.content,
        sender_type=message.sender_type,
        tag_id=message.tag_id)
    db.add(message_db)
    db.commit()
    db.refresh(message_db)
    return message_db.to_dict()


def delMessage(db: Session, message_id: int):
    """ 删除消息 """
    message_db = get_message_by_id(db, message_id)

    if message_db is None:
        raise HTTPException(status_code=404, detail="消息不存在")

    db.delete(message_db)
    db.commit()
    return message_db.to_dict()


def updateMessage(db: Session, message: MessageUpdate):
    """ 更新消息 """
    message_db = get_message_by_id(db, message.id)

    if message_db is None:
        raise HTTPException(status_code=404, detail="消息不存在")

    if not message.content:
        raise HTTPException(status_code=400, detail="消息内容不能为空")
    else:
        message_db.content = message.content

    db.commit()
    db.refresh(message_db)
    return message_db.to_dict()


def get_message(db: Session, message_id: int) -> Message:
    """ 从数据库获取消息 """
    return get_message_by_id(db, message_id)


def get_messages(db: Session, tag_id: int) -> List[Message]:
    """ 从数据库获取消息列表 """
    return get_messages_by_tag_id(db, tag_id)
