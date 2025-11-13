"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional

from llamacontroller.db.base import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # admin, user
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, nullable=False, default=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # 关系
    api_tokens = relationship("APIToken", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def is_locked(self) -> bool:
        """检查用户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def is_admin(self) -> bool:
        """检查用户是否是管理员"""
        return self.role == "admin"


class APIToken(Base):
    """API 令牌模型"""
    __tablename__ = "api_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # 关系
    user = relationship("User", back_populates="api_tokens")
    
    def __repr__(self) -> str:
        return f"<APIToken(id={self.id}, name='{self.name}', user_id={self.user_id})>"
    
    def is_expired(self) -> bool:
        """检查令牌是否过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return self.is_active and not self.is_expired()


class Session(Base):
    """会话模型"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv4 或 IPv6
    user_agent = Column(Text, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, user_id={self.user_id}, session_id='{self.session_id[:8]}...')>"
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create_expires_at(cls, timeout_seconds: int = 3600) -> datetime:
        """创建过期时间"""
        return datetime.utcnow() + timedelta(seconds=timeout_seconds)


class AuditLog(Base):
    """审计日志模型"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可选，匿名操作时为空
    action = Column(String(50), nullable=False, index=True)  # login, logout, load_model, etc.
    resource = Column(String(100), nullable=True)  # model_id, token_id, etc.
    details = Column(Text, nullable=True)  # JSON 格式的额外信息
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    success = Column(Boolean, nullable=False, default=True)
    
    # 关系
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', success={self.success})>"
