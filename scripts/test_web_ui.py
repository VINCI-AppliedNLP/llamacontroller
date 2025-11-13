"""
测试Web UI模板和路由
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.web.routes import router as web_router

def test_web_routes():
    """测试Web UI路由是否正确注册"""
    print("检查Web UI路由...")
    
    routes = web_router.routes
    route_paths = [route.path for route in routes]
    
    expected_routes = [
        "/",
        "/login",
        "/logout",
        "/dashboard",
        "/dashboard/load-model",
        "/dashboard/unload-model",
        "/dashboard/switch-model",
        "/tokens",
        "/tokens/create",
        "/tokens/{token_id}",
        "/logs",
        "/logs/refresh"
    ]
    
    print(f"\n已注册的路由: {len(route_paths)}")
    for path in route_paths:
        status = "✓" if path in expected_routes else "?"
        print(f"  {status} {path}")
    
    missing = set(expected_routes) - set(route_paths)
    if missing:
        print(f"\n⚠️ 缺少的路由: {missing}")
    else:
        print("\n✓ 所有预期路由已注册")

def test_templates():
    """测试模板文件是否存在"""
    print("\n检查模板文件...")
    
    template_dir = Path("src/llamacontroller/web/templates")
    
    expected_templates = [
        "base.html",
        "login.html",
        "dashboard.html",
        "tokens.html",
        "logs.html",
        "partials/model_status.html",
        "partials/token_list.html",
        "partials/logs_content.html"
    ]
    
    for template in expected_templates:
        filepath = template_dir / template
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✓ {template} ({size} bytes)")
        else:
            print(f"  ✗ {template} (缺失)")

def main():
    """运行所有测试"""
    print("=" * 50)
    print("Web UI 测试")
    print("=" * 50)
    
    try:
        test_web_routes()
        test_templates()
        
        print("\n" + "=" * 50)
        print("测试完成!")
        print("=" * 50)
        print("\n下一步:")
        print("1. 初始化数据库: python scripts/init_db.py")
        print("2. 启动服务器: python run.py")
        print("3. 访问: http://localhost:3000")
        print("4. 使用默认凭据登录: admin / admin123")
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
