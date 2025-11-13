# 访问 llama-server Web 界面

当你加载一个模型后，llama-server 会自动启动并提供一个内置的 Web 聊天界面。

## 快速开始

### 1. 启动 LlamaController

```bash
python run.py
```

服务器将在 `http://localhost:3000` 启动。

### 2. 检查 llama-server 状态

访问根端点查看当前状态：

```bash
curl http://localhost:3000/
```

**未加载模型时的响应**:
```json
{
  "name": "LlamaController",
  "version": "0.1.0",
  "description": "llama.cpp model lifecycle management with Ollama API compatibility",
  "endpoints": {
    "management": "/api/v1",
    "ollama_compatible": "/api",
    "docs": "/docs",
    "openapi": "/openapi.json"
  },
  "llama_server": {
    "status": "stopped",
    "message": "Load a model to start llama-server"
  }
}
```

### 3. 加载模型

使用管理 API 加载模型：

```bash
curl -X POST http://localhost:3000/api/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "phi-4-reasoning"}'
```

或使用 PowerShell：

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:3000/api/v1/models/load `
  -ContentType "application/json" `
  -Body '{"model_id":"phi-4-reasoning"}'
```

### 4. 获取 llama-server URL

模型加载后，再次查看根端点：

```bash
curl http://localhost:3000/
```

**模型加载后的响应**:
```json
{
  "name": "LlamaController",
  "version": "0.1.0",
  "description": "llama.cpp model lifecycle management with Ollama API compatibility",
  "endpoints": {
    "management": "/api/v1",
    "ollama_compatible": "/api",
    "docs": "/docs",
    "openapi": "/openapi.json"
  },
  "llama_server": {
    "status": "running",
    "url": "http://127.0.0.1:8080",
    "web_interface": "http://127.0.0.1:8080",
    "model": "Phi-4 Reasoning Plus"
  }
}
```

### 5. 访问 Web 界面

在浏览器中打开显示的 URL：

```
http://127.0.0.1:8080
```

这将打开 llama.cpp 的内置聊天界面，您可以直接与模型交互！

---

## 其他获取 URL 的方式

### 方式 1: 查看模型状态端点

```bash
curl http://localhost:3000/api/v1/models/status
```

响应示例：
```json
{
  "model_id": "phi-4-reasoning",
  "model_name": "Phi-4 Reasoning Plus",
  "status": "running",
  "loaded_at": "2025-11-12T18:30:00.000000",
  "memory_usage_mb": null,
  "uptime_seconds": 45.5,
  "pid": 12345,
  "host": "127.0.0.1",
  "port": 8080,
  "server_url": "http://127.0.0.1:8080"
}
```

### 方式 2: 使用 Swagger UI

1. 访问 `http://localhost:3000/docs`
2. 找到 `GET /` 端点
3. 点击 "Try it out" 和 "Execute"
4. 查看响应中的 `llama_server.web_interface`

### 方式 3: 使用 Python 脚本

```python
import requests

response = requests.get("http://localhost:3000/")
data = response.json()

if data["llama_server"]["status"] == "running":
    url = data["llama_server"]["web_interface"]
    print(f"llama-server 正在运行: {url}")
    print(f"当前模型: {data['llama_server']['model']}")
else:
    print("llama-server 未运行")
    print(data["llama_server"]["message"])
```

---

## llama-server Web 界面功能

当你访问 llama-server 的 web 界面时，你可以：

- ✅ **实时聊天**: 直接与加载的模型对话
- ✅ **调整参数**: 修改温度、top-p、top-k 等参数
- ✅ **查看令牌**: 实时查看生成的令牌数
- ✅ **性能指标**: 查看推理速度和延迟
- ✅ **上下文管理**: 查看和管理对话上下文

---

## 端口配置

默认端口是 `8080`。如需修改，编辑 `config/llamacpp-config.yaml`:

```yaml
default_host: "127.0.0.1"
default_port: 8080  # 修改为其他端口
```

---

## 故障排除

### 问题: URL 显示但无法访问

**可能原因**:
- 模型仍在加载中
- 防火墙阻止了连接
- 端口被其他程序占用

**解决方案**:
1. 等待几秒钟让模型完全加载
2. 检查防火墙设置
3. 使用健康检查验证: `curl http://127.0.0.1:8080/health`

### 问题: llama_server 状态为 stopped

**解决方案**:
1. 确认模型已加载: `curl http://localhost:3000/api/v1/models/status`
2. 检查模型文件路径是否正确
3. 查看 LlamaController 日志: `logs/app.log`

### 问题: 想要更改模型

**解决方案**:
```bash
# 切换到另一个模型
curl -X POST http://localhost:3000/api/v1/models/switch \
  -H "Content-Type: application/json" \
  -d '{"model_id": "qwen3-coder-30b"}'
```

---

## 完整工作流程示例

```bash
# 1. 启动 LlamaController
python run.py

# 2. 在另一个终端，加载模型
curl -X POST http://localhost:3000/api/v1/models/load \
  -H "Content-Type: application/json" \
  -d '{"model_id": "phi-4-reasoning"}'

# 3. 获取 llama-server URL
curl http://localhost:3000/ | grep web_interface

# 4. 在浏览器中打开 http://127.0.0.1:8080

# 5. 开始聊天！
```

---

## 相关文档

- [API 测试报告](./API_TEST_REPORT.md) - 完整的 API 端点文档
- [快速开始指南](./QUICKSTART.md) - 项目设置和配置
- [测试指南](../TESTING.md) - 完整的集成测试

---

**文档更新**: 2025-11-12  
**版本**: 1.0
