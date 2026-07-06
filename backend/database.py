# ============================================
# 文件名: backend/database.py
# 功能: 数据库连接和会话管理
# ============================================

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 数据库文件路径（项目根目录下的 newsmind.db）
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'newsmind.db'}"

# 创建引擎（SQLite 需开启多线程支持）
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # FastAPI 多线程需要
    echo=False,  # 生产环境关闭 SQL 日志
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ORM 基类
Base = declarative_base()


def init_db():
    """初始化数据库：创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    获取数据库会话（FastAPI 依赖注入用）
    使用完毕后自动关闭会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
