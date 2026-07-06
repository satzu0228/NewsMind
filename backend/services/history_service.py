# ============================================
# 文件名: backend/services/history_service.py
# 功能: 操作历史业务逻辑
# ============================================

from typing import List
from sqlalchemy.orm import Session

from backend.models.models import History


def add_history(
    db: Session,
    news_id: int,
    action: str = "read",
) -> History:
    """
    添加操作历史
    参数:
        db: 数据库会话
        news_id: 新闻ID
        action: 操作类型 (read / summarize)
    返回:
        History 对象
    """
    history = History(
        news_id=news_id,
        action=action,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_history(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    action: str = None,
) -> tuple:
    """
    获取操作历史（分页 + 类型筛选）
    参数:
        db: 数据库会话
        page: 页码
        page_size: 每页条数
        action: 操作类型筛选（可选: read / summarize）
    返回:
        (历史列表, 总数)
    """
    query = db.query(History)

    if action:
        query = query.filter(History.action == action)

    query = query.order_by(History.created_at.desc())

    total = query.count()
    offset = (page - 1) * page_size
    history_list = query.offset(offset).limit(page_size).all()

    return history_list, total


def get_recent_history(db: Session, limit: int = 10) -> List[History]:
    """获取最近记录"""
    return db.query(History).order_by(
        History.created_at.desc()
    ).limit(limit).all()
