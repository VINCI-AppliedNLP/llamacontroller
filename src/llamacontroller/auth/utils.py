"""
认证工具函数
"""
import bcrypt
from typing import Optional

def hash_password(password: str) -> str:
    """
    使用 bcrypt 哈希密码
    
    Args:
        password: 明文密码
    
    Returns:
        密码哈希值（包含 salt）
    """
    # 生成 salt 并哈希密码
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码
    
    Args:
        password: 明文密码
        password_hash: 存储的密码哈希值
    
    Returns:
        True 如果密码匹配，否则 False
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False

def get_client_ip(request) -> Optional[str]:
    """
    从请求中获取客户端 IP 地址
    
    Args:
        request: FastAPI Request 对象
    
    Returns:
        IP 地址字符串
    """
    # 检查反向代理头
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For 可能包含多个 IP，取第一个
        return forwarded.split(",")[0].strip()
    
    # 检查其他常见的代理头
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接连接的客户端 IP
    if request.client:
        return request.client.host
    
    return None

def get_user_agent(request) -> Optional[str]:
    """
    从请求中获取 User-Agent
    
    Args:
        request: FastAPI Request 对象
    
    Returns:
        User-Agent 字符串
    """
    return request.headers.get("User-Agent")
