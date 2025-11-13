# Token验证和API代理设计文档

## 问题分析

### 发现的问题

1. **Web UI Token创建功能正常**
   - ✅ Token可以在Web UI (`/tokens`)中成功创建
   - ✅ Token存储在数据库中
   - ✅ Token在界面上正确显示

2. **llama.cpp的API Key限制**
   - ⚠️ llama-server在启动时通过`--api-key`参数设置API密钥
   - ⚠️ 一旦启动，API密钥无法动态更改
   - ⚠️ 这与LlamaController的多Token设计冲突

3. **缺少Token验证层（安全漏洞）**
   - ❌ Ollama兼容API端点(`/api/generate`, `/api/chat`等)当前**没有**Token验证
   - ❌ 请求直接代理到llama.cpp，绕过了认证系统
   - ❌ 任何人都可以访问这些端点

### 当前架构问题

```
问题架构:
客户端请求 → Ollama API端点 → 直接代理到llama.cpp（无验证❌）
                ↓
          No Authentication!

期望架构:
客户端请求 → Ollama API端点 → Token验证✓ → 代理到llama.cpp
                ↓
        Authorization: Bearer <token>
```

## 解决方案

### 方案1: Token验证代理层（推荐）✅

**实现思路:**
1. 在Ollama API端点添加Token验证依赖
2. 验证用户的API Token（Bearer token）
3. 验证通过后，代理到llama.cpp
4. 如果llama.cpp启用了API key，在代理时替换header

**架构:**
```
客户端 
  ↓
Authorization: Bearer llc_xxx (用户Token)
  ↓
Ollama API端点 (FastAPI)
  ↓
Token验证中间件
  ↓ (验证通过)
代理层
  ↓
Authorization: Bearer <llama-cpp-key> (固定key，可选)
  ↓
llama.cpp server
```

**优点:**
- ✅ 不需要修改llama.cpp
- ✅ 支持多个用户Token
- ✅ 可以按Token记录使用情况
- ✅ 可以按Token限流
- ✅ 灵活的权限控制

**缺点:**
- 需要修改现有代码
- 额外的验证开销（很小）

### 方案2: 不使用llama.cpp的API key（简化方案）

**实现思路:**
- llama.cpp启动时不设置`--api-key`
- 只在LlamaController层进行Token验证
- llama.cpp只监听localhost，不对外暴露

**优点:**
- ✅ 实现简单
- ✅ 不需要处理API key替换

**缺点:**
- ⚠️ 如果llama.cpp端口泄露，可能被直接访问

## 实施计划

### Phase 1: 添加Token验证依赖

**文件:** `src/llamacontroller/auth/dependencies.py`

添加函数:
```python
async def verify_api_token(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    验证API Token (Bearer token)
    
    用于Ollama API端点的认证
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization format. Use: Bearer <token>"
        )
    
    token = authorization[7:]  # Remove "Bearer "
    
    # Verify token
    api_token = crud.verify_api_token(db, token)
    if not api_token:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    # Get user
    user = crud.get_user_by_id(db, api_token.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not active"
        )
    
    # Update last_used_at
    crud.update_token_last_used(db, api_token.id)
    
    return user
```

### Phase 2: 修改Ollama API端点

**文件:** `src/llamacontroller/api/ollama.py`

修改所有端点，添加Token验证:

```python
from ..auth.dependencies import verify_api_token

@router.post("/generate")
async def generate(
    request: GenerateRequest,
    user: User = Depends(verify_api_token),  # 添加Token验证
    lifecycle: ModelLifecycleManager = Depends(verify_model_loaded),
    config: ConfigManager = Depends(get_config_manager)
):
    # ... 现有代码
```

### Phase 3: 更新代理逻辑

**文件:** `src/llamacontroller/api/ollama.py`

如果llama.cpp使用了API key，需要在代理时替换:

```python
async def _proxy_to_llama_cpp(
    endpoint: str,
    method: str,
    config: ConfigManager,
    json_data: dict | None = None,
    stream: bool = False,
    llama_api_key: str | None = None  # 新增参数
) -> httpx.Response:
    """代理请求到llama.cpp"""
    base_url = _get_llama_cpp_url(config)
    url = f"{base_url}{endpoint}"
    
    headers = {}
    if llama_api_key:
        headers["Authorization"] = f"Bearer {llama_api_key}"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        if method.upper() == "POST":
            response = await client.post(
                url, 
                json=json_data,
                headers=headers
            )
        # ...
```

