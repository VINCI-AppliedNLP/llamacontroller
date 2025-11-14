"""
Authentication-related FastAPI dependencies
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
    """Get authentication service instance"""
    return AuthService(db)

async def verify_api_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify API Token (Bearer token)
    
    Used for authentication in Ollama API endpoints.
    Expected format: Authorization: Bearer llc_xxxxx
    
    Args:
        authorization: Authorization header value
        db: Database session
        
    Returns:
        Verified User object
        
    Raises:
        HTTPException: If token is invalid or expired
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
    Get current user from session Cookie (for Web UI)
    
    Raises:
        HTTPException: If session is invalid or not authenticated
    """
    # Prioritize getting from X-Session-ID header
    final_session_id = x_session_id if x_session_id else session_id
    
    if final_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in"
        )
    
    # Verify session
    session = crud.verify_session(db, final_session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, please login again"
        )
    
    # Get user
    user = crud.get_user_by_id(db, session.user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User does not exist or is disabled"
        )
    
    return user

async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current user from Bearer Token (for API)
    
    Raises:
        HTTPException: If token is invalid or not authenticated
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth.verify_api_token(credentials.credentials)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

async def get_optional_user_from_session(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from session Cookie (optional, for Web UI)
    
    Returns:
        User if authenticated, otherwise None
    """
    if session_id is None:
        return None
    
    # Verify session
    session = crud.verify_session(db, session_id)
    
    if session is None:
        return None
    
    # Get user
    user = crud.get_user_by_id(db, session.user_id)
    
    return user if user and user.is_active else None

async def get_current_user_optional(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Get current user (optional, supports session and token)
    
    Prioritize session Cookie, then Bearer Token
    
    Returns:
        User if authenticated, otherwise None
    """
    # Try session first
    if session_id is not None:
        user = auth.verify_session(session_id)
        if user is not None:
            return user
    
    # Then try token
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
    Get current user (required, supports session and token)
    
    Prioritize session Cookie, then Bearer Token
    
    Raises:
        HTTPException: If not authenticated
    """
    user = await get_current_user_optional(session_id, credentials, auth)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return user

async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require admin privileges
    
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user

async def get_current_session(
    request: Request,
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    x_session_id: Optional[str] = None,
    db: Session = Depends(get_db)
) -> DBSession:
    """
    Get current session object
    
    Supports getting session ID from Cookie or X-Session-ID header
    
    Raises:
        HTTPException: If session is invalid or not authenticated
    """
    # Prioritize getting from X-Session-ID header
    if x_session_id is None:
        x_session_id = request.headers.get("X-Session-ID")
    
    # If not in header, use Cookie
    final_session_id = x_session_id if x_session_id else session_id
    
    if final_session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session ID not provided"
        )
    
    # Verify session
    session = crud.verify_session(db, final_session_id)
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    return session

def get_request_info(request: Request) -> dict:
    """
    Get request information (IP address, User-Agent, etc.)
    
    Returns:
        dict: {"ip_address": str, "user_agent": str}
    """
    return {
        "ip_address": get_client_ip(request),
        "user_agent": get_user_agent(request)
    }
