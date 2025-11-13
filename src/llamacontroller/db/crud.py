"""
数据库 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import secrets
import hashlib

from llamacontroller.db.models import User, APIToken, Session as DBSession, AuditLog

# ==================== User CRUD ====================

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """通过 ID 获取用户"""
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """通过用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """获取用户列表"""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, username: str, password_hash: str, role: str = "user") -> User:
    """创建新用户"""
    user = User(
        username=username,
        password_hash=password_hash,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user: User) -> User:
    """更新用户"""
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user: User) -> None:
    """删除用户"""
    db.delete(user)
    db.commit()

def increment_failed_login(db: Session, user: User, lockout_duration: int = 300) -> User:
    """
    增加失败登录次数
    
    Args:
        db: 数据库会话
        user: 用户对象
        lockout_duration: 锁定时长（秒），默认 5 分钟
    """
    user.failed_login_attempts += 1
    
    # 如果失败次数达到 5 次，锁定账户
    if user.failed_login_attempts >= 5:
        user.locked_until = datetime.utcnow() + timedelta(seconds=lockout_duration)
    
    db.commit()
    db.refresh(user)
    return user

def reset_failed_login(db: Session, user: User) -> User:
    """重置失败登录次数"""
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)
    return user

# ==================== API Token CRUD ====================

def get_api_token_by_id(db: Session, token_id: int) -> Optional[APIToken]:
    """通过 ID 获取令牌"""
    return db.query(APIToken).filter(APIToken.id == token_id).first()

def get_api_token_by_hash(db: Session, token_hash: str) -> Optional[APIToken]:
    """通过哈希值获取令牌"""
    return db.query(APIToken).filter(APIToken.token_hash == token_hash).first()

def get_user_api_tokens(db: Session, user_id: int) -> List[APIToken]:
    """获取用户的所有令牌"""
    return db.query(APIToken).filter(APIToken.user_id == user_id).all()

def create_api_token(
    db: Session,
    user_id: int,
    name: str,
    expires_days: Optional[int] = None,
    custom_token: Optional[str] = None
) -> tuple[APIToken, str]:
    """
    创建 API 令牌
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        name: 令牌名称
        expires_days: 过期天数（可选）
        custom_token: 自定义令牌值（可选，如果不提供则自动生成）
    
    Returns:
        tuple[APIToken, str]: (数据库记录, 原始令牌)
    """
    # 使用自定义令牌或生成随机令牌
    if custom_token:
        raw_token = custom_token
    else:
        # 生成推荐长度的令牌（32字节 = 43字符 base64）
        raw_token = secrets.token_urlsafe(32)
    
    # 计算哈希值用于存储
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # 计算过期时间
    expires_at = None
    if expires_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
    
    # 创建数据库记录
    api_token = APIToken(
        user_id=user_id,
        token_hash=token_hash,
        name=name,
        expires_at=expires_at
    )
    
    db.add(api_token)
    db.commit()
    db.refresh(api_token)
    
    return api_token, raw_token

def generate_token(length: int = 32) -> str:
    """
    生成推荐的随机令牌
    
    Args:
        length: 字节长度（默认 32 字节 = ~43 字符）
    
    Returns:
        str: URL 安全的 base64 编码令牌
    """
    return secrets.token_urlsafe(length)

def update_api_token_last_used(db: Session, token: APIToken) -> APIToken:
    """更新令牌最后使用时间"""
    token.last_used_at = datetime.utcnow()
    db.commit()
    db.refresh(token)
    return token

def update_api_token(db: Session, token: APIToken) -> APIToken:
    """更新令牌"""
    db.commit()
    db.refresh(token)
    return token

def delete_api_token(db: Session, token: APIToken) -> None:
    """删除令牌"""
    db.delete(token)
    db.commit()

def verify_api_token(db: Session, raw_token: str) -> Optional[APIToken]:
    """
    验证 API 令牌
    
    Args:
        db: 数据库会话
        raw_token: 原始令牌字符串
    
    Returns:
        APIToken 如果有效，否则 None
    """
    # 计算哈希值
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    # 查找令牌
    token = get_api_token_by_hash(db, token_hash)
    
    if token is None:
        return None
    
    # 检查是否有效
    if not token.is_valid():
        return None
    
    # 更新最后使用时间
    update_api_token_last_used(db, token)
    
    return token

# ==================== Session CRUD ====================

def get_session_by_id(db: Session, session_id: str) -> Optional[DBSession]:
    """通过会话 ID 获取会话"""
    return db.query(DBSession).filter(DBSession.session_id == session_id).first()

def get_user_sessions(db: Session, user_id: int) -> List[DBSession]:
    """获取用户的所有会话"""
    return db.query(DBSession).filter(DBSession.user_id == user_id).all()

def create_session(
    db: Session,
    user_id: int,
    timeout_seconds: int = 3600,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> DBSession:
    """创建会话"""
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
    
    session = DBSession(
        session_id=session_id,
        user_id=user_id,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session

def delete_session(db: Session, session: DBSession) -> None:
    """删除会话"""
    db.delete(session)
    db.commit()

def delete_expired_sessions(db: Session) -> int:
    """删除所有过期会话"""
    count = db.query(DBSession).filter(
        DBSession.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    return count

def verify_session(db: Session, session_id: str) -> Optional[DBSession]:
    """
    验证会话
    
    Returns:
        DBSession 如果有效，否则 None
    """
    session = get_session_by_id(db, session_id)
    
    if session is None:
        return None
    
    if session.is_expired():
        delete_session(db, session)
        return None
    
    return session

# ==================== Audit Log CRUD ====================

def create_audit_log(
    db: Session,
    action: str,
    success: bool = True,
    user_id: Optional[int] = None,
    resource: Optional[str] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """创建审计日志"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        ip_address=ip_address,
        success=success
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return log

def get_audit_logs(
    db: Session,
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[AuditLog]:
    """获取审计日志"""
    query = db.query(AuditLog)
    
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    
    if action is not None:
        query = query.filter(AuditLog.action == action)
    
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

def delete_old_audit_logs(db: Session, days: int = 90) -> int:
    """删除旧的审计日志"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    count = db.query(AuditLog).filter(
        AuditLog.created_at < cutoff_date
    ).delete()
    db.commit()
    return count
