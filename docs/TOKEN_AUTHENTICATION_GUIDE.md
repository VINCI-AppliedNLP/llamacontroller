# Token认证使用指南

## 概述

LlamaController实现了完整的Token认证系统，允许多用户通过API Token安全访问llama.cpp服务。

## 架构

```
客户端应用
  ↓
Authorization: Bearer llc_xxx (用户Token)
  ↓
LlamaController (localhost:3000)
  ├─ Token验证 ✓
  ├─ 权限检查 ✓
  └─ 代理请求
      ↓
  Authorization: Bearer <internal-key> (可选)
      ↓
llama.cpp server (localhost:8080)
  └─ 只监听localhost
```

## 配置llama.cpp API Key（可选）

### 1. 编辑配置文件

编辑 `config/llamacpp-config.yaml`:

```yaml
llama_cpp:
  executable_path: "C:\\path\\to\\llama-server.exe"
  default_host: "127.0.0.1"
  default_port: 8080
  
  # 启用llama-server内部认证（可选，推荐生产环境）
  api_key: "your-secure-internal-key-2024"
  
  # 或者不启用（开发环境）
  # api_key: null
  
  log_level: "info"
  restart_on_crash: true
  max_restart_attempts: 3
  timeout_seconds: 300
```

### 2. 何时使用llama.cpp API Key

**推荐启用（设置api_key）：**
- ✅ 生产环境
- ✅ 多租户部署
- ✅ 需要额外安全层

**可以不启用（api_key: null）：**
- ✅ 开发测试环境
- ✅ llama-server只监听localhost
- ✅ 已经有防火墙保护

### 3. 安全说明

- **llama.cpp API key**: 仅用于LlamaController与llama-server之间的内部通信
- **用户不需要知道**: 这个key对用户透明
- **用户使用LlamaController tokens**: 格式为 `llc_xxx`

## 创建和使用API Token

### 方法1: 通过Web UI创建

1. 登录Web UI: `http://localhost:3000/login`
   ```
   用户名: admin
   密码: admin123
   ```

2. 访问Token管理页面: `http://localhost:3000/tokens`

3. 点击"Create New Token"按钮

4. 填写信息:
   - **Name**: Token名称（例如：my-app-token）
   - **Expires Days**: 过期天数（1-365），留空则永不过期

5. 复制生成的Token（只显示一次！）
   ```
   llc_a7f3e9d2c1b4f8e6d5a3c9b7e4f2d8c6a1b5c9
   ```

### 方法2: 通过API创建

```bash
# 首先登录获取session
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 使用session创建token
curl -X POST http://localhost:3000/api/v1/tokens \
  -H "Cookie: session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"my-api-token","expires_days":30}'
```

## 使用Token访问API

### Ollama兼容API

所有Ollama API端点都需要Token认证：

```bash
# 文本生成
curl -X POST http://localhost:3000/api/generate \
  -H "Authorization: Bearer llc_your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi-4-reasoning",
    "prompt": "Hello, how are you?",
    "stream": false
  }'

# 聊天补全
curl -X POST http://localhost:3000/api/chat \
  -H "Authorization: Bearer llc_your_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi-4-reasoning",
    "messages": [
      {"role": "user", "content": "What is AI?"}
    ]
  }'

# 列出模型
curl http://localhost:3000/api/tags \
  -H "Authorization: Bearer llc_your_token_here"
```

### Python示例

```python
import requests

# 配置
BASE_URL = "http://localhost:3000"
API_TOKEN = "llc_your_token_here"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# 文本生成
response = requests.post(
    f"{BASE_URL}/api/generate",
    headers=headers,
    json={
        "model": "phi-4-reasoning",
        "prompt": "Explain quantum computing",
        "stream": False
    }
)

print(response.json())
```

### JavaScript/Node.js示例

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:3000';
const API_TOKEN = 'llc_your_token_here';

const headers = {
  'Authorization': `Bearer ${API_TOKEN}`,
  'Content-Type': 'application/json'
};

// 聊天补全
axios.post(`${BASE_URL}/api/chat`, {
  model: 'phi-4-reasoning',
  messages: [
    { role: 'user', content: 'What is machine learning?' }
  ]
}, { headers })
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

## Token管理

### 列出所有Token

