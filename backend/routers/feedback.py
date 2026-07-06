# ============================================
# 文件名: backend/routers/feedback.py
# 接口: POST /feedback
# 功能: 用户反馈提交
# ============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import (
    FeedbackRequest, FeedbackResponse, MessageResponse,
)
from backend.services import feedback_service

router = APIRouter(prefix="/feedback", tags=["反馈"])


@router.post("", response_model=MessageResponse, summary="提交反馈")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db),
):
    """
    ## 提交用户反馈

    对摘要质量进行评分和评价。

    ### 请求示例:
    ```json
    {
        "news_id": 1,
        "summary_id": 1,
        "rating": 4,
        "comment": "摘要比较准确，但漏掉了最后一段的关键信息"
    }
    ```
    """
    if request.news_id is None and request.summary_id is None:
        raise HTTPException(
            status_code=422,
            detail="至少需要提供 news_id 或 summary_id 之一",
        )

    feedback = feedback_service.add_feedback(
        db,
        rating=request.rating,
        comment=request.comment,
        news_id=request.news_id,
        summary_id=request.summary_id,
    )

    return MessageResponse(
        success=True,
        message=f"反馈提交成功, 评分: {request.rating}/5",
        data={
            "feedback_id": feedback.id,
            "rating": feedback.rating,
        },
    )


@router.get("/stats", summary="获取反馈统计")
async def get_feedback_stats(db: Session = Depends(get_db)):
    """
    ## 获取反馈统计

    返回总体评分数、平均评分和评分分布。

    ### 示例:
    - `GET /feedback/stats`
    """
    return feedback_service.get_feedback_stats(db)
