"""
认证相关的 FastAPI 依赖
"""
from fastapi import Depends, HTTPException, status, Request, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from llamacontroller.api.dependencies import get_db
from llamacontroller.db.models import User, Session as DBSession
from llamacontroller.auth.service import AuthService
from llamacontroller.auth.utils import get_client_ip, get_user_agent
from llamacontroller.db import crud

# HTTP Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)

async def verify_api_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    验证API Token (Bearer token)
    
    用于Ollama API端点的认证。
    期望格式: Authorization: Bearer llc_xxxxx
    
    Args:
        authorization: Authorization header值
        db: 数据库会话
        
    Returns:
        验证通过的User对象
        
    Raises:
        HTTPException: 如果Token无效或过期
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header. Use: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # Verify token
    api_token = crud.verify_api_token(db, token)
    if not api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = crud.get_user_by_id(db, api_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last_used_at timestamp
    crud.update_api_token_last_used(db, api_token)
    
    return user

def get_current_user_from_session(
    session_id: str = Cookie(None, alias="session_id"),
    x_session_id: str = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db)
) -> User:
    """
    从会话 Cookie 获取当前用户（用于 Web UI）
    
    Raises:
        HTTPException: 如果会话无效或未认证
    """
    # 优先从 X-Session-ID 头获取
    final_session_id = x_session_id if x_session_id else session_id
    
    if final_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录"
        )
    
    # 验证会话
    session = crud.verify_session(db, final_session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期，请重新登录"
        )
    
    # 获取用户
    user = crud.get_user_by_id(db, session.user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用"
        )
    
    return user

async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth: AuthService = Depends(get_auth_service)
) -> User:
    """
    从 Bearer Token 获取当前用户（用于 API）
    
    Raises:
        HTTPException: 如果令牌无效或未认证
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth.verify_api_token(credentials.credentials)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

async def get_optional_user_from_session(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    从会话 Cookie 获取当前用户（可选，用于 Web UI）
    
    Returns:
        User 如果已认证，否则 None
    """
    if session_id is None:
        return None
    
    # 验证会话
    session = crud.verify_session(db, session_id)
    
    if session is None:
        return None
    
    # 获取用户
    user = crud.get_user_by_id(db, session.user_id)
    
    return user if user and user.is_active else None

async def get_current_user_optional(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    获取当前用户（可选，支持会话和令牌）
    
    优先使用会话 Cookie，然后是 Bearer Token
    
    Returns:
        User 如果已认证，否则 None
    """
    # 先尝试会话
    if session_id is not None:
        user = auth.verify_session(session_id)
        if user is not None:
            return user
    
    # 再尝试令牌
    if credentials is not None:
        user = auth.verify_api_token(credentials.credentials)
        if user is not None:
            return user
    
    return None

async def get_current_user(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth: AuthService = Depends(get_auth_service)
) -> User:
    """
    获取当前用户（必需，支持会话和令牌）
    
    优先使用会话 Cookie，然后是 Bearer Token
    
    Raises:
        HTTPException: 如果未认证
    """
    user = await get_current_user_optional(session_id, credentials, auth)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证"
        )
    
    return user

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    要求管理员权限
    
    Raises:
        HTTPException: 如果用户不是管理员
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    return current_user

async def get_current_session(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> DBSession:
    """
    获取当前会话对象
    
    支持从 Cookie 或 X-Session-ID 头获取会话 ID
    
    Raises:
        HTTPException: 如果会话无效或未认证
    """
    # 优先从 X-Session-ID 头获取
    if x_session_id is None:
        x_session_id = request.headers.get("X-Session-ID")
    
    # 如果头中没有，使用 Cookie
    final_session_id = x_session_id if x_session_id else session_id
    
    if final_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供会话 ID"
        )
    
    # 验证会话
    session = crud.verify_session(db, final_session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期或无效"
        )
    
    return session

def get_request_info(request: Request) -> dict:
    """
    获取请求信息（IP 地址、User-Agent 等）
    
    Returns:
        dict: {"ip_address": str, "user_agent": str}
    """
    return {
        "ip_address": get_client_ip(request),
        "user_agent": get_user_agent(request)
    }
