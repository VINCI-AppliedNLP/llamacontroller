"""
令牌管理 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from llamacontroller.api.dependencies import get_db
from llamacontroller.auth.dependencies import get_current_user
from llamacontroller.db import crud
from llamacontroller.db.models import User
from llamacontroller.models.auth import (
    CreateTokenRequest,
    UpdateTokenRequest,
    TokenResponse,
    TokenListResponse,
    MessageResponse
)

router = APIRouter(prefix="/api/v1/tokens", tags=["令牌管理"])

def get_client_ip(request: Request) -> str | None:
    """获取客户端 IP 地址"""
    return request.client.host if request.client else None

@router.get("", response_model=TokenListResponse)
async def list_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取当前用户的所有 API 令牌
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    """
    tokens = crud.get_user_api_tokens(db, current_user.id)
    
    return TokenListResponse(
        tokens=[TokenResponse.from_orm(token) for token in tokens],
        total=len(tokens)
    )

@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    request: Request,
    token_req: CreateTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建新的 API 令牌
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    
    - **name**: 令牌名称（用于标识）
    - **expires_days**: 过期天数（1-365），可选，不设置则永不过期
    
    返回的令牌只会显示一次，请妥善保存
    """
    ip_address = get_client_ip(request)
    
    # 创建令牌
    token, raw_token = crud.create_api_token(
        db,
        user_id=current_user.id,
        name=token_req.name,
        expires_days=token_req.expires_days
    )
    
    # 记录审计日志
    crud.create_audit_log(
        db,
        action="create_token",
        success=True,
        user_id=current_user.id,
        resource=str(token.id),
        ip_address=ip_address,
        details=f"令牌名称: {token_req.name}"
    )
    
    # 返回响应（包含原始令牌）
    response = TokenResponse.from_orm(token)
    response.token = raw_token
    
    return response

@router.patch("/{token_id}", response_model=TokenResponse)
async def update_token(
    token_id: int,
    request: Request,
    token_req: UpdateTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新 API 令牌（启用/禁用）
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    
    - **is_active**: 是否激活令牌
    """
    ip_address = get_client_ip(request)
    
    # 获取令牌
    token = crud.get_api_token_by_id(db, token_id)
    
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="令牌不存在"
        )
    
    # 检查权限（只能修改自己的令牌）
    if token.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此令牌"
        )
    
    # 更新令牌
    token.is_active = token_req.is_active
    crud.update_api_token(db, token)
    
    # 记录审计日志
    crud.create_audit_log(
        db,
        action="update_token",
        success=True,
        user_id=current_user.id,
        resource=str(token.id),
        ip_address=ip_address,
        details=f"设置 is_active={token_req.is_active}"
    )
    
    return TokenResponse.from_orm(token)

@router.delete("/{token_id}", response_model=MessageResponse)
async def delete_token(
    token_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除 API 令牌
    
    需要通过 Cookie 或 X-Session-ID 头提供会话 ID
    """
    ip_address = get_client_ip(request)
    
    # 获取令牌
    token = crud.get_api_token_by_id(db, token_id)
    
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="令牌不存在"
        )
    
    # 检查权限（只能删除自己的令牌）
    if token.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此令牌"
        )
    
    # 删除令牌
    crud.delete_api_token(db, token)
    
    # 记录审计日志
    crud.create_audit_log(
        db,
        action="delete_token",
        success=True,
        user_id=current_user.id,
        resource=str(token_id),
        ip_address=ip_address
    )
    
    return MessageResponse(message="令牌删除成功")