```bash
curl http://localhost:3000/api/v1/tokens \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

### 停用Token

```bash
curl -X PATCH http://localhost:3000/api/v1/tokens/1 \
  -H "Cookie: session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

### 删除Token

```bash
curl -X DELETE http://localhost:3000/api/v1/tokens/1 \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

## 错误处理

### 常见错误

**401 Unauthorized - 缺少Token**
```json
{
  "detail": "Missing authorization header. Use: Authorization: Bearer <token>"
}
```
解决：添加Authorization header

**401 Unauthorized - Token无效**
```json
{
  "detail": "Invalid or expired token"
}
```
解决：检查Token是否正确，或创建新Token

**401 Unauthorized - Token过期**
```json
{
  "detail": "Invalid or expired token"
}
```
解决：创建新Token

**403 Forbidden - 无权限**
```json
{
  "detail": "User not active"
}
```
解决：联系管理员激活账户

## 安全最佳实践

### 1. Token安全

✅ **DO:**
- 将Token存储在环境变量中
- 使用HTTPS（生产环境）
- 定期轮换Token
- 为每个应用创建独立Token
- 设置合理的过期时间

❌ **DON'T:**
- 不要在代码中硬编码Token
- 不要在Git中提交Token
- 不要在URL中传递Token
- 不要共享Token

### 2. llama.cpp API Key安全

✅ **DO:**
- 使用强随机密钥
- 只在配置文件中存储
- 不要对外暴露
- 定期更换（需要重启服务）

❌ **DON'T:**
- 不要使用简单密码
- 不要在日志中打印
- 不要提交到版本控制

### 3. 网络安全

✅ **DO:**
- llama-server只监听127.0.0.1
- 使用防火墙限制访问
- 考虑使用反向代理（Nginx/Caddy）
- 启用HTTPS

## 与Ollama的兼容性

### 相同点

- ✅ API端点兼容（/api/generate, /api/chat等）
- ✅ 请求/响应格式兼容
- ✅ 可以使用Ollama客户端库

### 不同点

- ⚠️ **需要Token认证**: Ollama默认无认证，LlamaController要求Token
- ⚠️ **Authorization Header**: 必须添加 `Authorization: Bearer llc_xxx`

### 适配Ollama客户端

大多数Ollama客户端支持设置headers：

```python
# Python ollama库
import ollama

client = ollama.Client(
    host='http://localhost:3000',
    headers={'Authorization': 'Bearer llc_your_token_here'}
)

response = client.generate(
    model='phi-4-reasoning',
    prompt='Hello!'
)
```

## 监控和审计

### 查看Token使用情况

Token的`last_used_at`字段会自动更新：

```bash
curl http://localhost:3000/api/v1/tokens \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

响应示例：
```json
{
  "tokens": [
    {
      "id": 1,
      "name": "my-app-token",
      "created_at": "2025-11-12T10:00:00Z",
      "last_used_at": "2025-11-12T17:30:00Z",
      "expires_at": null,
      "is_active": true
    }
  ],
  "total": 1
}
```

### 审计日志

所有API调用都会记录到审计日志（如果启用）。

## 故障排除

### Token无法使用

1. 检查Token格式：应以`llc_`开头
2. 检查Token是否激活：`is_active: true`
3. 检查Token是否过期：`expires_at`
4. 检查用户是否激活：联系管理员

### llama-server连接失败

1. 检查llama-server是否运行
2. 检查端口是否正确（默认8080）
3. 如果启用了API key，检查配置是否正确

### 权限错误

- Web UI需要session cookie
- API调用需要Bearer token
- 不能混用（session不能用于API，token不能用于WebUI）

## 总结

### Token验证流程

1. 用户在Web UI创建Token（`llc_xxx`）
2. 客户端应用使用Token调用API
3. LlamaController验证Token
4. 验证通过后，代理请求到llama-server
5. 如果llama-server启用了API key，自动添加内部key
6. 返回结果给客户端

### 双层认证

```
外层：用户Token (llc_xxx)
  ├─ 多用户支持
  ├─ 可追踪使用
  ├─ 可独立撤销
  └─ 灵活的权限控制

内层：llama.cpp API Key (可选)
  ├─ 内部通信保护
  ├─ 固定key
  ├─ 需重启更改
  └─ 额外安全层
```

---

**文档版本**: 1.0  
**创建日期**: 2025-11-12  
**更新日期**: 2025-11-12
