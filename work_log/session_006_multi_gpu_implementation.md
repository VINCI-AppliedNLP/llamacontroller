# LlamaController 实施日志 - Session 006: 多GPU支持实现

## 日期
2025-11-12

## 目标
实现2 GPU支持增强功能，允许用户选择在GPU 0、GPU 1或两个GPU上加载模型

## 已完成工作

### 1. 配置模型更新 ✅

#### 文件: `src/llamacontroller/models/config.py`

**新增类**:
- `GpuPortsConfig`: GPU端口映射配置
  - `gpu0`: 8081 (GPU 0的端口)
  - `gpu1`: 8088 (GPU 1的端口)
  - `both`: 8081 (使用两个GPU时的端口)

- `GpuConfig`: 模型的GPU配置
  - `mode`: "single" 或 "both"
  - `gpu_id`: 当mode为"single"时使用的GPU ID (0或1)

**更新的类**:
- `LlamaCppConfig`: 
  - 添加了 `gpu_ports: GpuPortsConfig` 字段
  - `default_port` 现在标记为已弃用

- `ModelParameters`:
  - `get_cli_arguments()` 方法现在接受 `gpu_id` 参数
  - 自动添加 `--tensor-split` 参数:
    - GPU 0: `--tensor-split 1,0`
    - GPU 1: `--tensor-split 0,1`
    - Both: `--tensor-split 0.5,0.5`

- `ModelConfig`:
  - 添加了可选的 `gpu_config: Optional[GpuConfig]` 字段

### 2. 配置文件更新 ✅

#### 文件: `config/llamacpp-config.yaml`

添加了GPU端口映射:
```yaml
gpu_ports:
  gpu0: 8081
  gpu1: 8088
  both: 8081
```

### 3. 适配器更新 ✅

#### 文件: `src/llamacontroller/core/adapter.py`

**更新的方法**:
- `start_server()`:
  - 添加了 `gpu_id: Optional[Union[int, str]]` 参数
  - 将GPU ID传递给 `params.get_cli_arguments(gpu_id=gpu_id)`
  - 自动处理GPU特定的tensor-split参数

**导入更新**:
- 添加了 `Union` 到typing导入

## 待完成工作

### 阶段1: 核心多实例支持

#### 1.1 更新生命周期管理器 (高优先级)
**文件**: `src/llamacontroller/core/lifecycle.py`

需要重大重构以支持多个GPU实例:

```python
class GpuInstance:
    """单个GPU实例的状态"""
    gpu_id: Union[int, str]  # 0, 1, or "both"
    port: int
    adapter: LlamaCppAdapter
    model_id: str
    model_config: ModelConfig
    load_time: datetime

class ModelLifecycleManager:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.gpu_instances: Dict[Union[int, str], GpuInstance] = {}
        # gpu_instances可能包含:
        # {0: GpuInstance, 1: GpuInstance} 或
        # {"both": GpuInstance}
    
    async def load_model(
        self, 
        model_id: str, 
        gpu_id: Union[int, str] = 0
    ) -> LoadModelResponse:
        """在指定GPU上加载模型"""
        # 1. 验证gpu_id有效 (0, 1, 或 "both")
        # 2. 检查该GPU是否已经加载了模型
        # 3. 如果是"both"模式，检查GPU 0和1是否都空闲
        # 4. 确定端口 (从config.llama_cpp.gpu_ports)
        # 5. 创建新的LlamaCppAdapter实例
        # 6. 启动服务器，传递gpu_id
        # 7. 创建并存储GpuInstance
        # 8. 返回LoadModelResponse
    
    async def unload_model(
        self, 
        gpu_id: Union[int, str]
    ) -> UnloadModelResponse:
        """从指定GPU卸载模型"""
        # 1. 检查gpu_id是否有实例
        # 2. 停止适配器
        # 3. 从gpu_instances中移除
    
    async def get_status(self) -> ModelStatus:
        """获取所有GPU的状态"""
        # 返回所有GPU实例的状态
    
    async def get_gpu_status(
        self, 
        gpu_id: Union[int, str]
    ) -> Optional[GpuInstanceStatus]:
        """获取特定GPU的状态"""
    
    async def get_all_gpu_statuses(self) -> Dict[str, GpuInstanceStatus]:
        """获取所有GPU的状态字典"""
    
    def get_port_for_gpu(self, gpu_id: Union[int, str]) -> int:
        """根据GPU ID获取端口"""
        if gpu_id == 0:
            return self.config_manager.llama_cpp.gpu_ports.gpu0
        elif gpu_id == 1:
            return self.config_manager.llama_cpp.gpu_ports.gpu1
        elif gpu_id == "both":
            return self.config_manager.llama_cpp.gpu_ports.both
    
    def get_gpu_for_model(self, model_id: str) -> Optional[Union[int, str]]:
        """查找哪个GPU加载了指定模型"""
        for gpu_id, instance in self.gpu_instances.items():
            if instance.model_id == model_id:
                return gpu_id
        return None
```

