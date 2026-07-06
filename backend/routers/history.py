# ============================================
# 文件名: backend/routers/history.py
# 接口: GET /history
# 功能: 操作历史查询
# ============================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import HistoryItem, HistoryListResponse
from backend.services import history_service

router = APIRouter(prefix="/history", tags=["历史"])


@router.get("", response_model=HistoryListResponse, summary="获取操作历史")
async def get_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    action: str = Query(None, description="操作类型筛选: read / summarize"),
    db: Session = Depends(get_db),
):
    """
    ## 获取操作历史记录

    支持按操作类型筛选。

    ### 示例:
    - `GET /history?page=1&page_size=20` — 全部历史
    - `GET /history?action=summarize` — 只看摘要生成记录
    - `GET /history?action=read` — 只看阅读记录
    """
    records, total = history_service.get_history(
        db, page=page, page_size=page_size, action=action,
    )

    items = []
    for record in records:
        news = record.news  # 通过 relationship 加载
        items.append(HistoryItem(
            id=record.id,
            news_id=record.news_id,
            action=record.action,
            category=news.category if news else None,
            content_preview=news.content[:200] if news and news.content else None,
            created_at=record.created_at,
        ))

    return HistoryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )
