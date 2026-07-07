# ============================================
# 文件名: backend/routers/favorite.py
# 接口: POST /favorite / DELETE /favorite / GET /favorite
# 功能: 收藏管理
# ============================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import (
    FavoriteRequest, FavoriteResponse, FavoriteListResponse,
    MessageResponse,
)
from backend.services import favorite_service

router = APIRouter(prefix="/favorite", tags=["收藏"])


@router.post("", response_model=MessageResponse, summary="添加收藏")
async def add_favorite(
    request: FavoriteRequest,
    db: Session = Depends(get_db),
):
    """
    ## 添加收藏

    ### 请求示例:
    ```json
    {
        "news_id": 1
    }
    ```
    """
    try:
        favorite = favorite_service.add_favorite(db, news_id=request.news_id)
        return MessageResponse(
            success=True,
            message=f"收藏成功: 新闻ID={request.news_id}",
            data={"favorite_id": favorite.id, "news_id": favorite.news_id},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("", response_model=MessageResponse, summary="取消收藏")
async def remove_favorite(
    news_id: int = Query(..., description="要取消收藏的新闻ID"),
    db: Session = Depends(get_db),
):
    """
    ## 取消收藏

    ### 示例:
    - `DELETE /favorite?news_id=1`
    """
    success = favorite_service.remove_favorite(db, news_id=news_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"收藏不存在: 新闻ID={news_id}",
        )
    return MessageResponse(
        success=True,
        message=f"已取消收藏: 新闻ID={news_id}",
    )


@router.get("", response_model=FavoriteListResponse, summary="获取收藏列表")
async def get_favorites(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    category: str = Query(None, description="分类筛选"),
    keyword: str = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
):
    """
    ## 获取收藏列表

    按收藏时间倒序排列，支持分类和关键词过滤。

    ### 示例:
    - `GET /favorite?page=1&page_size=20`
    - `GET /favorite?category=科技`
    - `GET /favorite?keyword=人工智能`
    """
    favorites, total = favorite_service.get_favorites(
        db, page=page, page_size=page_size,
        category=category, keyword=keyword,
    )

    items = []
    for fav in favorites:
        news = fav.news  # 通过 relationship 自动加载
        items.append(FavoriteResponse(
            id=fav.id,
            news_id=fav.news_id,
            category=news.category if news else None,
            content_preview=news.content[:200] if news and news.content else None,
            length=news.length if news else 0,
            created_at=fav.created_at,
        ))

    return FavoriteListResponse(total=total, items=items)
