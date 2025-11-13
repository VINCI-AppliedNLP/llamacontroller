"""
测试认证相关的 API 端点
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:3000"

def print_response(title: str, response: requests.Response):
    """打印响应信息"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")

def test_auth_endpoints():
    """测试认证端点"""
    print("\n" + "="*60)
    print("测试认证 API 端点")
    print("="*60)
    
    session_id: Optional[str] = None
    api_token: Optional[str] = None
    user_id: Optional[int] = None
    token_id: Optional[int] = None
    
    # 1. 测试登录（使用默认管理员账户）
    print("\n1. 测试用户登录")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print_response("POST /api/v1/auth/login", response)
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")
        print(f"✓ 登录成功，Session ID: {session_id}")
    else:
        print("✗ 登录失败")
        return
    
    # 2. 测试获取当前用户信息
    print("\n2. 测试获取当前用户信息")
    headers = {"X-Session-ID": session_id}
    cookies = {"session_id": session_id}
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers=headers,
        cookies=cookies
    )
    print_response("GET /api/v1/auth/me", response)
    
    if response.status_code == 200:
        print("✓ 获取当前用户信息成功")
    else:
        print("✗ 获取当前用户信息失败")
    
    # 3. 测试创建 API 令牌
    print("\n3. 测试创建 API 令牌")
    response = requests.post(
        f"{BASE_URL}/api/v1/tokens",
        headers=headers,
        cookies=cookies,
        json={"name": "测试令牌", "expires_days": 30}
    )
    print_response("POST /api/v1/tokens", response)
    
    if response.status_code == 201:
        data = response.json()
        api_token = data.get("token")
        token_id = data.get("id")
        print(f"✓ 创建令牌成功，Token: {api_token}")
    else:
        print("✗ 创建令牌失败")
    
    # 4. 测试列出令牌
    print("\n4. 测试列出所有令牌")
    response = requests.get(
        f"{BASE_URL}/api/v1/tokens",
        headers=headers,
        cookies=cookies
    )
    print_response("GET /api/v1/tokens", response)
    
    if response.status_code == 200:
        print("✓ 列出令牌成功")
    else:
        print("✗ 列出令牌失败")
    
    # 5. 测试使用 API 令牌访问
    if api_token:
        print("\n5. 测试使用 API 令牌访问")
        token_headers = {"Authorization": f"Bearer {api_token}"}
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers=token_headers
        )
        print_response("GET /api/v1/auth/me (使用 API Token)", response)
        
        if response.status_code == 200:
            print("✓ API 令牌验证成功")
        else:
            print("✗ API 令牌验证失败")
    
    # 6. 测试禁用令牌
    if token_id:
        print("\n6. 测试禁用令牌")
        response = requests.patch(
            f"{BASE_URL}/api/v1/tokens/{token_id}",
            headers=headers,
            cookies=cookies,
            json={"is_active": False}
        )
        print_response(f"PATCH /api/v1/tokens/{token_id}", response)
        
        if response.status_code == 200:
            print("✓ 禁用令牌成功")
        else:
            print("✗ 禁用令牌失败")
    
    # 7. 测试修改密码
    print("\n7. 测试修改密码")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/change-password",
        headers=headers,
        cookies=cookies,
        json={"old_password": "admin123", "new_password": "newpass123"}
    )
    print_response("POST /api/v1/auth/change-password", response)
    
    if response.status_code == 200:
        print("✓ 修改密码成功")
        # 改回原密码
        requests.post(
            f"{BASE_URL}/api/v1/auth/change-password",
            headers=headers,
            cookies=cookies,
            json={"old_password": "newpass123", "new_password": "admin123"}
        )
    else:
        print("✗ 修改密码失败")
    
    # 8. 测试创建用户（管理员功能）
    print("\n8. 测试创建用户（管理员）")
    response = requests.post(
        f"{BASE_URL}/api/v1/users",
        headers=headers,
        cookies=cookies,
        json={"username": "testuser", "password": "testpass123", "role": "user"}
    )
    print_response("POST /api/v1/users", response)
    
    if response.status_code == 201:
        data = response.json()
        user_id = data.get("id")
        print(f"✓ 创建用户成功，User ID: {user_id}")
    else:
        print("✗ 创建用户失败")
    
    # 9. 测试列出所有用户
    print("\n9. 测试列出所有用户（管理员）")
    response = requests.get(
        f"{BASE_URL}/api/v1/users",
        headers=headers,
        cookies=cookies
    )
    print_response("GET /api/v1/users", response)
    
    if response.status_code == 200:
        print("✓ 列出用户成功")
    else:
        print("✗ 列出用户失败")
    
    # 10. 测试获取用户详情
    if user_id:
        print(f"\n10. 测试获取用户详情")
        response = requests.get(
            f"{BASE_URL}/api/v1/users/{user_id}",
            headers=headers,
            cookies=cookies
        )
        print_response(f"GET /api/v1/users/{user_id}", response)
        
        if response.status_code == 200:
            print("✓ 获取用户详情成功")
        else:
            print("✗ 获取用户详情失败")
    
    # 11. 测试更新用户
    if user_id:
        print(f"\n11. 测试更新用户")
        response = requests.patch(
            f"{BASE_URL}/api/v1/users/{user_id}",
            headers=headers,
            cookies=cookies,
            json={"is_active": False}
        )
        print_response(f"PATCH /api/v1/users/{user_id}", response)
        
        if response.status_code == 200:
            print("✓ 更新用户成功")
        else:
            print("✗ 更新用户失败")
    
    # 12. 测试删除令牌
    if token_id:
        print(f"\n12. 测试删除令牌")
        response = requests.delete(
            f"{BASE_URL}/api/v1/tokens/{token_id}",
            headers=headers,
            cookies=cookies
        )
        print_response(f"DELETE /api/v1/tokens/{token_id}", response)
        
        if response.status_code == 200:
            print("✓ 删除令牌成功")
        else:
            print("✗ 删除令牌失败")
    
    # 13. 测试删除用户
    if user_id:
        print(f"\n13. 测试删除用户")
        response = requests.delete(
            f"{BASE_URL}/api/v1/users/{user_id}",
            headers=headers,
            cookies=cookies
        )
        print_response(f"DELETE /api/v1/users/{user_id}", response)
        
        if response.status_code == 200:
            print("✓ 删除用户成功")
        else:
            print("✗ 删除用户失败")
    
    # 14. 测试登出
    print("\n14. 测试用户登出")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/logout",
        headers=headers,
        cookies=cookies
    )
    print_response("POST /api/v1/auth/logout", response)
    
    if response.status_code == 200:
        print("✓ 登出成功")
    else:
        print("✗ 登出失败")
    
    # 15. 测试登出后访问（应该失败）
    print("\n15. 测试登出后访问（应该失败）")
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers=headers,
        cookies=cookies
    )
    print_response("GET /api/v1/auth/me (登出后)", response)
    
    if response.status_code == 401:
        print("✓ 正确拒绝未认证访问")
    else:
        print("✗ 应该拒绝访问但没有")
    
    print("\n" + "="*60)
    print("认证端点测试完成")
    print("="*60)

if __name__ == "__main__":
    try:
        test_auth_endpoints()
    except requests.exceptions.ConnectionError:
        print("\n错误: 无法连接到服务器")
        print("请确保服务器运行在 http://localhost:3000")
        print("\n运行服务器: python run.py")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
