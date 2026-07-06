# ============================================
# 文件名: backend/models/models.py
# 功能: SQLAlchemy ORM 数据库模型
# 表:
#   news      - 新闻文章
#   summaries - 生成摘要记录
#   favorites - 用户收藏
#   history   - 阅读/摘要历史
#   feedback  - 用户反馈
# ============================================

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float,
    DateTime, ForeignKey, Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class News(Base):
    """
    新闻文章表
    存储预处理后的新闻数据
    """
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    category = Column(String(20), index=True, nullable=False, comment="新闻类别（科技/体育/...）")
    content = Column(Text, nullable=False, comment="新闻正文（清洗后）")
    tokenized = Column(Text, nullable=True, comment="分词后文本")
    length = Column(Integer, default=0, comment="原文长度（字符）")
    token_length = Column(Integer, default=0, comment="分词后词数")
    created_at = Column(DateTime, default=datetime.now, comment="入库时间")

    # 关联关系
    summaries = relationship("Summary", back_populates="news", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="news", cascade="all, delete-orphan")
    history_records = relationship("History", back_populates="news", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<News(id={self.id}, category='{self.category}')>"


class Summary(Base):
    """
    摘要记录表
    存储每次生成的摘要结果
    """
    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="摘要ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"),
                     index=True, nullable=False, comment="关联新闻ID")
    extractive_summary = Column(Text, nullable=True, comment="抽取式摘要（TextRank）")
    abstractive_summary = Column(Text, nullable=True, comment="生成式摘要（T5）")
    inference_time = Column(Float, default=0.0, comment="推理耗时（秒）")
    rouge_l = Column(Float, nullable=True, comment="ROUGE-L 评估分数")
    created_at = Column(DateTime, default=datetime.now, comment="生成时间")

    # 关联
    news = relationship("News", back_populates="summaries")
    feedback = relationship("Feedback", back_populates="summary", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Summary(id={self.id}, news_id={self.news_id})>"


class Favorite(Base):
    """
    用户收藏表
    """
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="收藏ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"),
                     index=True, nullable=False, comment="关联新闻ID")
    created_at = Column(DateTime, default=datetime.now, comment="收藏时间")

    # 关联
    news = relationship("News", back_populates="favorites")

    def __repr__(self):
        return f"<Favorite(id={self.id}, news_id={self.news_id})>"


class History(Base):
    """
    用户操作历史表
    """
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="历史ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="CASCADE"),
                     index=True, nullable=False, comment="关联新闻ID")
    action = Column(String(20), nullable=False, default="read",
                    comment="操作类型: read(阅读) / summarize(生成摘要)")
    created_at = Column(DateTime, default=datetime.now, comment="操作时间")

    # 关联
    news = relationship("News", back_populates="history_records")

    def __repr__(self):
        return f"<History(id={self.id}, action='{self.action}')>"


class Feedback(Base):
    """
    用户反馈表
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="反馈ID")
    news_id = Column(Integer, ForeignKey("news.id", ondelete="SET NULL"),
                     nullable=True, comment="关联新闻ID（可选）")
    summary_id = Column(Integer, ForeignKey("summaries.id", ondelete="SET NULL"),
                        nullable=True, comment="关联摘要ID（可选）")
    rating = Column(Integer, default=0, comment="评分 1-5")
    comment = Column(Text, nullable=True, comment="反馈文字")
    created_at = Column(DateTime, default=datetime.now, comment="反馈时间")

    # 关联
    news = relationship("News")
    summary = relationship("Summary", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating})>"
