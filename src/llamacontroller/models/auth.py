"""
认证相关的 Pydantic 模型
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# ==================== 请求模型 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=1, description="密码")

class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码至少需要 8 个字符")
        return v

class CreateUserRequest(BaseModel):
    """创建用户请求（管理员）"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, description="密码")
    role: str = Field(default="user", description="角色：admin 或 user")
    
    @validator('role')
    def validate_role(cls, v):
        """验证角色"""
        if v not in ["admin", "user"]:
            raise ValueError("角色必须是 admin 或 user")
        return v

class UpdateUserRequest(BaseModel):
    """更新用户请求（管理员）"""
    is_active: Optional[bool] = Field(None, description="是否激活")
    role: Optional[str] = Field(None, description="角色")
    
    @validator('role')
    def validate_role(cls, v):
        """验证角色"""
        if v is not None and v not in ["admin", "user"]:
            raise ValueError("角色必须是 admin 或 user")
        return v

class CreateTokenRequest(BaseModel):
    """创建 API 令牌请求"""
    name: str = Field(..., min_length=1, max_length=100, description="令牌名称")
    expires_days: Optional[int] = Field(None, gt=0, le=365, description="过期天数（1-365）")

class UpdateTokenRequest(BaseModel):
    """更新令牌请求"""
    is_active: bool = Field(..., description="是否激活")

# ==================== 响应模型 ====================

class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    failed_login_attempts: int
    locked_until: Optional[datetime]
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """登录响应"""
    user: UserResponse
    session_id: str
    expires_at: datetime
    message: str = "登录成功"

class TokenResponse(BaseModel):
    """令牌响应"""
    id: int
    name: str
    token: Optional[str] = None  # 仅在创建时返回原始令牌
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class TokenListResponse(BaseModel):
    """令牌列表响应"""
    tokens: List[TokenResponse]
    total: int

class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse]
    total: int

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True

class CurrentUserResponse(BaseModel):
    """当前用户信息响应"""
    user: UserResponse
    session: SessionInfo

class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    user_id: Optional[int]
    username: Optional[str]  # 从 user 关系填充
    action: str
    resource: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    success: bool
    
    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    """审计日志列表响应"""
    logs: List[AuditLogResponse]
    total: int

# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    success: bool = False
