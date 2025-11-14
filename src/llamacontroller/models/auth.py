"""
Authentication-related Pydantic models
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

# ==================== Request Models ====================

class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=1, description="Password")

class ChangePasswordRequest(BaseModel):
    """Change password request"""
    old_password: str = Field(..., min_length=1, description="Old password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class CreateUserRequest(BaseModel):
    """Create user request (admin)"""
    username: str = Field(..., min_length=1, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    role: str = Field(default="user", description="Role: admin or user")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role"""
        if v not in ["admin", "user"]:
            raise ValueError("Role must be admin or user")
        return v

class UpdateUserRequest(BaseModel):
    """Update user request (admin)"""
    is_active: Optional[bool] = Field(None, description="Is active")
    role: Optional[str] = Field(None, description="Role")
    
    @validator('role')
    def validate_role(cls, v):
        """Validate role"""
        if v is not None and v not in ["admin", "user"]:
            raise ValueError("Role must be admin or user")
        return v

class CreateTokenRequest(BaseModel):
    """Create API token request"""
    name: str = Field(..., min_length=1, max_length=100, description="Token name")
    expires_days: Optional[int] = Field(None, gt=0, le=365, description="Expiry days (1-365)")

class UpdateTokenRequest(BaseModel):
    """Update token request"""
    is_active: bool = Field(..., description="Is active")

# ==================== Response Models ====================

class UserResponse(BaseModel):
    """User response"""
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
    """Login response"""
    user: UserResponse
    session_id: str
    expires_at: datetime
    message: str = "Login successful"

class TokenResponse(BaseModel):
    """Token response"""
    id: int
    name: str
    token: Optional[str] = None  # Only returns raw token on creation
    created_at: datetime
    last_used_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True

class TokenListResponse(BaseModel):
    """Token list response"""
    tokens: List[TokenResponse]
    total: int

class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total: int

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    user_id: int
    created_at: datetime
    expires_at: datetime
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True

class CurrentUserResponse(BaseModel):
    """Current user information response"""
    user: UserResponse
    session: SessionInfo

class AuditLogResponse(BaseModel):
    """Audit log response"""
    id: int
    user_id: Optional[int]
    username: Optional[str]  # Populated from user relationship
    action: str
    resource: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    success: bool
    
    class Config:
        from_attributes = True

class AuditLogListResponse(BaseModel):
    """Audit log list response"""
    logs: List[AuditLogResponse]
    total: int

# ==================== Common Responses ====================

class MessageResponse(BaseModel):
    """Common message response"""
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    success: bool = False
