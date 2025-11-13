"""
检查数据库中的 API tokens
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
        # Get all users
        from llamacontroller.db.models import User
        users = db.query(User).all()
        
        print("=== Users and their API Tokens ===\n")
        for user in users:
            print(f"User: {user.username} (ID: {user.id})")
            tokens = crud.get_user_api_tokens(db, user.id)
            
            if tokens:
                for token in tokens:
                    print(f"  - Token Name: {token.name}")
                    print(f"    Token Hash: {token.token_hash[:30]}...")
                    print(f"    Is Active: {token.is_active}")
                    print(f"    Created: {token.created_at}")
                    if token.expires_at:
                        print(f"    Expires: {token.expires_at}")
                    print()
            else:
                print("  No tokens found\n")
    finally:
        db.close()

if __name__ == "__main__":
    main()
