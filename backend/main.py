# ============================================
# 文件名: backend/main.py
# 功能: FastAPI 主入口
# 启动: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
# ============================================

import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import init_db
from backend.routers import news, summary, favorite, history, feedback


# ============================================
# 应用生命周期
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的回调"""
    # 启动时：初始化数据库
    print("=" * 50)
    print(" NewsMind Backend 启动中...")
    print("=" * 50)
    init_db()
    print("[OK] 数据库初始化完成")
    yield
    # 关闭时：清理资源
    print("[OK] NewsMind Backend 已关闭")


# ============================================
# 创建 FastAPI 应用
# ============================================

app = FastAPI(
    title="NewsMind API",
    description="""
## 📰 NewsMind - 智能新闻摘要系统 API

基于 BERT + TextRank + T5 的中文新闻自动摘要后端服务。

### 功能模块:
- **新闻管理**: 新闻列表、详情、分类、搜索
- **摘要生成**: 一键生成抽取式+生成式摘要
- **收藏管理**: 添加/删除/查看收藏
- **操作历史**: 浏览和摘要生成记录
- **用户反馈**: 摘要质量评分

### 技术栈:
- FastAPI + SQLAlchemy + SQLite
- BERT-base-chinese 句子编码
- TextRank 关键句提取
- T5-small Transformer 摘要生成
- ROUGE-L 质量评估
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc
)


# ============================================
# CORS 中间件（允许 ArkTS 前端访问）
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 注册路由
# ============================================

app.include_router(news.router)
app.include_router(summary.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(feedback.router)


# ============================================
# 根路径 & 健康检查
# ============================================

@app.get("/", tags=["系统"])
async def root():
    """API 根路径"""
    return {
        "name": "NewsMind API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": "ok", "message": "NewsMind API is running"}


# ============================================
# 数据导入接口（将预处理数据导入数据库）
# ============================================

@app.post("/admin/import-data", tags=["管理"])
async def import_processed_data():
    """
    ## 导入预处理数据到数据库

    将 data/processed/train.json 等文件导入 SQLite 数据库。
    首次启动后调用此接口填充数据。
    """
    import json
    from backend.database import SessionLocal
    from backend.models.models import News

    processed_dir = Path(__file__).resolve().parent.parent / "data" / "processed"

    imported = 0
    for filename in ["train.json", "val.json", "test.json"]:
        filepath = processed_dir / filename
        if not filepath.exists():
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        db = SessionLocal()
        try:
            for item in data:
                # 检查不重复
                existing = db.query(News).filter(
                    News.content.startswith(item.get("content", "")[:100])
                ).first()
                if existing:
                    continue

                news = News(
                    category=item.get("category", "未知"),
                    content=item.get("content", ""),
                    tokenized=item.get("tokenized", ""),
                    length=item.get("length", 0),
                    token_length=item.get("token_length", 0),
                )
                db.add(news)
                imported += 1

            db.commit()
        finally:
            db.close()

    return {
        "success": True,
        "message": f"数据导入完成",
        "imported_count": imported,
    }


# ============================================
# 直接运行入口
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
