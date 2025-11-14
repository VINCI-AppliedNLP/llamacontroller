"""
Authentication service
"""
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status
import json

from llamacontroller.db import crud
from llamacontroller.db.models import User, APIToken
from llamacontroller.auth.utils import hash_password, verify_password
from llamacontroller.models.auth import LoginResponse, UserResponse, SessionInfo

class AuthService:
    """Authentication service class"""
    
    def __init__(self, db: Session, session_timeout: int = 3600):
        """
        Initialize authentication service
        
        Args:
            db: Database session
            session_timeout: Session timeout in seconds, default 1 hour
        """
        self.db = db
        self.session_timeout = session_timeout
    
    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> tuple[bool, Optional[str], Optional[User]]:
        """
        Authenticate user
        
        Args:
            username: Username
            password: Password
            ip_address: IP address
        
        Returns:
            tuple[bool, Optional[str], Optional[User]]: (Success?, Error message?, User object?)
        """
        # Find user
        user = crud.get_user_by_username(self.db, username)
        
        # Record audit log audit log
        crud.create_audit_log(
            self.db,
            action="login_attempt",
            success=False,  # Assume failure first, will create new record if successful
            user_id=user.id if user else None,
            ip_address=ip_address
        )
        
        # User doesn't exist
        if user is None:
            return False, "Incorrect username or password", None
        
        # Check if user is active
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Check if user is locked
        if user.is_locked():
            return False, f"Account is locked, please try again later", None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            # Increment failure count
            crud.increment_failed_login(self.db, user)
            return False, "Incorrect username or password", None
        
        # Authentication successful, reset failure count
        crud.reset_failed_login(self.db, user)
        
        return True, None, user
    
    def create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """
        Create session
        
        Args:
            user: User object
            ip_address: IP address
            user_agent: User-Agent
        
        Returns:
            LoginResponse: Login response
        """
        # Create sessionte session
        session = crud.create_session(
            self.db,
            user_id=user.id,
            timeout_seconds=self.session_timeout,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Record successful login
        crud.create_audit_log(
            self.db,
            action="login",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
            details=json.dumps({"user_agent": user_agent})
        )
        
        # Build response
        return LoginResponse(
            user=UserResponse.from_orm(user),
            session_id=session.session_id,
            expires_at=session.expires_at
        )
    
    def verify_session(self, session_id: str) -> Optional[User]:
        """
        Verify session
        
        Args:
            session_id: Session ID
        
        Returns:
            User if session is valid, otherwise None
        """
        session = crud.verify_session(self.db, session_id)
        
        if session is None:
            return None
        
        # Get user
        user = crud.get_user_by_id(self.db, session.user_id)
        
        # Check if user is active
        if user is None or not user.is_active:
            return None
        
        return user
    
    def logout(self, session_id: str, ip_address: Optional[str] = None) -> bool:
        """
        Logout (delete session)
        
        Args:
            session_id: Session ID
            ip_address: IP address
        
        Returns:
            bool: Whether successful
        """
        session = crud.get_session_by_id(self.db, session_id)
        
        if session is None:
            return False
        
        # Record logout
        crud.create_audit_log(
            self.db,
            action="logout",
            success=True,
            user_id=session.user_id,
            ip_address=ip_address
        )
        
        # Delete session
        crud.delete_session(self.db, session)
        
        return True
    
    def verify_api_token(self, raw_token: str) -> Optional[User]:
        """
        Verify API token
        
        Args:
            raw_token: Raw token string
        
        Returns:
            User if token is valid, otherwise None
        """
        token = crud.verify_api_token(self.db, raw_token)
        
        if token is None:
            return None
        
        # Get user
        user = crud.get_user_by_id(self.db, token.user_id)
        
        # Check if user is active
        if user is None or not user.is_active:
            return None
        
        return user
    
    def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Change password
        
        Args:
            user: User object
            old_password: Old password
            new_password: New password
            ip_address: IP address
        
        Returns:
            tuple[bool, Optional[str]]: (Success?, Error message?)
        """
        # Verify old password
        if not verify_password(old_password, user.password_hash):
            crud.create_audit_log(
                self.db,
                action="change_password",
                success=False,
                user_id=user.id,
                ip_address=ip_address,
                details="Incorrect old password"
            )
            return False, "Incorrect old password"
        
        # Hash new password
        new_password_hash = hash_password(new_password)
        
        # Update password
        user.password_hash = new_password_hash
        crud.update_user(self.db, user)
        
        # Record audit log
        crud.create_audit_log(
            self.db,
            action="change_password",
            success=True,
            user_id=user.id,
            ip_address=ip_address
        )
        
        return True, None
    
    def create_user(
        self,
        username: str,
        password: str,
        role: str = "user",
        created_by_user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> User:
        """
        Create user
        
        Args:
            username: Username
            password: Password
            role: Role
            created_by_user_id: Creator user ID
            ip_address: IP address
        
        Returns:
            User: New user object
        """
        # Check if username already exists
        existing_user = crud.get_user_by_username(self.db, username)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = crud.create_user(self.db, username, password_hash, role)
        
        # Record audit log
        crud.create_audit_log(
            self.db,
            action="create_user",
            success=True,
            user_id=created_by_user_id,
            resource=str(user.id),
            ip_address=ip_address,
            details=json.dumps({"username": username, "role": role})
        )
        
        return user
