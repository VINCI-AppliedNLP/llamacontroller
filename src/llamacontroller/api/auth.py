"""
认证 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from llamacontroller.api.dependencies import get_db
from llamacontroller.auth.service import AuthService
from llamacontroller.auth.dependencies import get_current_user, get_current_session
from llamacontroller.db.models import User, Session as DBSession
from llamacontroller.models.auth import (
    LoginRequest,
    LoginResponse,
    ChangePasswordRequest,
    MessageResponse,
    CurrentUserResponse,
    UserResponse,
    SessionInfo
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


def get_client_info(request: Request) -> tuple[str | None, str | None]:
    """
    获取客户端信息
    
    Returns:
        tuple[ip_address, user_agent]
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    login_req: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    """
    ip_address, user_agent = get_client_info(request)
    
    # 创建认证服务
    auth_service = AuthService(db)
    
    # 认证用户
    success, error_msg, user = auth_service.authenticate_user(
        username=login_req.username,
        password=login_req.password,
        ip_address=ip_address
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg
        )
    
    # 创建会话
    response = auth_service.create_session(
        user=user,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return response


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_session: DBSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    用户登出
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    """
    ip_address, _ = get_client_info(request)
    
    # 创建认证服务
    auth_service = AuthService(db)
    
    # 登出
    success = auth_service.logout(
        session_id=current_session.session_id,
        ip_address=ip_address
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="登出失败"
        )
    
    return MessageResponse(message="登出成功")


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    current_session: DBSession = Depends(get_current_session)
):
    """
    获取当前用户信息
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    """
    return CurrentUserResponse(
        user=UserResponse.from_orm(current_user),
        session=SessionInfo.from_orm(current_session)
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: Request,
    password_req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    
    - **old_password**: 旧密码
    - **new_password**: 新密码（至少 8 个字符）
    """
    ip_address, _ = get_client_info(request)
    
    # 创建认证服务
    auth_service = AuthService(db)
    
    # 修改密码
    success, error_msg = auth_service.change_password(
        user=current_user,
        old_password=password_req.old_password,
        new_password=password_req.new_password,
        ip_address=ip_address
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    return MessageResponse(message="密码修改成功")
