# ============================================
# 文件名: backend/services/user_service.py
# 功能: 用户认证业务逻辑
# ============================================

import hashlib
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from backend.models.models import User


def _hash_password(password: str) -> str:
    """简单的密码哈希（SHA-256 + salt）"""
    salt = "newsmind_salt_2024"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()


def _generate_token() -> str:
    """生成随机登录令牌"""
    return secrets.token_hex(32)


def register(
    db: Session,
    username: str,
    password: str,
) -> User:
    """
    注册新用户
    参数:
        db: 数据库会话
        username: 用户名
        password: 密码
    返回:
        User 对象
    异常:
        ValueError: 用户名已存在
    """
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError(f"用户名 '{username}' 已存在")

    user = User(
        username=username,
        password_hash=_hash_password(password),
        token=_generate_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(
    db: Session,
    username: str,
    password: str,
) -> User:
    """
    用户登录
    参数:
        db: 数据库会话
        username: 用户名
        password: 密码
    返回:
        User 对象（带新 token）
    异常:
        ValueError: 用户名或密码错误
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("用户名或密码错误")

    if user.password_hash != _hash_password(password):
        raise ValueError("用户名或密码错误")

    # 刷新 token
    user.token = _generate_token()
    db.commit()
    db.refresh(user)
    return user


def get_user_by_token(db: Session, token: str) -> Optional[User]:
    """
    通过令牌获取用户
    参数:
        db: 数据库会话
        token: 登录令牌
    返回:
        User 对象或 None
    """
    if not token:
        return None
    return db.query(User).filter(User.token == token).first()


def logout(db: Session, token: str) -> bool:
    """
    退出登录（清除令牌）
    参数:
        db: 数据库会话
        token: 登录令牌
    返回:
        是否成功
    """
    user = get_user_by_token(db, token)
    if not user:
        return False
    user.token = None
    db.commit()
    return True


def update_profile(
    db: Session,
    token: str,
    username: Optional[str] = None,
    avatar: Optional[str] = None,
) -> User:
    """
    更新用户资料
    参数:
        db: 数据库会话
        token: 登录令牌
        username: 新用户名（可选）
        avatar: 新头像（可选）
    返回:
        更新后的 User 对象
    异常:
        ValueError: 用户不存在或用户名已存在
    """
    user = get_user_by_token(db, token)
    if not user:
        raise ValueError("用户未登录")

    if username is not None and username != user.username:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError(f"用户名 '{username}' 已存在")
        user.username = username

    if avatar is not None:
        user.avatar = avatar

    db.commit()
    db.refresh(user)
    return user
