# ============================================
# 文件名: backend/services/favorite_service.py
# 功能: 收藏业务逻辑
# ============================================

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.models.models import News, Favorite


def add_favorite(db: Session, news_id: int) -> Favorite:
    """
    添加收藏
    参数:
        db: 数据库会话
        news_id: 新闻ID
    返回:
        Favorite 对象
    异常:
        ValueError: 新闻不存在
        IntegrityError: 重复收藏
    """
    # 验证新闻存在
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise ValueError(f"新闻不存在: ID={news_id}")

    # 检查是否已收藏
    existing = db.query(Favorite).filter(
        Favorite.news_id == news_id
    ).first()
    if existing:
        raise ValueError(f"该新闻已收藏: ID={news_id}")

    # 添加收藏
    favorite = Favorite(news_id=news_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, news_id: int) -> bool:
    """
    取消收藏
    参数:
        db: 数据库会话
        news_id: 新闻ID
    返回:
        True 表示删除成功, False 表示收藏不存在
    """
    favorite = db.query(Favorite).filter(
        Favorite.news_id == news_id
    ).first()

    if not favorite:
        return False

    db.delete(favorite)
    db.commit()
    return True


def get_favorites(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
) -> tuple:
    """
    获取收藏列表（分页）
    支持按分类和关键词过滤。
    返回:
        (收藏列表, 总数)
    """
    query = db.query(Favorite).join(News, Favorite.news_id == News.id)

    if category:
        query = query.filter(News.category == category)
    if keyword:
        query = query.filter(News.content.contains(keyword))

    query = query.order_by(Favorite.created_at.desc())

    total = query.count()
    offset = (page - 1) * page_size
    favorites = query.offset(offset).limit(page_size).all()

    return favorites, total


def is_favorited(db: Session, news_id: int) -> bool:
    """检查新闻是否已收藏"""
    return db.query(Favorite).filter(
        Favorite.news_id == news_id
    ).first() is not None
