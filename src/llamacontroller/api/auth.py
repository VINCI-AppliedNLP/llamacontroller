"""
Authentication API endpoints
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

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def get_client_info(request: Request) -> tuple[str | None, str | None]:
    """
    Get client information
    
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
    User login
    
    - **username**: Username
    - **password**: Password
    """
    ip_address, user_agent = get_client_info(request)
    
    # Create authentication service
    auth_service = AuthService(db)
    
    # Authenticate user
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
    
    # Create session
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
    User logout
    
    Requires session ID via Cookie or X-Session-ID header
    """
    ip_address, _ = get_client_info(request)
    
    # Create authentication service
    auth_service = AuthService(db)
    
    # Logout
    success = auth_service.logout(
        session_id=current_session.session_id,
        ip_address=ip_address
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Logout failed"
        )
    
    return MessageResponse(message="Logout successful")


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    current_session: DBSession = Depends(get_current_session)
):
    """
    Get current user information
    
    Requires session ID via Cookie or X-Session-ID header
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
    Change password
    
    Requires session ID via Cookie or X-Session-ID header
    
    - **old_password**: Old password
    - **new_password**: New password (at least 8 characters)
    """
    ip_address, _ = get_client_info(request)
    
    # Create authentication service
    auth_service = AuthService(db)
    
    # Change password
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
    
    return MessageResponse(message="Password changed successfully")