**关键变化**:
- 从单适配器改为多适配器架构
- 每个GPU实例有自己的适配器和HTTP客户端
- 需要跟踪哪个GPU加载了哪个模型
- 支持同时运行多个llama-server进程

#### 1.2 更新生命周期模型
**文件**: `src/llamacontroller/models/lifecycle.py`

需要添加:
```python
class GpuInstanceStatus(BaseModel):
    """单个GPU实例的状态"""
    gpu_id: Union[int, str]
    port: int
    model_id: Optional[str]
    model_name: Optional[str]
    status: ProcessStatus
    loaded_at: Optional[datetime]
    uptime_seconds: Optional[int]
    pid: Optional[int]

class AllGpuStatus(BaseModel):
    """所有GPU的状态"""
    gpu0: Optional[GpuInstanceStatus]
    gpu1: Optional[GpuInstanceStatus]
    both: Optional[GpuInstanceStatus]
```

### 阶段2: API端点更新

#### 2.1 更新管理API
**文件**: `src/llamacontroller/api/management.py`

**需要修改的端点**:

```python
@router.post("/api/v1/models/load")
async def load_model(request: LoadModelRequest):
    # LoadModelRequest需要添加gpu_id字段
    # 调用lifecycle_manager.load_model(model_id, gpu_id)

@router.post("/api/v1/models/unload")
async def unload_model(request: UnloadModelRequest):
    # UnloadModelRequest需要添加gpu_id字段
    # 调用lifecycle_manager.unload_model(gpu_id)

@router.get("/api/v1/models/status")
async def get_model_status():
    # 返回所有GPU的状态

# 新端点
@router.get("/api/v1/gpu/status")
async def get_gpu_statuses():
    """获取所有GPU状态"""
    return await lifecycle_manager.get_all_gpu_statuses()

@router.get("/api/v1/gpu/{gpu_id}/status")
async def get_gpu_status(gpu_id: Union[int, str]):
    """获取特定GPU状态"""
    return await lifecycle_manager.get_gpu_status(gpu_id)
```

#### 2.2 更新API模型
**文件**: `src/llamacontroller/models/api.py`

```python
class LoadModelRequest(BaseModel):
    model_id: str
    gpu_id: Union[int, str] = 0  # 默认GPU 0

class UnloadModelRequest(BaseModel):
    gpu_id: Union[int, str]  # 指定要卸载的GPU

class SwitchModelRequest(BaseModel):
    model_id: str
    gpu_id: Union[int, str] = 0  # 指定要切换到的GPU
```

#### 2.3 更新Ollama API路由
**文件**: `src/llamacontroller/api/ollama.py`

需要实现请求路由逻辑:
```python
async def route_to_correct_gpu(model_id: str) -> int:
    """确定哪个GPU有此模型并返回端口"""
    gpu_id = lifecycle_manager.get_gpu_for_model(model_id)
    if gpu_id is None:
        raise HTTPException(404, "Model not loaded on any GPU")
    return lifecycle_manager.get_port_for_gpu(gpu_id)
```

### 阶段3: Web UI更新

#### 3.1 更新Dashboard模板
**文件**: `src/llamacontroller/web/templates/dashboard.html`

需要添加GPU选择控件:
```html
<form hx-post="/dashboard/load-model" ...>
    <select name="model_id">...</select>
    <select name="gpu_id">
        <option value="0">GPU 0</option>
        <option value="1">GPU 1</option>
        <option value="both">Both GPUs</option>
    </select>
    <button type="submit">Load</button>
</form>
```

