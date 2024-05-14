from fastapi import HTTPException
from database.tag import TagDB
from sqlalchemy.orm import Session
from models.tag import TagCreate, Tag, TagUpdate
from utils.query_db import get_tag_by_id, get_tags_by_user_id, check_tag_name
from utils.custom_log import log

def create_tag(db: Session, tag: TagCreate) -> Tag:
    """ 创建标签 """
    can_use = check_tag_name(db, tag.name)
    if not can_use:
        log.error("标签名称已存在，返回 400 错误: %s", tag.name)
        raise HTTPException(status_code=400, detail="标签名称已存在")
    
    db_tag = TagDB(user_id=tag.user_id, name=tag.name, pin=tag.pin)
    db.add(db_tag)
    db.commit()
    # 刷新对象以获取自动生成的 ID
    db.refresh(db_tag)
    return db_tag


def del_tag(db: Session, tag_id: int, user_id: int) -> Tag:
    """ 删除标签 """
    db_tag = get_tag_by_id(db, tag_id, user_id)

    if db_tag is None:
        raise HTTPException(status_code=404, detail="对话标签不存在")

    db.delete(db_tag)

    # 提交事务以确保删除操作被数据库执行
    db.commit()
    # 注意：删除操作，不可以再使用 db_tag 对象刷新，因为它已经被删除了
    # 返回已删除的对象的最后状态
    return db_tag


def update_tag(db: Session, tag: TagUpdate):
    """ 更新标签名 """
    db_tag = get_tag_by_id(db, tag_id=tag.id, user_id=tag.user_id)

    if db_tag is None:
        raise HTTPException(status_code=404, detail="对话标签不存在")

    if tag.pin is not None:
        db_tag.pin = tag.pin
    if tag.name is not None:
        can_use = check_tag_name(db, tag.name)
        if not can_use:
            log.error("标签名称已存在，返回 400 错误: %s", tag.name)
            raise HTTPException(status_code=400, detail="标签名称已存在")
        db_tag.name = tag.name
    db.commit()
    db.refresh(db_tag)
    return db_tag


def get_tag(db: Session, tag_id: int, user_id: int):
    """ 从数据库获取标签 """
    return get_tag_by_id(db, tag_id, user_id)


def get_tags(db: Session, user_id: int):
    """ 从数据库获取标签列表 """
    return get_tags_by_user_id(db, user_id)
