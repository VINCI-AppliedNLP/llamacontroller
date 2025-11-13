# Multi-GPU String Format Design

## 概述
将GPU ID从特殊值"both"改为逗号分隔的字符串格式,以支持未来扩展到更多GPU。

## 当前设计 (需要更改)
- GPU 0: `gpu_id = 0`
- GPU 1: `gpu_id = 1`
- 两个GPU: `gpu_id = "both"`

## 新设计 (建议)
- GPU 0: `gpu_id = "0"` 或 `gpu_id = 0` (兼容)
- GPU 1: `gpu_id = "1"` 或 `gpu_id = 1` (兼容)
- GPU 0和1: `gpu_id = "0,1"`
- 未来GPU 0,2,3: `gpu_id = "0,2,3"`

## 类型定义变更

### Union[int, str] → str
```python
# 旧: gpu_id: Union[int, str]  # 0, 1, or "both"
# 新: gpu_id: str  # "0", "1", "0,1", "0,1,2", etc.
```

## 实现变更

### 1. 验证函数
```python
def _validate_gpu_id(self, gpu_id: str) -> List[int]:
    """
    验证并解析GPU ID字符串
    
    Args:
        gpu_id: GPU ID字符串 (如 "0", "1", "0,1", "0,1,2")
        
    Returns:
        GPU ID列表 [0], [1], [0, 1], etc.
        
    Raises:
        LifecycleError: GPU ID无效
    """
    # 支持向后兼容
    if isinstance(gpu_id, int):
        gpu_id = str(gpu_id)
    
    try:
        # 解析逗号分隔的ID
        gpu_ids = [int(x.strip()) for x in gpu_id.split(',')]
        
        # 验证范围 (当前仅支持0-1,未来可扩展)
        for gid in gpu_ids:
            if gid < 0 or gid > 7:  # 预留到8个GPU
                raise ValueError(f"GPU ID {gid} out of range (0-7)")
        
        # 检查重复
        if len(gpu_ids) != len(set(gpu_ids)):
            raise ValueError("Duplicate GPU IDs")
        
        return sorted(gpu_ids)
    except ValueError as e:
        raise LifecycleError(f"Invalid gpu_id '{gpu_id}': {e}")
```

### 2. 端口映射策略

**选项A: 基于主GPU (推荐)**
```python
def get_port_for_gpu(self, gpu_id: str) -> int:
    """根据GPU ID获取端口,使用主GPU(第一个)的端口"""
    gpu_list = self._validate_gpu_id(gpu_id)
    primary_gpu = gpu_list[0]
    
    # 端口映射: GPU 0->8081, GPU 1->8088, etc.
    return 8081 + (primary_gpu * 7)  # 每个GPU间隔7个端口
```

**选项B: 预定义多GPU端口**
```python
class GpuPortsConfig(BaseModel):
    """GPU端口映射"""
    default_ports: Dict[int, int] = {
        0: 8081,
        1: 8088,
        2: 8095,
        # ...
    }
    multi_gpu_port: int = 8081  # 多GPU使用第一个GPU的端口
```

### 3. tensor-split生成
```python
def get_tensor_split(self, gpu_ids: List[int]) -> str:
    """
    生成tensor-split参数
    
    Args:
        gpu_ids: GPU ID列表 [0, 1] or [0, 2, 3]
        
    Returns:
        tensor-split字符串 "0.5,0.5" or "0.33,0,0.33,0.34"
    """
    max_gpu = max(gpu_ids)
    splits = [0.0] * (max_gpu + 1)
    
    # 平均分配
    split_value = 1.0 / len(gpu_ids)
    for gid in gpu_ids:
        splits[gid] = split_value
    
    return ','.join(f"{s:.2f}" for s in splits)

# 示例:
# [0, 1] → "0.50,0.50"
# [0, 2] → "0.50,0.00,0.50"
# [0, 1, 2] → "0.33,0.33,0.34"
```

### 4. 字典键策略
```python
# 旧: gpu_instances: Dict[Union[int, str], GpuInstance]
# 新: gpu_instances: Dict[str, GpuInstance]

# 键格式: "0", "1", "0,1", "0,1,2"
gpu_instances = {
    "0": GpuInstance(...),      # GPU 0单独
    "1": GpuInstance(...),      # GPU 1单独
    "0,1": GpuInstance(...),    # GPU 0和1
}
```

### 5. 冲突检测
```python
def _check_gpu_conflicts(self, gpu_id: str) -> None:
    """检查GPU冲突"""
    requested_gpus = set(self._validate_gpu_id(gpu_id))
    
    for existing_key, instance in self.gpu_instances.items():
        existing_gpus = set(self._validate_gpu_id(existing_key))
        
        # 检查是否有重叠
        if requested_gpus & existing_gpus:
            conflict_gpus = requested_gpus & existing_gpus
            raise LifecycleError(
                f"GPU conflict: GPU(s) {conflict_gpus} already in use by '{existing_key}'"
            )
```

## API示例

```json
// 加载到GPU 0
{
  "model_id": "phi-4",
  "gpu_id": "0"
}

// 加载到GPU 1
{
  "model_id": "qwen-coder",
  "gpu_id": "1"
}

// 加载到GPU 0和1
{
  "model_id": "large-model",
  "gpu_id": "0,1"
}

// 未来: 加载到GPU 0,2,3
{
  "model_id": "huge-model",
  "gpu_id": "0,2,3"
}
```

## 配置文件变更

```yaml
# 旧格式
gpu_ports:
  gpu0: 8081
  gpu1: 8088
  both: 8081

# 新格式 (选项A - 简单)
gpu_ports:
  base_port: 8081
  port_offset: 7  # 每个GPU +7

# 或 (选项B - 灵活)
gpu_ports:
  "0": 8081
  "1": 8088
  "2": 8095
  "3": 8102
```

## 迁移路径

### 阶段1: 向后兼容
- 同时支持 `Union[int, str]`
- "both" → "0,1" 自动转换
- 整数自动转字符串

### 阶段2: 仅字符串
- 移除整数支持
- 弃用"both"
- 文档更新

## 优势

✅ **可扩展**: 轻松支持8+ GPU  
✅ **灵活**: 任意GPU组合 (0,2 / 1,3 / 0,1,2,3)  
✅ **直观**: "0,1,2"比"triple"更清晰  
✅ **向后兼容**: 支持渐进迁移  
✅ **标准化**: 使用逗号分隔是常见格式

## 实施优先级

1. **高**: 核心类型和验证函数
2. **高**: 生命周期管理器更新
3. **中**: API端点更新
4. **中**: 配置文件更新
5. **低**: Web UI更新
6. **低**: 文档和示例

---

**建议**: 立即实施此设计,替代当前的"both"方案
