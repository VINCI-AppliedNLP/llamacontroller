# LlamaController 快速启动指南

本指南帮助你快速启动并测试 LlamaController API。

## 前提条件

1. **Python 环境**
   ```bash
   conda activate llama.cpp
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置文件**
   确保以下配置文件存在：
   - `config/llamacpp-config.yaml`
   - `config/models-config.yaml`
   - `config/auth-config.yaml`

## 启动服务器

### 方法 1: 使用 Python 模块
```bash
python -m src.llamacontroller.main
```

### 方法 2: 使用 uvicorn 直接运行
```bash
uvicorn src.llamacontroller.main:app --host 0.0.0.0 --port 3000 --reload
```

服务器将在 http://localhost:3000 启动

## 访问 API 文档

启动服务器后，访问以下 URL：

- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc
- **OpenAPI JSON**: http://localhost:3000/openapi.json

## 测试 API 端点

### 1. 基础健康检查

```bash
# 应用健康检查
curl http://localhost:3000/health

# 模型健康检查
curl http://localhost:3000/api/v1/health
```

### 2. 列出可用模型

```bash
# LlamaController API
curl http://localhost:3000/api/v1/models

# Ollama 兼容 API
curl http://localhost:3000/api/tags
```

### 3. 加载模型

```bash
curl -X POST http://localhost:3000/api/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "phi-4-reasoning"}'
```

### 4. 获取模型状态

```bash
curl http://localhost:3000/api/v1/models/status
```

### 5. 切换模型

```bash
curl -X POST http://localhost:3000/api/v1/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_id": "qwen3-coder-30b"}'
```

### 6. 文本生成（Ollama 兼容）

```bash
# 非流式
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi-4-reasoning",
    "prompt": "What is the capital of France?",
    "stream": false
  }'

# 流式
curl -X POST http://localhost:3000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi-4-reasoning",
    "prompt": "Write a short story",
    "stream": true
  }'
```

### 7. 聊天补全（Ollama 兼容）

```bash
curl -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "phi-4-reasoning",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "stream": false
  }'
```

### 8. 查看运行中的模型

```bash
# Ollama 兼容
curl http://localhost:3000/api/ps
```

### 9. 卸载模型

```bash
curl -X POST http://localhost:3000/api/v1/models/unload
```

### 10. 获取服务器日志

```bash
curl http://localhost:3000/api/v1/logs?lines=50
```

## 使用 Python 客户端

### 基础示例

```python
import requests

BASE_URL = "http://localhost:3000"

# 列出模型
response = requests.get(f"{BASE_URL}/api/v1/models")
print(response.json())

# 加载模型
response = requests.post(
    f"{BASE_URL}/api/v1/models/load",
    json={"model_id": "phi-4-reasoning"}
)
print(response.json())

# 获取状态
response = requests.get(f"{BASE_URL}/api/v1/models/status")
print(response.json())
```

### Ollama 兼容示例

```python
import requests

BASE_URL = "http://localhost:3000"

# 文本生成
response = requests.post(
    f"{BASE_URL}/api/generate",
    json={
        "model": "phi-4-reasoning",
        "prompt": "Explain quantum computing",
        "stream": False
    }
)
print(response.json())

# 聊天
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "model": "phi-4-reasoning",
        "messages": [
            {"role": "user", "content": "What is Python?"}
        ],
        "stream": False
    }
)
print(response.json())
```

### 流式响应示例

```python
import requests

response = requests.post(
    "http://localhost:3000/api/generate",
    json={
        "model": "phi-4-reasoning",
        "prompt": "Write a poem about AI",
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行 API 测试
pytest tests/test_api.py -v

# 运行特定测试
pytest tests/test_api.py::TestManagementAPI::test_list_models_empty -v

# 查看测试覆盖率
pytest --cov=src/llamacontroller --cov-report=html
```

## 常见问题

### 1. 服务器启动失败

**问题**: `Failed to initialize managers`

**解决方案**:
- 检查配置文件是否存在于 `./config/` 目录
- 验证 YAML 文件格式正确
- 确保 llama.cpp 可执行文件路径正确

### 2. 模型加载失败

**问题**: `Model not found`

**解决方案**:
- 检查模型 ID 是否在 `models-config.yaml` 中定义
- 验证模型文件路径是否正确
- 确保模型文件存在

### 3. llama.cpp 连接失败

**问题**: `llama.cpp error: Connection refused`

**解决方案**:
- 确认 llama-server 正在运行
- 检查端口配置（默认 8080）
- 查看 llama-server 日志

### 4. CORS 错误

**问题**: 浏览器中出现 CORS 错误

**解决方案**:
- 当前 CORS 配置允许所有来源
- 如需限制，修改 `src/llamacontroller/main.py` 中的 CORS 配置

## 下一步

1. **探索 API 文档**: 访问 http://localhost:3000/docs
2. **测试模型切换**: 尝试在不同模型间切换
3. **集成到应用**: 使用 Ollama 兼容 API 集成到现有应用
4. **配置认证**: 准备 Phase 4 认证功能（即将推出）

## 生产部署建议

1. **使用反向代理** (Nginx/Caddy)
2. **启用 HTTPS**
3. **配置环境变量**
4. **限制 CORS 来源**
5. **启用认证**（Phase 4）
6. **设置日志轮转**
7. **配置监控和告警**

## 支持

遇到问题？查看：
- [架构文档](../design/04-architecture.md)
- [实施指南](../design/05-implementation-guide.md)
- [测试最佳实践](../design/06-testing-best-practices.md)
- [工作日志](../work_log/)
