# ============================================
# 文件名: backend/services/news_service.py
# 功能: 新闻业务逻辑（查询/详情/搜索）
# ============================================

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models.models import News, Favorite


def get_news_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
) -> tuple[List[News], int]:
    """
    获取新闻列表（分页 + 分类筛选 + 关键词搜索）
    参数:
        db: 数据库会话
        page: 页码（从1开始）
        page_size: 每页条数
        category: 分类筛选（可选）
        keyword: 正文关键词搜索（可选）
    返回:
        (新闻列表, 总数)
    """
    query = db.query(News)

    # 按分类筛选
    if category:
        query = query.filter(News.category == category)

    # 按关键词搜索（正文模糊匹配）
    if keyword:
        query = query.filter(News.content.contains(keyword))

    # 总数
    total = query.count()

    # 分页 + 按时间倒序
    offset = (page - 1) * page_size
    news_list = query.order_by(News.id.desc()).offset(offset).limit(page_size).all()

    return news_list, total


def get_news_detail(db: Session, news_id: int) -> Optional[News]:
    """获取单条新闻详情"""
    return db.query(News).filter(News.id == news_id).first()


def get_categories(db: Session) -> List[str]:
    """获取所有新闻类别"""
    results = db.query(News.category).distinct().all()
    return sorted([r[0] for r in results if r[0]])


def check_is_favorite(db: Session, news_id: int) -> bool:
    """检查新闻是否已收藏"""
    return db.query(Favorite).filter(Favorite.news_id == news_id).first() is not None


def has_summary(db: Session, news_id: int) -> bool:
    """检查新闻是否已有摘要"""
    from backend.models.models import Summary
    return db.query(Summary).filter(Summary.news_id == news_id).first() is not None


def search_news(db: Session, keyword: str, limit: int = 20) -> List[News]:
    """搜索新闻（标题/正文匹配）"""
    return db.query(News).filter(
        News.content.contains(keyword)
    ).limit(limit).all()


def get_or_create_news(db: Session, content: str, category: str = "未知") -> News:
    """
    根据文本查找已有新闻，不存在则创建
    用于摘要生成时自动存入新闻
    """
    # 用内容前100字查找是否已存在
    preview = content[:100]
    existing = db.query(News).filter(
        News.content.startswith(preview)
    ).first()

    if existing:
        return existing

    # 创建新记录
    news = News(
        category=category,
        content=content,
        length=len(content),
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    return news
