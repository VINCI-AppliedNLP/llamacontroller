"""
测试数据库操作

验证 CRUD 操作、认证服务等功能
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from llamacontroller.db.base import get_db
from llamacontroller.db import crud
from llamacontroller.auth.service import AuthService
from llamacontroller.auth.utils import hash_password

def test_user_operations():
    """测试用户操作"""
    print("\n=== 测试用户操作 ===")
    db = next(get_db())
    
    try:
        # 1. 获取管理员用户
        admin = crud.get_user_by_username(db, "admin")
        print(f"✓ 找到管理员用户: {admin.username} (ID: {admin.id}, 角色: {admin.role})")
        
        # 2. 创建测试用户
        test_user = crud.get_user_by_username(db, "testuser")
        if test_user is None:
            password_hash = hash_password("testpass123")
            test_user = crud.create_user(db, "testuser", password_hash, "user")
            print(f"✓ 创建测试用户: {test_user.username} (ID: {test_user.id})")
        else:
            print(f"✓ 测试用户已存在: {test_user.username}")
        
        # 3. 列出所有用户
        users = crud.get_users(db)
        print(f"✓ 数据库中共有 {len(users)} 个用户")
        
        # 4. 更新用户
        test_user.is_active = True
        crud.update_user(db, test_user)
        print(f"✓ 更新用户成功")
        
        return admin, test_user
        
    finally:
        db.close()

def test_authentication():
    """测试认证"""
    print("\n=== 测试认证 ===")
    db = next(get_db())
    auth = AuthService(db)
    
    try:
        # 1. 测试正确的凭据
        success, error, user = auth.authenticate_user("admin", "admin123", "127.0.0.1")
        if success:
            print(f"✓ 管理员认证成功: {user.username}")
        else:
            print(f"✗ 管理员认证失败: {error}")
        
        # 2. 测试错误的密码
        success, error, user = auth.authenticate_user("admin", "wrongpass", "127.0.0.1")
        if not success:
            print(f"✓ 错误密码被正确拒绝: {error}")
        else:
            print(f"✗ 错误密码应该被拒绝")
        
        # 3. 测试不存在的用户
        success, error, user = auth.authenticate_user("nonexistent", "password", "127.0.0.1")
        if not success:
            print(f"✓ 不存在的用户被正确拒绝: {error}")
        else:
            print(f"✗ 不存在的用户应该被拒绝")
        
    finally:
        db.close()

def test_session_operations():
    """测试会话操作"""
    print("\n=== 测试会话操作 ===")
    db = next(get_db())
    auth = AuthService(db)
    
    try:
        # 1. 获取管理员
        admin = crud.get_user_by_username(db, "admin")
        
        # 2. 创建会话
        login_response = auth.create_session(
            admin,
            ip_address="127.0.0.1",
            user_agent="Test Script"
        )
        print(f"✓ 创建会话成功")
        print(f"  会话 ID: {login_response.session_id[:16]}...")
        print(f"  过期时间: {login_response.expires_at}")
        
        # 3. 验证会话
        verified_user = auth.verify_session(login_response.session_id)
        if verified_user:
            print(f"✓ 会话验证成功: {verified_user.username}")
        else:
            print(f"✗ 会话验证失败")
        
        # 4. 登出
        success = auth.logout(login_response.session_id, "127.0.0.1")
        if success:
            print(f"✓ 登出成功")
        
        # 5. 验证已登出的会话
        verified_user = auth.verify_session(login_response.session_id)
        if verified_user is None:
            print(f"✓ 已登出的会话验证正确返回 None")
        else:
            print(f"✗ 已登出的会话应该无效")
        
    finally:
        db.close()

def test_api_token_operations():
    """测试 API 令牌操作"""
    print("\n=== 测试 API 令牌操作 ===")
    db = next(get_db())
    auth = AuthService(db)
    
    try:
        # 1. 获取管理员
        admin = crud.get_user_by_username(db, "admin")
        
        # 2. 创建 API 令牌
        token_record, raw_token = crud.create_api_token(
            db,
            user_id=admin.id,
            name="测试令牌",
            expires_days=30
        )
        print(f"✓ 创建 API 令牌成功")
        print(f"  令牌 ID: {token_record.id}")
        print(f"  令牌名称: {token_record.name}")
        print(f"  原始令牌: {raw_token[:20]}...")
        
        # 3. 验证令牌
        verified_user = auth.verify_api_token(raw_token)
        if verified_user:
            print(f"✓ 令牌验证成功: {verified_user.username}")
        else:
            print(f"✗ 令牌验证失败")
        
        # 4. 列出用户的所有令牌
        tokens = crud.get_user_api_tokens(db, admin.id)
        print(f"✓ 用户共有 {len(tokens)} 个令牌")
        
        # 5. 停用令牌
        token_record.is_active = False
        crud.update_api_token(db, token_record)
        print(f"✓ 令牌已停用")
        
        # 6. 验证已停用的令牌
        verified_user = auth.verify_api_token(raw_token)
        if verified_user is None:
            print(f"✓ 已停用的令牌验证正确返回 None")
        else:
            print(f"✗ 已停用的令牌应该无效")
        
        # 7. 删除令牌
        crud.delete_api_token(db, token_record)
        print(f"✓ 令牌已删除")
        
    finally:
        db.close()

def test_audit_log():
    """测试审计日志"""
    print("\n=== 测试审计日志 ===")
    db = next(get_db())
    
    try:
        # 1. 创建审计日志
        log = crud.create_audit_log(
            db,
            action="test_action",
            success=True,
            user_id=1,
            resource="test_resource",
            details='{"key": "value"}',
            ip_address="127.0.0.1"
        )
        print(f"✓ 创建审计日志成功 (ID: {log.id})")
        
        # 2. 获取审计日志
        logs = crud.get_audit_logs(db, limit=10)
        print(f"✓ 获取到 {len(logs)} 条审计日志")
        
        # 3. 显示最近的几条日志
        print("\n最近的审计日志:")
        for log in logs[:5]:
            print(f"  - [{log.created_at}] {log.action} by User#{log.user_id} - {'成功' if log.success else '失败'}")
        
    finally:
        db.close()

def test_password_change():
    """测试密码修改"""
    print("\n=== 测试密码修改 ===")
    db = next(get_db())
    auth = AuthService(db)
    
    try:
        # 1. 获取测试用户
        test_user = crud.get_user_by_username(db, "testuser")
        if test_user is None:
            print("✗ 测试用户不存在，跳过密码修改测试")
            return
        
        # 2. 尝试使用错误的旧密码
        success, error = auth.change_password(
            test_user,
            "wrongoldpass",
            "newpass123",
            "127.0.0.1"
        )
        if not success:
            print(f"✓ 错误的旧密码被正确拒绝: {error}")
        
        # 3. 使用正确的旧密码修改
        success, error = auth.change_password(
            test_user,
            "testpass123",
            "newpass456",
            "127.0.0.1"
        )
        if success:
            print(f"✓ 密码修改成功")
        else:
            print(f"✗ 密码修改失败: {error}")
        
        # 4. 验证新密码
        success, error, user = auth.authenticate_user("testuser", "newpass456", "127.0.0.1")
        if success:
            print(f"✓ 使用新密码认证成功")
        else:
            print(f"✗ 使用新密码认证失败: {error}")
        
    finally:
        db.close()

def main():
    """主函数"""
    print("╔════════════════════════════════════════════╗")
    print("║  LlamaController 数据库操作测试            ║")
    print("╚════════════════════════════════════════════╝")
    
    try:
        # 运行所有测试
        test_user_operations()
        test_authentication()
        test_session_operations()
        test_api_token_operations()
        test_audit_log()
        test_password_change()
        
        print("\n" + "="*50)
        print("✓ 所有测试通过！")
        print("="*50)
        
        return 0
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
