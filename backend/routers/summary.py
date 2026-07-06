# ============================================
# 文件名: backend/routers/summary.py
# 接口: POST /summary
# 功能: 生成新闻摘要
# ============================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.schemas import (
    SummaryRequest, SummaryResponse, MessageResponse,
)
from backend.services import summary_service, history_service

router = APIRouter(prefix="/summary", tags=["摘要"])


@router.post("", response_model=SummaryResponse, summary="生成新闻摘要")
async def create_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db),
):
    """
    ## 生成新闻摘要

    支持两种输入方式:
    1. **已有新闻ID**: 传入 `news_id`，对数据库中已有新闻生成摘要
    2. **直接输入文本**: 传入 `text`，对任意文本生成摘要

    ### 请求示例 1（已有新闻）:
    ```json
    {
        "news_id": 1,
        "top_k": 5
    }
    ```

    ### 请求示例 2（直接文本）:
    ```json
    {
        "text": "新华社北京3月15日电 人工智能技术正在深刻改变世界...",
        "top_k": 5
    }
    ```

    ### 响应:
    返回抽取式摘要和生成式摘要，以及推理耗时。
    """
    # 验证输入
    if not request.news_id and not request.text:
        raise HTTPException(
            status_code=422,
            detail="必须提供 news_id 或 text 参数之一"
        )

    try:
        result = summary_service.generate_summary(
            db,
            text=request.text or "",
            news_id=request.news_id,
            top_k=request.top_k,
        )

        # 记录操作历史
        history_service.add_history(
            db,
            news_id=result.news_id or 0,
            action="summarize",
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"摘要生成失败: {str(e)}")
