# ============================================
# 文件名: backend/schemas/schemas.py
# 功能: Pydantic 请求/响应数据模型（FastAPI 参数校验和序列化）
# ============================================

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============================================
# 用户认证相关
# ============================================

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=4, max_length=50, description="密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class AuthResponse(BaseModel):
    """登录/注册响应"""
    success: bool = True
    message: str = "操作成功"
    token: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    avatar: Optional[str] = None


class UserProfile(BaseModel):
    """用户资料"""
    id: int
    username: str
    avatar: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """更新用户资料请求"""
    username: Optional[str] = Field(default=None, min_length=1, max_length=50, description="新用户名")
    avatar: Optional[str] = Field(default=None, max_length=10, description="新头像 emoji")


# ============================================
# News 相关
# ============================================

class NewsItem(BaseModel):
    """新闻列表项（简要）"""
    id: int
    category: str
    content_preview: str = Field(default="", description="正文前200字预览")
    length: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsDetail(BaseModel):
    """新闻详情（完整正文）"""
    id: int
    category: str
    content: str
    length: int = 0
    token_length: int = 0
    has_summary: bool = False       # 是否已有摘要
    is_favorite: bool = False       # 是否已收藏
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NewsListResponse(BaseModel):
    """新闻列表响应"""
    total: int
    page: int
    page_size: int
    items: List[NewsItem]


# ============================================
# Summary 相关
# ============================================

class SummaryRequest(BaseModel):
    """生成摘要请求"""
    news_id: Optional[int] = Field(default=None, description="已有新闻ID（可选）")
    text: Optional[str] = Field(default=None, description="直接输入新闻文本（可选）")
    top_k: int = Field(default=5, ge=1, le=10, description="TextRank 关键句数量")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "新华社北京3月15日电 人工智能技术正在深刻改变世界..."
            }
        }


class SummaryResponse(BaseModel):
    """摘要生成响应"""
    news_id: Optional[int] = None
    summary_id: int
    extractive_summary: str       # 抽取式摘要
    abstractive_summary: str      # 生成式摘要
    inference_time: float         # 推理耗时（秒）
    rouge_l: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# Favorite 相关
# ============================================

class FavoriteRequest(BaseModel):
    """添加收藏请求"""
    news_id: int = Field(..., description="要收藏的新闻ID")

    class Config:
        json_schema_extra = {
            "example": {"news_id": 1}
        }


class FavoriteResponse(BaseModel):
    """收藏响应"""
    id: int
    news_id: int
    category: Optional[str] = None
    content_preview: Optional[str] = None
    length: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FavoriteListResponse(BaseModel):
    """收藏列表响应"""
    total: int
    items: List[FavoriteResponse]


# ============================================
# History 相关
# ============================================

class HistoryItem(BaseModel):
    """历史记录项"""
    id: int
    news_id: int
    action: str
    category: Optional[str] = None
    content_preview: Optional[str] = None
    length: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HistoryListResponse(BaseModel):
    """历史列表响应"""
    total: int
    page: int
    page_size: int
    items: List[HistoryItem]


# ============================================
# Feedback 相关
# ============================================

class FeedbackRequest(BaseModel):
    """提交反馈请求"""
    news_id: Optional[int] = Field(default=None, description="关联新闻ID")
    summary_id: Optional[int] = Field(default=None, description="关联摘要ID")
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    comment: Optional[str] = Field(default="", description="反馈文字")

    class Config:
        json_schema_extra = {
            "example": {
                "news_id": 1,
                "summary_id": 1,
                "rating": 4,
                "comment": "摘要简洁但漏掉了关键信息"
            }
        }


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: int
    news_id: Optional[int] = None
    summary_id: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# 通用响应
# ============================================

class MessageResponse(BaseModel):
    """通用消息响应"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[dict] = None
