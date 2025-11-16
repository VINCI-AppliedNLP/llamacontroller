# 进程注册管理 (Process Registry Management)

## 概述

进程注册管理系统提供了对 llama-server 进程的持久化跟踪和管理能力，即使在 LlamaController 重启后也能恢复进程信息，并能检测和清理孤立进程。

## 功能特性

### 1. 进程持久化跟踪

- 自动记录每个 llama-server 进程的详细信息（PID、模型信息、GPU ID、端口等）
- 使用 JSON 文件（`data/processes.json`）持久化存储进程注册信息
- 支持原子化文件写入，确保数据完整性

### 2. 崩溃恢复

- LlamaController 启动时自动恢复已注册的进程信息
- 验证进程是否仍在运行
- 自动清理无效的注册记录

### 3. 孤立进程检测

- 自动检测未被 LlamaController 跟踪的 llama-server 进程
- 提供 API 端点手动清理孤立进程

### 4. 进程验证

- 实时验证进程是否仍在运行
- 确认进程是否为 llama-server 进程

## API 端点

### 获取进程注册表

**端点**: `GET /api/v1/process-registry`

**描述**: 获取所有已注册进程的信息

**响应示例**:
```json
{
  "processes": {
    "0": {
      "pid": 12345,
      "model_id": "llama-7b",
      "model_name": "Llama 2 7B",
      "model_path": "/path/to/model.gguf",
      "gpu_id": "0",
      "port": 8080,
      "started_at": "2025-11-16T15:00:00Z",
      "command_line": ["llama-server", "-m", "/path/to/model.gguf", ...],
      "status": "running"
    }
  }
}
```

### 清理孤立进程

**端点**: `POST /api/v1/cleanup-orphaned`

**描述**: 检测并清理孤立的 llama-server 进程

**参数**:
- `force` (bool, 可选): 是否立即使用 SIGKILL。默认为 false（先尝试 SIGTERM）

**响应示例**:
```json
{
  "success": true,
  "orphaned_pids": [12346, 12347],
  "killed_count": 2,
  "message": "Cleaned up 2 orphaned processes"
}
```

## 使用示例

### Python 示例

```python
import requests

# 设置 API 基础 URL 和认证
base_url = "http://localhost:8000"
headers = {"Authorization": "Bearer YOUR_TOKEN"}

# 获取进程注册表
response = requests.get(f"{base_url}/api/v1/process-registry", headers=headers)
processes = response.json()["processes"]

for gpu_id, process in processes.items():
    print(f"GPU {gpu_id}: PID {process['pid']}, Model {process['model_name']}")

# 清理孤立进程
response = requests.post(
    f"{base_url}/api/v1/cleanup-orphaned",
    params={"force": False},
    headers=headers
)
result = response.json()
print(f"Cleaned up {result['killed_count']} orphaned processes")
```

### cURL 示例

```bash
# 获取进程注册表
curl -X GET "http://localhost:8000/api/v1/process-registry" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 清理孤立进程（温和方式）
curl -X POST "http://localhost:8000/api/v1/cleanup-orphaned?force=false" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 强制清理孤立进程
curl -X POST "http://localhost:8000/api/v1/cleanup-orphaned?force=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 测试

使用提供的测试脚本验证功能：

```bash
# 运行进程注册测试
python scripts/test_process_registry.py
```

测试脚本将：
1. 初始化进程注册表
2. 验证已注册的进程
3. 检测孤立进程
4. 获取 GPU 状态
5. （可选）加载模型并验证注册

## 工作原理

### 进程注册流程

1. **模型加载时**:
   - LlamaController 启动 llama-server 进程
   - 获取进程 PID
   - 创建 `ProcessRegistryEntry` 对象
   - 保存到 `data/processes.json`

2. **模型卸载时**:
   - 终止 llama-server 进程
   - 从注册表中移除该条目
   - 更新 `data/processes.json`

3. **启动时恢复**:
   - 读取 `data/processes.json`
   - 验证每个进程是否仍在运行
   - 清理无效的注册记录
   - 恢复有效进程的状态

### 孤立进程检测

1. 扫描系统中所有进程
2. 识别名称为 "llama-server" 的进程
3. 检查该进程是否在注册表中
4. 返回未注册的进程列表

### 进程终止策略

- **温和模式** (`force=False`):
  1. 发送 SIGTERM 信号
  2. 等待 5 秒
  3. 如果进程仍在运行，发送 SIGKILL

- **强制模式** (`force=True`):
  - 直接发送 SIGKILL 信号

## 注意事项

1. **权限要求**: 清理孤立进程需要有权限终止这些进程
2. **数据完整性**: 进程注册文件使用原子写入，防止数据损坏
3. **跨平台兼容**: 使用 psutil 库确保跨平台兼容性
4. **安全性**: 所有 API 端点都需要认证

## 故障排查

### 问题：进程注册文件损坏

如果 `data/processes.json` 文件损坏：

```bash
# 备份损坏的文件
mv data/processes.json data/processes.json.backup

# 重启 LlamaController，将创建新的注册文件
python run.py
```

### 问题：无法清理孤立进程

如果无法清理孤立进程，尝试：

1. 使用强制模式：`force=true`
2. 手动终止进程：
   ```bash
   # Windows
   taskkill /PID <pid> /F
   
   # Linux/Mac
   kill -9 <pid>
   ```

### 问题：进程验证失败

如果进程验证持续失败：

1. 检查 llama-server 进程是否正常运行
2. 查看日志文件确认错误原因
3. 尝试卸载并重新加载模型

## 相关文件

- **实现**: `src/llamacontroller/core/process_registry.py`
- **集成**: `src/llamacontroller/core/lifecycle.py`
- **API**: `src/llamacontroller/api/management.py`
- **数据**: `data/processes.json`
- **测试**: `scripts/test_process_registry.py`
- **设计文档**: `design/09-process-registry-management.md`
