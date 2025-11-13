"""
认证服务
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
    """认证服务类"""
    
    def __init__(self, db: Session, session_timeout: int = 3600):
        """
        初始化认证服务
        
        Args:
            db: 数据库会话
            session_timeout: 会话超时时间（秒），默认 1 小时
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
        认证用户
        
        Args:
            username: 用户名
            password: 密码
            ip_address: IP 地址
        
        Returns:
            tuple[bool, Optional[str], Optional[User]]: (成功?, 错误消息?, 用户对象?)
        """
        # 查找用户
        user = crud.get_user_by_username(self.db, username)
        
        # 记录审计日志
        crud.create_audit_log(
            self.db,
            action="login_attempt",
            success=False,  # 先假设失败，成功时会创建新记录
            user_id=user.id if user else None,
            ip_address=ip_address
        )
        
        # 用户不存在
        if user is None:
            return False, "用户名或密码错误", None
        
        # 检查用户是否激活
        if not user.is_active:
            return False, "账户已被禁用", None
        
        # 检查用户是否被锁定
        if user.is_locked():
            return False, f"账户已锁定，请稍后再试", None
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            # 增加失败次数
            crud.increment_failed_login(self.db, user)
            return False, "用户名或密码错误", None
        
        # 认证成功，重置失败次数
        crud.reset_failed_login(self.db, user)
        
        return True, None, user
    
    def create_session(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LoginResponse:
        """
        创建会话
        
        Args:
            user: 用户对象
            ip_address: IP 地址
            user_agent: User-Agent
        
        Returns:
            LoginResponse: 登录响应
        """
        # 创建会话
        session = crud.create_session(
            self.db,
            user_id=user.id,
            timeout_seconds=self.session_timeout,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # 记录成功登录
        crud.create_audit_log(
            self.db,
            action="login",
            success=True,
            user_id=user.id,
            ip_address=ip_address,
            details=json.dumps({"user_agent": user_agent})
        )
        
        # 构建响应
        return LoginResponse(
            user=UserResponse.from_orm(user),
            session_id=session.session_id,
            expires_at=session.expires_at
        )
    
    def verify_session(self, session_id: str) -> Optional[User]:
        """
        验证会话
        
        Args:
            session_id: 会话 ID
        
        Returns:
            User 如果会话有效，否则 None
        """
        session = crud.verify_session(self.db, session_id)
        
        if session is None:
            return None
        
        # 获取用户
        user = crud.get_user_by_id(self.db, session.user_id)
        
        # 检查用户是否激活
        if user is None or not user.is_active:
            return None
        
        return user
    
    def logout(self, session_id: str, ip_address: Optional[str] = None) -> bool:
        """
        登出（删除会话）
        
        Args:
            session_id: 会话 ID
            ip_address: IP 地址
        
        Returns:
            bool: 是否成功
        """
        session = crud.get_session_by_id(self.db, session_id)
        
        if session is None:
            return False
        
        # 记录登出
        crud.create_audit_log(
            self.db,
            action="logout",
            success=True,
            user_id=session.user_id,
            ip_address=ip_address
        )
        
        # 删除会话
        crud.delete_session(self.db, session)
        
        return True
    
    def verify_api_token(self, raw_token: str) -> Optional[User]:
        """
        验证 API 令牌
        
        Args:
            raw_token: 原始令牌字符串
        
        Returns:
            User 如果令牌有效，否则 None
        """
        token = crud.verify_api_token(self.db, raw_token)
        
        if token is None:
            return None
        
        # 获取用户
        user = crud.get_user_by_id(self.db, token.user_id)
        
        # 检查用户是否激活
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
        修改密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
            ip_address: IP 地址
        
        Returns:
            tuple[bool, Optional[str]]: (成功?, 错误消息?)
        """
        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            crud.create_audit_log(
                self.db,
                action="change_password",
                success=False,
                user_id=user.id,
                ip_address=ip_address,
                details="旧密码错误"
            )
            return False, "旧密码错误"
        
        # 哈希新密码
        new_password_hash = hash_password(new_password)
        
        # 更新密码
        user.password_hash = new_password_hash
        crud.update_user(self.db, user)
        
        # 记录审计日志
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
        创建用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色
            created_by_user_id: 创建者用户 ID
            ip_address: IP 地址
        
        Returns:
            User: 新用户对象
        """
        # 检查用户名是否已存在
        existing_user = crud.get_user_by_username(self.db, username)
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 哈希密码
        password_hash = hash_password(password)
        
        # 创建用户
        user = crud.create_user(self.db, username, password_hash, role)
        
        # 记录审计日志
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
