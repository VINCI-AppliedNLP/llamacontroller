# llama-serve 参数配置指南

本文档说明如何配置 llama-serve 启动参数。

## 概述

LlamaController 支持两种参数配置方式:

1. **新式 `cli_params`** (推荐) - 灵活的参数系统,直接使用 llama-serve 原生参数名
2. **旧式结构化参数** (已弃用) - 向后兼容,但功能受限

## 推荐方式: `cli_params`

### 基本用法

在 `config/models-config.yaml` 中使用 `cli_params` 字段:

```yaml
models:
  - id: "my-model"
    name: "My Model"
    path: "/path/to/model.gguf"
    parameters:
      cli_params:
        c: 24000              # 上下文大小
        ngl: 33               # GPU 层数
        t: 8                  # 线程数
        temp: 0.7             # 采样温度
        top-p: 0.9            # Top-p 采样
```

### 参数类型

#### 1. 键值对参数

大多数参数采用键值对形式:

```yaml
cli_params:
  c: 24000                    # 数字
  temp: 0.7                   # 浮点数
  model-draft: "/path/to/draft.gguf"  # 字符串
```

生成的命令行:
```bash
--c 24000 --temp 0.7 --model-draft /path/to/draft.gguf
```

#### 2. 布尔标志参数

不需要值的开关参数,使用 `null`:

```yaml
cli_params:
  context-shift: null         # 启用上下文转移
  no-mmap: null               # 禁用内存映射
  mlock: null                 # 锁定模型在 RAM 中
```

生成的命令行:
```bash
--context-shift --no-mmap --mlock
```

**注意**: YAML 中 `null` 值表示布尔标志。如果您想使用空列表 `[]`,效果相同。

#### 3. 多值参数

某些参数可以有多个值(如 LoRA 适配器):

```yaml
cli_params:
  lora: ["adapter1.bin", "adapter2.bin"]
```

生成的命令行:
```bash
--lora adapter1.bin --lora adapter2.bin
```

### 完整示例

```yaml
models:
  - id: "phi-4-advanced"
    name: "Phi-4 Advanced Configuration"
    path: "C:\\models\\phi-4.gguf"
    parameters:
      cli_params:
        # 基本参数
        c: 32768              # 上下文大小
        ngl: 40               # GPU 层数
        t: 16                 # CPU 线程数
        
        # 采样参数
        temp: 0.8
        top-p: 0.95
        top-k: 50
        repeat-penalty: 1.15
        
        # 性能优化
        context-shift: null   # 启用上下文转移
        flash-attn: null      # Flash attention
        mlock: null           # 锁定内存
        
        # 高级参数
        rope-freq-base: 10000
        rope-freq-scale: 1.0
        yarn-ext-factor: 1.0
```

## 常用参数参考

### 核心参数

| 参数 | 简写 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| `ctx-size` | `c` | 整数 | 上下文窗口大小 | `c: 16384` |
| `n-gpu-layers` | `ngl` | 整数 | 加载到 GPU 的层数 | `ngl: 35` |
| `threads` | `t` | 整数 | CPU 线程数 | `t: 8` |
| `predict` | `n` | 整数 | 生成的最大 token 数 | `n: 512` |

### 采样参数

| 参数 | 类型 | 范围 | 说明 | 示例 |
|------|------|------|------|------|
| `temp` | 浮点 | 0.0-2.0 | 采样温度,越高越随机 | `temp: 0.7` |
| `top-p` | 浮点 | 0.0-1.0 | Nucleus sampling | `top-p: 0.9` |
| `top-k` | 整数 | ≥0 | Top-k 采样 | `top-k: 40` |
| `repeat-penalty` | 浮点 | ≥0.0 | 重复惩罚 | `repeat-penalty: 1.1` |
| `min-p` | 浮点 | 0.0-1.0 | 最小概率阈值 | `min-p: 0.05` |

### 性能优化

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `context-shift` | 标志 | 启用上下文转移(KV 缓存滚动) | `context-shift: null` |
| `flash-attn` | 标志 | 使用 Flash Attention | `flash-attn: null` |
| `no-mmap` | 标志 | 禁用内存映射 | `no-mmap: null` |
| `mlock` | 标志 | 锁定模型在 RAM 中 | `mlock: null` |
| `numa` | 标志 | NUMA 支持 | `numa: null` |

### RoPE 缩放参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `rope-freq-base` | 浮点 | RoPE 频率基数 | `rope-freq-base: 10000` |
| `rope-freq-scale` | 浮点 | RoPE 频率缩放 | `rope-freq-scale: 1.0` |
| `yarn-ext-factor` | 浮点 | YaRN 外推因子 | `yarn-ext-factor: 1.0` |
| `yarn-attn-factor` | 浮点 | YaRN 注意力因子 | `yarn-attn-factor: 1.0` |

## 旧式参数(已弃用)

为了向后兼容,仍然支持旧式参数:

```yaml
parameters:
  n_ctx: 8192
  n_gpu_layers: 0
  n_threads: 8
  temperature: 0.8
  top_p: 0.95
  top_k: 40
  repeat_penalty: 1.1
```

**不推荐使用**,因为:
- 功能受限,不支持所有 llama-serve 参数
- 无法使用布尔标志
- 参数名与 llama-serve 不一致

## 混合使用

可以混合使用两种方式,`cli_params` 优先:

```yaml
parameters:
  # 旧式参数作为后备
  n_ctx: 8192
  n_threads: 8
  
  # cli_params 会覆盖旧式参数
  cli_params:
    c: 16384              # 覆盖 n_ctx
    context-shift: null   # 新功能
```

## 验证配置

启动模型后,检查日志中的命令行:

```
Starting llama-server: llama-server -m /path/to/model.gguf --host 127.0.0.1 --port 8080 --c 24000 --ngl 33 --t 8 --temp 0.7 --top-p 0.9 --context-shift
```

## 最佳实践

1. **使用短参数名**: `c` 而不是 `ctx-size`,更简洁
2. **布尔标志用 `null`**: 清晰表示无值参数
3. **添加注释**: 帮助理解每个参数的作用
4. **根据硬件调整**: 
   - GPU 内存充足: 增加 `ngl`
   - RAM 有限: 使用 `no-mmap`
   - CPU 核心多: 增加 `t`
5. **上下文大小**: 根据模型支持和任务需求设置 `c`

## 故障排查

### 模型加载失败
- 检查 `ngl` 是否超过 GPU VRAM 容量
- 尝试减少 `c` (上下文大小)
- 使用 `no-mmap` 如果内存映射有问题

### 性能问题
- 启用 `context-shift` 处理长上下文
- 增加 `ngl` 使用更多 GPU
- 调整 `t` (线程数)匹配 CPU 核心

### 参数不生效
- 检查 YAML 格式是否正确
- 确认使用 `cli_params` 字段
- 查看启动日志中的完整命令行

## 参考资源

- [llama.cpp 官方文档](https://github.com/ggerganov/llama.cpp)
- [llama-server 参数说明](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md)