### Phase 4: 配置llama.cpp API Key（可选）

**文件:** `config/llamacpp-config.yaml`

```yaml
llama_cpp:
  executable_path: "C:\\path\\to\\llama-server.exe"
  default_host: "127.0.0.1"
  default_port: 8080
  api_key: "llama-internal-key-2024"  # 可选，内部使用的固定key
  log_level: "info"
```

**文件:** `src/llamacontroller/models/config.py`

```python
class LlamaCppConfig(BaseModel):
    executable_path: str
    default_host: str = "127.0.0.1"
    default_port: int = 8080
    api_key: Optional[str] = None  # 新增
    # ...
```

**文件:** `src/llamacontroller/core/adapter.py`

```python
def start_server(self, model_path: str, params: ModelParameters, ...):
    # ...
    cmd = [
        self.config.executable_path,
        "-m", model_path,
        "--host", host,
        "--port", str(port),
    ]
    
    # 如果配置了API key，添加到命令行
    if self.config.api_key:
        cmd.extend(["--api-key", self.config.api_key])
    
    # ...
```

## 安全考虑

### 1. Token格式
- 使用`llc_`前缀标识LlamaController tokens
- 至少32字节随机性
- 示例: `llc_a7f3e9d2c1b4f8e6d5a3c9b7e4f2d8c6`

### 2. Token存储
- 数据库中只存储Token的hash
- 使用SHA-256哈希
- 原始Token只在创建时显示一次

### 3. llama.cpp API Key
- 只用于内部通信
- 不对外暴露
- 可以设置为空（不启用）

### 4. 网络隔离
- llama.cpp只监听127.0.0.1
- 不直接暴露到外网
- 所有外部访问必须通过LlamaController

## 测试计划

### 1. Token验证测试
```bash
# 测试无Token访问（应失败）
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"phi-4","prompt":"Hello"}'

# 测试无效Token（应失败）
curl -X POST http://localhost:3000/api/generate \
  -H "Authorization: Bearer invalid_token" \
  -H "Content-Type: application/json" \
  -d '{"model":"phi-4","prompt":"Hello"}'

# 测试有效Token（应成功）
curl -X POST http://localhost:3000/api/generate \
  -H "Authorization: Bearer llc_xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"phi-4","prompt":"Hello"}'
```

### 2. Token管理测试
```bash
# 创建Token
curl -X POST http://localhost:3000/api/v1/tokens \
  -H "Cookie: session_id=xxx" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-token","expires_days":30}'

# 列出Tokens
curl http://localhost:3000/api/v1/tokens \
  -H "Cookie: session_id=xxx"

# 删除Token
curl -X DELETE http://localhost:3000/api/v1/tokens/1 \
  -H "Cookie: session_id=xxx"
```

## 实施优先级

### 必须实现（P0）
1. ✅ Token验证依赖函数
2. ✅ Ollama API端点添加Token验证
3. ✅ 测试Token验证流程

### 推荐实现（P1）
4. ⏳ 添加API使用统计（按Token）
5. ⏳ 添加Token限流
6. ⏳ 审计日志记录API调用

### 可选实现（P2）
7. ⏳ llama.cpp API key支持
8. ⏳ Token权限细分（读/写）
9. ⏳ Token使用配额

## 总结

### 当前状态
- ❌ Ollama API端点无Token验证（安全漏洞）
- ✅ Token创建功能正常
- ✅ Session认证正常（Web UI）

### 解决方案
- 实施Token验证代理层
- 在Ollama API端点添加`verify_api_token`依赖
- llama.cpp使用可选的内部API key
- 只验证LlamaController的Token，内部再转发给llama.cpp

### 预期效果
- ✅ 所有API访问都需要有效Token
- ✅ 支持多用户、多Token
- ✅ 可追踪每个Token的使用情况
- ✅ 灵活的权限和限流控制

---

**文档版本**: 1.0  
**创建日期**: 2025-11-12  
**状态**: 设计阶段
