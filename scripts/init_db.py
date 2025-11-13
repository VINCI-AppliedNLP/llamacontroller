"""
初始化数据库脚本

创建所有数据库表并创建初始管理员用户
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from llamacontroller.db.base import init_db, get_db
from llamacontroller.auth.utils import hash_password
from llamacontroller.db import crud

def create_default_admin():
    """创建默认管理员用户"""
    db = next(get_db())
    
    try:
        # 检查是否已存在管理员
        admin = crud.get_user_by_username(db, "admin")
        
        if admin is not None:
            print("✓ 管理员用户已存在")
            return
        
        # 创建默认管理员
        default_password = "admin123"
        password_hash = hash_password(default_password)
        
        admin = crud.create_user(
            db,
            username="admin",
            password_hash=password_hash,
            role="admin"
        )
        
        print(f"✓ 创建管理员用户: {admin.username}")
        print(f"  默认密码: {default_password}")
        print("  ⚠️  请立即修改默认密码！")
        
    except Exception as e:
        print(f"✗ 创建管理员失败: {e}")
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("=== LlamaController 数据库初始化 ===\n")
    
    # 确保 data 目录存在
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"✓ 数据目录: {data_dir}")
    
    # 初始化数据库（创建所有表）
    try:
        init_db()
        print("✓ 数据库表创建成功")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        return 1
    
    # 创建默认管理员
    try:
        create_default_admin()
    except Exception as e:
        print(f"✗ 创建默认用户失败: {e}")
        return 1
    
    print("\n=== 初始化完成 ===")
    print("\n下一步:")
    print("1. 启动服务器: python -m src.llamacontroller.main")
    print("2. 使用默认凭据登录: admin / admin123")
    print("3. 立即修改默认密码")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