#### 3.2 更新模型状态显示
**文件**: `src/llamacontroller/web/templates/partials/model_status.html`

显示每个GPU的状态:
```html
<div class="gpu-status">
    <h3>GPU 0 (Port 8081)</h3>
    {% if gpu0_status %}
        <p>Model: {{ gpu0_status.model_name }}</p>
        <p>Status: {{ gpu0_status.status }}</p>
        <button hx-post="/dashboard/unload-model" 
                hx-vals='{"gpu_id": 0}'>Unload</button>
    {% else %}
        <p>No model loaded</p>
    {% endif %}
</div>

<div class="gpu-status">
    <h3>GPU 1 (Port 8088)</h3>
    <!-- 类似内容 -->
</div>
```

#### 3.3 更新Web路由
**文件**: `src/llamacontroller/web/routes.py`

```python
@router.post("/dashboard/load-model")
async def load_model(
    request: Request,
    model_id: str = Form(...),
    gpu_id: str = Form("0"),  # 新增
    current_user: User = Depends(get_current_user)
):
    # 转换gpu_id ("0", "1", "both")
    gpu_param = int(gpu_id) if gpu_id in ["0", "1"] else "both"
    await lifecycle_manager.load_model(model_id, gpu_param)
    # ...

@router.post("/dashboard/unload-model")
async def unload_model(
    request: Request,
    gpu_id: str = Form(...),  # 新增
    current_user: User = Depends(get_current_user)
):
    gpu_param = int(gpu_id) if gpu_id in ["0", "1"] else "both"
    await lifecycle_manager.unload_model(gpu_param)
    # ...
```

### 阶段4: 测试

#### 4.1 单元测试
- 测试GPU配置解析
- 测试端口映射逻辑
- 测试tensor-split参数生成

#### 4.2 集成测试
- 测试在GPU 0上加载模型
- 测试在GPU 1上加载模型
- 测试在两个GPU上加载模型
- 测试同时在不同GPU上加载不同模型
- 测试从特定GPU卸载模型
- 测试API请求路由到正确的GPU

#### 4.3 端到端测试
- 测试完整的Web UI工作流
- 测试Ollama API兼容性

### 阶段5: 文档更新

#### 5.1 用户文档
- 更新QUICKSTART.md
- 添加GPU选择指南
- 添加配置示例

#### 5.2 API文档
- 更新API端点文档
- 添加GPU参数说明

## 技术注意事项

### 端口冲突处理
- GPU 0: 8081
- GPU 1: 8088
- Both: 8081 (与GPU 0共享，因为是单一进程)

### 进程管理
- 每个GPU实例需要独立的LlamaCppAdapter
- 每个适配器管理自己的subprocess.Popen
- 每个适配器有自己的HTTP client指向不同端口

### 状态管理
- gpu_instances字典的key可以是int或str
- "both"模式使用单一实例，占用GPU 0的端口
- 需要验证GPU可用性（不能同时加载GPU 0和"both"）

### HTTP客户端
- 每个适配器的httpx.AsyncClient指向不同端口
- 需要正确的清理和关闭

## 实现优先级

1. **高优先级** (核心功能):
   - [x] 配置模型更新
   - [ ] 生命周期管理器重构
   - [ ] API模型更新
   - [ ] 管理API端点更新

2. **中优先级** (用户界面):
   - [ ] Web UI更新
   - [ ] Ollama API路由

3. **低优先级** (增强):
   - [ ] 内存监控
   - [ ] GPU负载均衡
   - [ ] 自动GPU选择

## 当前状态

**已完成**: 
- ✅ 配置基础设施 (模型、YAML)
- ✅ 适配器GPU参数支持

**进行中**:
- ⏳ 生命周期管理器重构 (下一步)

**未开始**:
- ⏳ API端点更新
- ⏳ Web UI更新
- ⏳ 测试
- ⏳ 文档

**项目总体进度**: 
- Phase 1-5: 100%
- Multi-GPU Enhancement: 25%

---

**会话时间**: 2025-11-12 21:01 - 进行中  
**主要成果**: 完成配置模型和适配器的GPU支持基础  
**下一步**: 重构生命周期管理器以支持多GPU实例
