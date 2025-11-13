"""
完整的 API 端点测试脚本
测试所有管理和 Ollama 兼容端点
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# 配置
BASE_URL = "http://localhost:3000"
TIMEOUT = 5

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

def print_test(endpoint: str, method: str = "GET"):
    """打印测试信息"""
    print(f"{Colors.BLUE}🧪 测试: {Colors.BOLD}{method} {endpoint}{Colors.END}")

def print_success(message: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message: str):
    """打印错误信息"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_json(data: Dict[Any, Any], indent: int = 2):
    """打印 JSON 数据"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))

def test_endpoint(method: str, endpoint: str, expected_status: int = 200, 
                  json_data: Optional[Dict] = None, description: Optional[str] = None) -> bool:
    """
    测试单个端点
    
    Args:
        method: HTTP 方法
        endpoint: 端点路径
        expected_status: 期望的状态码
        json_data: 请求的 JSON 数据
        description: 测试描述
        
    Returns:
        bool: 测试是否通过
    """
    url = f"{BASE_URL}{endpoint}"
    
    if description:
        print(f"\n{Colors.CYAN}📋 {description}{Colors.END}")
    
    print_test(endpoint, method)
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=json_data, timeout=TIMEOUT)
        elif method == "DELETE":
            response = requests.delete(url, json=json_data, timeout=TIMEOUT)
        else:
            print_error(f"不支持的 HTTP 方法: {method}")
            return False
        
        # 检查状态码
        if response.status_code == expected_status:
            print_success(f"状态码: {response.status_code}")
        else:
            print_error(f"状态码: {response.status_code} (期望: {expected_status})")
            return False
        
        # 打印响应
        try:
            data = response.json()
            print_success("响应数据:")
            print_json(data)
            return True
        except:
            print_success(f"响应: {response.text[:200]}")
            return True
            
    except requests.exceptions.Timeout:
        print_error(f"请求超时 (>{TIMEOUT}s)")
        return False
    except requests.exceptions.ConnectionError:
        print_error("连接失败 - 服务器未运行?")
        return False
    except Exception as e:
        print_error(f"错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print_header("LlamaController API 端点测试")
    
    print(f"测试目标: {Colors.BOLD}{BASE_URL}{Colors.END}")
    print(f"超时设置: {TIMEOUT}秒\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # ========== 根端点测试 ==========
    print_header("1. 根端点测试")
    
    tests = [
        ("GET", "/", 200, None, "获取 API 信息"),
        ("GET", "/health", 200, None, "健康检查"),
    ]
    
    for method, endpoint, status, data, desc in tests:
        results["total"] += 1
        if test_endpoint(method, endpoint, status, data, desc):
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)
    
    # ========== 管理 API 测试 ==========
    print_header("2. 管理 API 测试 (/api/v1)")
    
    tests = [
        ("GET", "/api/v1/models", 200, None, "列出所有可用模型"),
        ("GET", "/api/v1/models/status", 200, None, "获取当前模型状态"),
        ("GET", "/api/v1/health", 200, None, "服务器健康检查"),
    ]
    
    for method, endpoint, status, data, desc in tests:
        results["total"] += 1
        if test_endpoint(method, endpoint, status, data, desc):
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)
    
    # ========== Ollama 兼容 API 测试 ==========
    print_header("3. Ollama 兼容 API 测试 (/api)")
    
    tests = [
        ("GET", "/api/tags", 200, None, "列出模型 (Ollama 格式)"),
        ("GET", "/api/ps", 200, None, "列出运行中的模型"),
        ("GET", "/api/version", 200, None, "获取版本信息"),
    ]
    
    for method, endpoint, status, data, desc in tests:
        results["total"] += 1
        if test_endpoint(method, endpoint, status, data, desc):
            results["passed"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)
    
    # POST 请求测试
    print("\n" + "─" * 70)
    results["total"] += 1
    if test_endpoint(
        "POST", 
        "/api/show", 
        404,  # 期望 404,因为模型可能不存在
        {"name": "test-model"},
        "显示模型信息 (不存在的模型)"
    ):
        results["passed"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)
    
    # DELETE 请求测试
    print("\n" + "─" * 70)
    results["total"] += 1
    if test_endpoint(
        "DELETE",
        "/api/delete",
        501,  # 期望 501 Not Implemented
        {"name": "test-model"},
        "删除模型 (未实现)"
    ):
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # ========== 文档端点测试 ==========
    print_header("4. 文档端点测试")
    
    print_test("/docs", "GET")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=TIMEOUT)
        if response.status_code == 200 and "text/html" in response.headers.get("content-type", ""):
            print_success("Swagger UI 可访问")
            results["passed"] += 1
        else:
            print_error(f"Swagger UI 不可用 (状态码: {response.status_code})")
            results["failed"] += 1
    except Exception as e:
        print_error(f"错误: {str(e)}")
        results["failed"] += 1
    results["total"] += 1
    
    time.sleep(0.5)
    
    print("\n" + "─" * 70)
    print_test("/openapi.json", "GET")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if "openapi" in data and "paths" in data:
                print_success("OpenAPI 规范可访问")
                print_success(f"端点数量: {len(data.get('paths', {}))}")
                results["passed"] += 1
            else:
                print_error("OpenAPI 规范格式错误")
                results["failed"] += 1
        else:
            print_error(f"OpenAPI 规范不可用 (状态码: {response.status_code})")
            results["failed"] += 1
    except Exception as e:
        print_error(f"错误: {str(e)}")
        results["failed"] += 1
    results["total"] += 1
    
    # ========== 测试总结 ==========
    print_header("测试总结")
    
    print(f"总测试数: {Colors.BOLD}{results['total']}{Colors.END}")
    print(f"通过: {Colors.GREEN}{Colors.BOLD}{results['passed']}{Colors.END}")
    print(f"失败: {Colors.RED}{Colors.BOLD}{results['failed']}{Colors.END}")
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"成功率: {Colors.BOLD}{success_rate:.1f}%{Colors.END}")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 所有测试通过!{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  有 {results['failed']} 个测试失败{Colors.END}\n")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}")
        exit(130)
