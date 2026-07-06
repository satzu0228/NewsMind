# ============================================
# 文件名: backend/services/summary_service.py
# 功能: 摘要生成业务逻辑
# ============================================

from typing import Optional
from sqlalchemy.orm import Session

from backend.models.models import News, Summary
from backend.schemas.schemas import SummaryResponse
from backend.services.news_service import get_or_create_news


# 全局摘要引擎（延迟加载，避免启动时加载大模型）
_summarizer = None


def get_summarizer():
    """获取或初始化摘要引擎（单例）"""
    global _summarizer
    if _summarizer is None:
        from backend.ai.summarizer import NewsSummarizer
        print("[*] 正在加载 BERT + T5 摘要模型（首次启动较慢，约30-60秒）...")
        _summarizer = NewsSummarizer()
        print("[✓] 摘要引擎就绪")
    return _summarizer


def generate_summary(
    db: Session,
    text: str,
    news_id: Optional[int] = None,
    top_k: int = 5,
) -> SummaryResponse:
    """
    生成新闻摘要
    参数:
        db: 数据库会话
        text: 新闻文本
        news_id: 已有新闻ID（可选，为None则自动创建）
        top_k: TextRank 关键句数量
    返回:
        SummaryResponse
    """
    # 1. 获取或创建新闻记录
    if news_id:
        news = db.query(News).filter(News.id == news_id).first()
        if not news:
            raise ValueError(f"新闻不存在: ID={news_id}")
        text = news.content
    else:
        # 自动存入新闻
        news = get_or_create_news(db, text)

    # 2. 调用摘要引擎
    summarizer = get_summarizer()
    result = summarizer.summarize(text, top_k=top_k, use_t5=True)

    # 3. 可选：计算 ROUGE-L（如果有参考摘要）
    rouge_l = None
    # 此处可用已有的TextRank结果作为参考
    # 但更好的方式是后续实现

    # 4. 保存摘要记录
    summary = Summary(
        news_id=news.id,
        extractive_summary=result["extractive_summary"],
        abstractive_summary=result["abstractive_summary"],
        inference_time=result["inference_time"],
        rouge_l=rouge_l,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)

    # 5. 返回
    return SummaryResponse(
        news_id=news.id,
        summary_id=summary.id,
        extractive_summary=summary.extractive_summary,
        abstractive_summary=summary.abstractive_summary,
        inference_time=summary.inference_time,
        rouge_l=summary.rouge_l,
        created_at=summary.created_at,
    )


def get_summary_by_news(db: Session, news_id: int) -> Optional[Summary]:
    """获取某新闻的最新摘要"""
    return db.query(Summary).filter(
        Summary.news_id == news_id
    ).order_by(Summary.id.desc()).first()
