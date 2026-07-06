# ============================================
# 文件名: backend/routers/news.py
# 接口: GET /news / GET /news/{id}
# 功能: 新闻列表查询、详情获取
# ============================================

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import (
    NewsItem, NewsDetail, NewsListResponse,
)
from backend.services import news_service, history_service

router = APIRouter(prefix="/news", tags=["新闻"])


@router.get("", response_model=NewsListResponse, summary="获取新闻列表")
async def get_news_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    category: str = Query(None, description="分类筛选（科技/体育/财经...）"),
    keyword: str = Query(None, description="正文关键词搜索"),
    db: Session = Depends(get_db),
):
    """
    ## 获取新闻列表

    支持分页、分类筛选、关键词搜索。

    ### 示例请求:
    - `GET /news?page=1&page_size=20` — 第1页，每页20条
    - `GET /news?category=科技` — 只看科技类新闻
    - `GET /news?keyword=人工智能` — 搜索含"人工智能"的新闻
    """
    news_list, total = news_service.get_news_list(
        db, page=page, page_size=page_size,
        category=category, keyword=keyword,
    )

    items = []
    for news in news_list:
        items.append(NewsItem(
            id=news.id,
            category=news.category,
            content_preview=news.content[:200] if news.content else "",
            length=news.length,
            created_at=news.created_at,
        ))

    return NewsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


@router.get("/{news_id}", response_model=NewsDetail, summary="获取新闻详情")
async def get_news_detail(
    news_id: int,
    db: Session = Depends(get_db),
):
    """
    ## 获取新闻详情

    返回完整正文及摘要/收藏状态。

    ### 示例:
    - `GET /news/1`
    """
    news = news_service.get_news_detail(db, news_id)
    if not news:
        raise HTTPException(status_code=404, detail=f"新闻不存在: ID={news_id}")

    # 记录阅读历史
    history_service.add_history(db, news_id=news_id, action="read")

    return NewsDetail(
        id=news.id,
        category=news.category,
        content=news.content,
        length=news.length,
        token_length=news.token_length or 0,
        has_summary=news_service.has_summary(db, news_id),
        is_favorite=news_service.check_is_favorite(db, news_id),
        created_at=news.created_at,
    )


@router.get("/categories/all", summary="获取所有新闻类别")
async def get_categories(db: Session = Depends(get_db)):
    """
    ## 获取所有新闻类别

    ### 示例:
    - `GET /news/categories/all`
    """
    categories = news_service.get_categories(db)
    return {"categories": categories, "count": len(categories)}
