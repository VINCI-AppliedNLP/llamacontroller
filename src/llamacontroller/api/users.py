"""
用户管理 API 端点（仅管理员）
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from llamacontroller.api.dependencies import get_db
from llamacontroller.auth.dependencies import require_admin
from llamacontroller.auth.service import AuthService
from llamacontroller.db import crud
from llamacontroller.db.models import User
from llamacontroller.models.auth import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/v1/users", tags=["用户管理"])

def get_client_ip(request: Request) -> str | None:
    """获取客户端 IP 地址"""
    return request.client.host if request.client else None

@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取所有用户列表（仅管理员）
    
    需要管理员权限
    
    - **skip**: 跳过的记录数
    - **limit**: 返回的最大记录数
    """
    users = crud.get_users(db, skip=skip, limit=limit)
    total = db.query(User).count()
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total
    )

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_req: CreateUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    创建新用户（仅管理员）
    
    需要管理员权限
    
    - **username**: 用户名（1-50 个字符）
    - **password**: 密码（至少 8 个字符）
    - **role**: 角色（admin 或 user），默认为 user
    """
    ip_address = get_client_ip(request)
    
    # 创建认证服务
    auth_service = AuthService(db)
    
    # 创建用户
    user = auth_service.create_user(
        username=user_req.username,
        password=user_req.password,
        role=user_req.role,
        created_by_user_id=current_user.id,
        ip_address=ip_address
    )
    
    return UserResponse.from_orm(user)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    获取指定用户信息（仅管理员）
    
    需要管理员权限
    """
    user = crud.get_user_by_id(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.from_orm(user)

@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: Request,
    user_req: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    更新用户信息（仅管理员）
    
    需要管理员权限
    
    - **is_active**: 是否激活用户
    - **role**: 角色（admin 或 user）
    """
    ip_address = get_client_ip(request)
    
    # 获取用户
    user = crud.get_user_by_id(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止管理员禁用自己
    if user.id == current_user.id and user_req.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己的账户"
        )
    
    # 防止管理员修改自己的角色
    if user.id == current_user.id and user_req.role is not None and user_req.role != user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改自己的角色"
        )
    
    # 更新字段
    if user_req.is_active is not None:
        user.is_active = user_req.is_active
    
    if user_req.role is not None:
        user.role = user_req.role
    
    # 保存更新
    crud.update_user(db, user)
    
    # 记录审计日志
    changes = []
    if user_req.is_active is not None:
        changes.append(f"is_active={user_req.is_active}")
    if user_req.role is not None:
        changes.append(f"role={user_req.role}")
    
    crud.create_audit_log(
        db,
        action="update_user",
        success=True,
        user_id=current_user.id,
        resource=str(user.id),
        ip_address=ip_address,
        details=", ".join(changes)
    )
    
    return UserResponse.from_orm(user)

@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    删除用户（仅管理员）
    
    需要管理员权限
    
    注意：无法删除自己的账户
    """
    ip_address = get_client_ip(request)
    
    # 获取用户
    user = crud.get_user_by_id(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止管理员删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    # 删除用户
    crud.delete_user(db, user)
    
    # 记录审计日志
    crud.create_audit_log(
        db,
        action="delete_user",
        success=True,
        user_id=current_user.id,
        resource=str(user_id),
        ip_address=ip_address,
        details=f"删除用户: {user.username}"
    )
    
    return MessageResponse(message="用户删除成功")
