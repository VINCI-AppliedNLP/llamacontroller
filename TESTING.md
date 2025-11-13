# LlamaController Testing Guide

本文档说明如何测试 LlamaController 的 llama.cpp 集成功能。

## 前提条件

1. **已安装 llama.cpp**
   - 路径配置在 `config/llamacpp-config.yaml`
   - 默认: `C:\Users\VHASLCShiJ\software\llamacpp\llama-server.exe`

2. **已下载模型文件**
   - GGUF 格式模型
   - 路径配置在 `config/models-config.yaml`
   - 默认位置: `C:\Users\VHASLCShiJ\software\ggufmodels\`

3. **Python 环境**
   ```bash
   conda activate llama.cpp
   pip install -r requirements.txt
   ```

## 测试层级

### Level 1: 配置测试 (最快)

验证配置文件加载正确:

```bash
python tests/test_lifecycle.py
```

**预期输出:**
```
Running basic tests...
✓ Lifecycle manager initialized
✓ Found 2 configured models:
  - phi-4-reasoning: Phi-4 Reasoning Plus
  - qwen3-coder-30b: Qwen3 Coder 30B Instruct
✓ Status: stopped
✓ Health: not healthy

Basic tests passed!
```

### Level 2: 演示脚本 (快速预览)

查看配置和可用模型,但不实际启动:

```bash
python scripts/demo_llama_execution.py
```

输入 `no` 可以退出而不启动服务器。

### Level 3: 完整集成测试 (推荐) ⭐

**实际启动 llama-server 并测试推理:**

```bash
python scripts/test_llama_inference.py
```

这个脚本会:

1. ✅ 加载配置
2. ✅ 列出可用模型
3. ✅ 询问确认(输入 `yes` 继续)
4. ✅ 启动 llama-server 子进程
5. ✅ 等待服务器就绪
6. ✅ 执行健康检查
7. ✅ 发送 HTTP 推理请求
8. ✅ 显示生成的文本
9. ✅ 保持服务器运行供手动测试
10. ✅ Ctrl+C 后优雅关闭

**预期输出示例:**

```
======================================================================
LlamaController - Full Integration Test
This will actually load llama-server and test inference
======================================================================

📋 Step 1: Loading configuration...
✓ llama-server: C:\Users\...\llama-server.exe
✓ Endpoint: http://127.0.0.1:8080

🔧 Step 2: Initializing lifecycle manager...
✓ Ready

📦 Step 3: Found 2 configured models
   - phi-4-reasoning: Phi-4 Reasoning Plus
   - qwen3-coder-30b: Qwen3 Coder 30B Instruct

🎯 Step 4: Will use model: phi-4-reasoning

⚠️  WARNING: This will actually start llama-server and load the model.
   Model file: C:\Users\...\Phi-4-reasoning-plus-UD-IQ1_M.gguf
   Size: ~3.57 GB (for Phi-4)

Continue? (yes/no): yes

🚀 Step 5: Loading model and starting llama-server...
----------------------------------------------------------------------

✅ llama-server started successfully!
   PID: 12345
   Status: running
   Endpoint: http://127.0.0.1:8080

🏥 Step 6: Health check...
✓ Server is healthy (uptime: 3s)

📜 Recent server logs:
   llama_model_load: loaded model...
   llama_new_context_with_model: KV cache created...
   server listening on 127.0.0.1:8080

======================================================================
🧪 Step 7: Testing Inference
======================================================================

📤 Sending completion request to /completion...
   Prompt: 'Once upon a time'
   URL: http://127.0.0.1:8080/completion
   Waiting for response...

✓ Response received (Status: 200)

📥 Completion Response:
----------------------------------------------------------------------
Prompt: Once upon a time
Generated: , in a land far away, there lived a brave knight...
----------------------------------------------------------------------

✅ INFERENCE TEST PASSED!
   llama.cpp is working correctly!

======================================================================
🔍 Step 8: Server Status After Inference
======================================================================
   Model: Phi-4 Reasoning Plus
   Status: running
   Uptime: 15s
   PID: 12345

======================================================================
✨ Server is still running!
======================================================================

You can now test manually:
   curl http://127.0.0.1:8080/health
   curl http://127.0.0.1:8080/completion -d '{"prompt":"Hello","n_predict":20}'

Press Ctrl+C when done testing...

   [Running] Uptime: 20s | Status: running
   [Running] Uptime: 25s | Status: running
   ...
```

## 手动测试命令

当服务器运行时,可以使用以下 curl 命令测试:

### 健康检查

```bash
curl http://127.0.0.1:8080/health
```

### 文本补全

```bash
curl http://127.0.0.1:8080/completion \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "The meaning of life is",
    "n_predict": 50,
    "temperature": 0.7
  }'
```

### Windows PowerShell

```powershell
# 健康检查
Invoke-WebRequest -Uri http://127.0.0.1:8080/health

# 文本补全
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8080/completion `
  -ContentType "application/json" `
  -Body '{"prompt":"Hello, my name is","n_predict":20}'
```

## 故障排除

### 问题: 服务器启动失败

**可能原因:**
- llama-server.exe 路径不正确
- 模型文件不存在
- 端口 8080 已被占用

**解决方案:**
1. 检查 `config/llamacpp-config.yaml` 中的路径
2. 验证模型文件存在: `dir C:\Users\...\ggufmodels\*.gguf`
3. 更改端口号(在配置文件中)

### 问题: 健康检查失败

**可能原因:**
- 服务器仍在加载模型
- 模型太大,内存不足

**解决方案:**
- 等待更长时间(大模型需要几分钟)
- 使用更小的模型测试
- 检查系统内存

### 问题: 推理请求超时

**可能原因:**
- 第一次请求,模型仍在初始化
- GPU 层配置不当

**解决方案:**
- 增加超时时间
- 调整 `n_gpu_layers` 参数
- 使用更小的 `n_predict` 值

## 性能提示

1. **GPU 加速**: 设置 `n_gpu_layers > 0` (需要 CUDA/Metal 支持)
2. **线程数**: 调整 `n_threads` 匹配 CPU 核心数
3. **上下文窗口**: 较小的 `n_ctx` 使用更少内存

## 下一步

测试通过后,可以:

1. 实现 REST API 层 (Phase 3)
2. 添加 Ollama 兼容端点
3. 构建 Web UI
4. 添加认证系统

---

**文档版本**: 1.0  
**最后更新**: 2025-11-12
