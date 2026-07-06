# ============================================
# 文件名: backend/services/feedback_service.py
# 功能: 用户反馈业务逻辑
# ============================================

from typing import Optional
from sqlalchemy.orm import Session

from backend.models.models import Feedback


def add_feedback(
    db: Session,
    rating: int,
    comment: Optional[str] = "",
    news_id: Optional[int] = None,
    summary_id: Optional[int] = None,
) -> Feedback:
    """
    添加用户反馈
    参数:
        db: 数据库会话
        rating: 评分 (1-5)
        comment: 反馈文字
        news_id: 关联新闻ID（可选）
        summary_id: 关联摘要ID（可选）
    返回:
        Feedback 对象
    """
    feedback = Feedback(
        news_id=news_id,
        summary_id=summary_id,
        rating=rating,
        comment=comment or "",
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_stats(db: Session) -> dict:
    """
    获取反馈统计
    返回:
        {
            "total": 总数,
            "avg_rating": 平均评分,
            "rating_distribution": {1: 数量, 2: 数量, ...}
        }
    """
    from sqlalchemy import func

    total = db.query(Feedback).count()
    if total == 0:
        return {"total": 0, "avg_rating": 0, "rating_distribution": {}}

    avg = db.query(func.avg(Feedback.rating)).scalar() or 0

    dist = {}
    for r in range(1, 6):
        dist[r] = db.query(Feedback).filter(Feedback.rating == r).count()

    return {
        "total": total,
        "avg_rating": round(float(avg), 2),
        "rating_distribution": dist,
    }
