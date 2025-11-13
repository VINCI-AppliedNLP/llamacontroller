"""
创建测试 API token 并显示完整值
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llamacontroller.db.base import SessionLocal
from llamacontroller.db import crud

def main():
    db = SessionLocal()
    try:
        # Create a token for admin user (ID: 1)
        print("创建新的 API token...")
        token_obj, raw_token = crud.create_api_token(
            db,
            user_id=1,
            name="curl-test-token",
            expires_days=30
        )
        
        print(f"\n✅ Token 创建成功！")
        print(f"Token 名称: {token_obj.name}")
        print(f"Token ID: {token_obj.id}")
        print(f"\n⚠️  完整 Token (请复制并保存):")
        print(f"{raw_token}")
        print(f"\n使用示例:")
        print(f'curl -H "Authorization: Bearer {raw_token}" http://127.0.0.1:3000/api/v1/models/status')
        print(f"\n注意: 此 token 只显示一次，请妥善保存！\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
