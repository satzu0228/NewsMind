# ============================================
# 文件名: backend/services/news_service.py
# 功能: 新闻业务逻辑（查询/详情/搜索）
# ============================================

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.models.models import News, Favorite


def _has_fts_table(db: Session) -> bool:
    return db.execute(text(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'news_fts'"
    )).first() is not None


def _search_with_fts(
    db: Session,
    keyword: str,
    page: int,
    page_size: int,
    category: Optional[str] = None,
) -> Optional[tuple[List[News], int]]:
    if not keyword or not _has_fts_table(db):
        return None

    offset = (page - 1) * page_size
    where_sql = "news_fts.content MATCH :keyword"
    params = {"keyword": keyword, "limit": page_size + 1, "offset": offset}
    if category:
        where_sql += " AND n.category = :category"
        params["category"] = category

    try:
        total = None
        if not category:
            total = db.execute(text(f"""
                SELECT COUNT(*)
                FROM news n
                JOIN news_fts ON news_fts.rowid = n.id
                WHERE {where_sql}
            """), params).scalar_one()

        ids = db.execute(text(f"""
            SELECT n.id
            FROM news n
            JOIN news_fts ON news_fts.rowid = n.id
            WHERE {where_sql}
            ORDER BY bm25(news_fts), n.id DESC
            LIMIT :limit OFFSET :offset
        """), params).scalars().all()
    except Exception:
        return None

    has_more = len(ids) > page_size
    ids = ids[:page_size]
    if total is None:
        total = offset + len(ids) + (1 if has_more else 0)

    if not ids:
        return [], total

    rows = db.query(News).filter(News.id.in_(ids)).all()
    by_id = {item.id: item for item in rows}
    return [by_id[item_id] for item_id in ids if item_id in by_id], total


def _search_short_keyword(
    db: Session,
    keyword: str,
    page: int,
    page_size: int,
    category: Optional[str] = None,
) -> tuple[List[News], int]:
    query = db.query(News)
    if category:
        query = query.filter(News.category == category)
    query = query.filter(News.content.contains(keyword))

    offset = (page - 1) * page_size
    rows = (
        query.order_by(News.id.desc())
        .offset(offset)
        .limit(page_size + 1)
        .all()
    )
    has_more = len(rows) > page_size
    news_list = rows[:page_size]
    total = offset + len(news_list) + (1 if has_more else 0)
    return news_list, total


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
    if keyword:
        stripped_keyword = keyword.strip()
        if len(stripped_keyword) < 3:
            return _search_short_keyword(db, stripped_keyword, page, page_size, category)
        fts_result = _search_with_fts(db, stripped_keyword, page, page_size, category)
        if fts_result is not None:
            return fts_result
        return _search_short_keyword(db, stripped_keyword, page, page_size, category)

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
    stripped_keyword = keyword.strip()
    if len(stripped_keyword) < 3:
        return _search_short_keyword(db, stripped_keyword, 1, limit)[0]

    fts_result = _search_with_fts(db, stripped_keyword, 1, limit)
    if fts_result is not None:
        return fts_result[0]

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
