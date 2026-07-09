# ============================================
# 文件名: backend/routers/auth.py
# 接口: POST /auth/register / POST /auth/login / POST /auth/logout
#        GET /auth/profile / PUT /auth/profile
# 功能: 用户认证与资料管理
# ============================================

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from backend.database import get_db
from backend.schemas.schemas import (
    RegisterRequest, LoginRequest, AuthResponse,
    UserProfile, UpdateProfileRequest, MessageResponse,
)
from backend.services import user_service

router = APIRouter(prefix="/auth", tags=["认证"])


def _get_token(authorization: Optional[str] = Header(None)) -> str:
    """从请求头提取 Bearer Token"""
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return ""


@router.post("/register", response_model=AuthResponse, summary="用户注册")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    ## 注册新用户

    注册成功后自动登录，返回 token。

    ### 请求示例:
    ```json
    {
        "username": "testuser",
        "password": "1234"
    }
    ```
    """
    try:
        user = user_service.register(db, request.username, request.password)
        return AuthResponse(
            success=True,
            message=f"注册成功，欢迎 {user.username}！",
            token=user.token,
            user_id=user.id,
            username=user.username,
            avatar=user.avatar,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse, summary="用户登录")
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    ## 用户登录

    登录成功返回 token。

    ### 请求示例:
    ```json
    {
        "username": "testuser",
        "password": "1234"
    }
    ```
    """
    try:
        user = user_service.login(db, request.username, request.password)
        return AuthResponse(
            success=True,
            message=f"登录成功，欢迎回来 {user.username}！",
            token=user.token,
            user_id=user.id,
            username=user.username,
            avatar=user.avatar,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", response_model=MessageResponse, summary="退出登录")
async def logout(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    ## 退出登录

    清除当前用户的登录令牌。
    需要在请求头中携带 `Authorization: Bearer <token>`。
    """
    token = _get_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="未提供登录令牌")

    success = user_service.logout(db, token)
    if not success:
        raise HTTPException(status_code=401, detail="无效的令牌")

    return MessageResponse(success=True, message="已退出登录")


@router.get("/profile", response_model=UserProfile, summary="获取用户资料")
async def get_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    ## 获取当前登录用户的资料

    需要在请求头中携带 `Authorization: Bearer <token>`。
    """
    token = _get_token(authorization)
    user = user_service.get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或令牌已过期")

    return UserProfile(
        id=user.id,
        username=user.username,
        avatar=user.avatar,
        created_at=user.created_at,
    )


@router.put("/profile", response_model=AuthResponse, summary="更新用户资料")
async def update_profile(
    request: UpdateProfileRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    ## 更新用户资料

    可更新用户名和头像（emoji）。
    需要在请求头中携带 `Authorization: Bearer <token>`。

    ### 请求示例:
    ```json
    {
        "username": "新名字",
        "avatar": "🎮"
    }
    ```
    """
    token = _get_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="未提供登录令牌")

    try:
        user = user_service.update_profile(
            db, token,
            username=request.username,
            avatar=request.avatar,
        )
        return AuthResponse(
            success=True,
            message="资料更新成功",
            token=user.token,
            user_id=user.id,
            username=user.username,
            avatar=user.avatar,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
