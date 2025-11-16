# Multi-GPU Unload Button Design Fix

## 问题描述

### 问题1: Multi-GPU Unload按钮缺失（已解决）
当使用多个GPU（例如 "0,1"）加载模型后，UI中没有显示unload按钮。

### 问题2: 单GPU卡片显示冲突（当前问题）
当模型加载到多GPU（如"0,1"）后，单独的GPU 0和GPU 1卡片仍然显示为"Idle"状态，这是不正确的。这些GPU实际上已被多GPU模型占用，应该被隐藏或显示为被占用状态。

**示例场景**：
- 加载模型到GPU "0,1"
- 期望：只显示一个Multi-GPU (0,1)卡片
- 实际：显示Multi-GPU (0,1)卡片 + GPU 0 (Idle) + GPU 1 (Idle) ❌
- 正确：只显示Multi-GPU (0,1)卡片 ✅

### 根本原因分析

1. **数据结构不一致**：
   - `lifecycle.py` 中 `gpu_instances` 的键是标准化的GPU ID字符串：`"0"`, `"1"`, `"0,1"`, `"0,1,2"` 等
   - `get_all_gpu_statuses()` 返回的字典键格式为：`"gpu0"`, `"gpu1"`, 但多GPU应该是 `"gpu0,1"`
   - 当前实现错误地使用 `f"gpu{gpu_id}"` 作为键，导致多GPU场景下键为 `"gpu0,1"` 而非预期的格式

2. **模板硬编码问题**：
   - `dashboard_content.html` 中硬编码查找 `gpu_statuses.both`
   - 应该统一使用 `gpu_statuses['gpu0,1']` 格式

3. **显示逻辑分离**：
   - 单GPU和多GPU的状态显示在不同的区域
   - 应该统一在GPU状态卡片中显示

## 设计解决方案

### 方案A: 统一键格式（推荐）

将所有GPU ID统一使用数字格式的键：

**后端变更**：
```python
async def get_all_gpu_statuses(self) -> Dict[str, Optional[GpuInstanceStatus]]:
    """返回所有已加载GPU的状态"""
    result = {}
    
    # 为每个加载的GPU实例返回状态
    for gpu_id in self.gpu_instances.keys():
        # 键格式: "0", "1", "0,1", "0,1,2" (不加"gpu"前缀)
        result[gpu_id] = await self.get_gpu_status(gpu_id)
    
    return result
```

**前端变更**：
```html
<!-- 动态生成所有GPU卡片，包括多GPU组合 -->
{% for gpu_key, gpu_instance in gpu_statuses.items() %}
    {% if gpu_instance %}
    <div class="border rounded-lg p-4 bg-green-50 border-green-200">
        <div class="flex items-center justify-between mb-2">
            <h4 class="font-semibold text-gray-900">
                GPU {{ gpu_key }}
            </h4>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium">Running</span>
        </div>
        <p class="text-sm text-gray-600">Model: {{ gpu_instance.model_name }}</p>
        <p class="text-xs text-gray-500">Port: {{ gpu_instance.port }}</p>
        <form hx-post="/dashboard/unload-model" hx-target="#dashboard-content" hx-disabled-elt="button" class="mt-2">
            <input type="hidden" name="gpu_id" value="{{ gpu_key }}">
            <button type="submit" class="text-sm text-red-600 hover:text-red-800 font-medium">Unload Model</button>
        </form>
    </div>
    {% endif %}
{% endfor %}
```

### 方案B: 保持当前格式，修复多GPU键

如果必须保持 `gpu0`, `gpu1` 格式：

```python
async def get_all_gpu_statuses(self) -> Dict[str, Optional[GpuInstanceStatus]]:
    """返回所有已加载GPU的状态"""
    result = {}
    
    for gpu_id in self.gpu_instances.keys():
        # 为单GPU: "gpu0", "gpu1"
        # 为多GPU: "gpu0,1", "gpu0,1,2"（不变）
        if ',' in gpu_id:
            key = f"gpu{gpu_id}"  # "gpu0,1"
        else:
            key = f"gpu{gpu_id}"  # "gpu0", "gpu1"
        result[key] = await self.get_gpu_status(gpu_id)
    
    return result
```

## 单GPU卡片隐藏逻辑

### 需求
当GPU被多GPU组合使用时，应该隐藏该GPU的单独卡片，避免显示错误的"Idle"状态。

### 实现方案

**模板逻辑**：
```jinja2
{% for gpu_idx in range(hardware_gpu_status.gpu_count) %}
    {# 检查该GPU是否被任何多GPU组合使用 #}
    {% set is_in_multi_gpu = namespace(value=false) %}
    {% for gpu_key in gpu_statuses.keys() %}
        {% if ',' in gpu_key %}
            {# 解析多GPU键，检查是否包含当前GPU #}
            {% set gpu_list = gpu_key.split(',') %}
            {% if gpu_idx|string in gpu_list %}
                {% set is_in_multi_gpu.value = true %}
            {% endif %}
        {% endif %}
    {% endfor %}
    
    {# 只有当GPU不在多GPU组合中时才显示单独卡片 #}
    {% if not is_in_multi_gpu.value %}
        <!-- 显示单GPU卡片 -->
    {% endif %}
{% endfor %}
```

### 显示规则

1. **单GPU模型**：显示对应的单GPU卡片
   - GPU 0 加载模型 → 显示 GPU 0 卡片 ✅
   - GPU 1 加载模型 → 显示 GPU 1 卡片 ✅

2. **多GPU模型**：隐藏组成GPU的单独卡片，只显示多GPU卡片
   - GPU 0,1 加载模型 → 只显示 Multi-GPU (0,1) 卡片 ✅
   - 不显示 GPU 0 和 GPU 1 的单独卡片 ✅

3. **混合场景**：正确处理单GPU和多GPU共存
   - GPU 0 单独加载 + GPU 2,3 多GPU → 显示 GPU 0, GPU 1(idle), Multi-GPU(2,3) ✅
   - GPU 1 单独加载 + GPU 0,2 多GPU → 显示 GPU 1, GPU 3(idle), Multi-GPU(0,2) ✅

## UI显示策略

### 统一的GPU状态显示

所有GPU状态（单GPU和多GPU）都应该在同一个网格区域显示：

```html
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
    <!-- 1. 首先显示硬件检测到的单个GPU -->
    {% for gpu_idx in range(hardware_gpu_status.gpu_count) %}
        <!-- 检查该GPU是否单独加载了模型 -->
        {% set gpu_instance = gpu_statuses.get(gpu_idx|string, none) %}
        <div class="border rounded-lg p-4 ...">
            <!-- GPU状态显示 -->
        </div>
    {% endfor %}
    
    <!-- 2. 然后显示多GPU组合 -->
    {% for gpu_key, gpu_instance in gpu_statuses.items() %}
        {% if ',' in gpu_key and gpu_instance %}
        <div class="border rounded-lg p-4 bg-blue-50 border-blue-200">
            <div class="flex items-center justify-between mb-2">
                <h4 class="font-semibold text-gray-900">Multi-GPU ({{ gpu_key }})</h4>
                <span class="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">Running</span>
            </div>
            <p class="text-sm text-gray-600">Model: {{ gpu_instance.model_name }}</p>
            <p class="text-xs text-gray-500">Port: {{ gpu_instance.port }}</p>
            <form hx-post="/dashboard/unload-model" hx-target="#dashboard-content" class="mt-2">
                <input type="hidden" name="gpu_id" value="{{ gpu_key }}">
                <button type="submit" class="text-sm text-red-600 hover:text-red-800 font-medium">
                    Unload Model
                </button>
            </form>
        </div>
        {% endif %}
    {% endfor %}
</div>
```

## 实现优先级

1. ✅ **高优先级**：修复 `get_all_gpu_statuses()` 键格式
2. ✅ **高优先级**：更新 `dashboard_content.html` 统一显示所有GPU状态
3. ✅ **中优先级**：移除硬编码的 `gpu_statuses.both` 检查
4. ✅ **低优先级**：优化UI布局，确保多GPU卡片显示清晰

## 测试场景

### 基本功能测试
- [ ] 加载模型到GPU 0，验证unload按钮显示
- [ ] 加载模型到GPU 1，验证unload按钮显示
- [ ] 加载模型到GPU 0和1（"0,1"），验证unload按钮显示在Multi-GPU卡片中
- [ ] 同时加载不同模型到GPU 0和GPU 1（分别），验证两个unload按钮都显示
- [ ] 卸载单GPU模型，验证按钮消失且GPU状态变为Idle
- [ ] 卸载多GPU模型，验证按钮消失且相关GPU状态变为Idle

### UI显示测试
- [ ] 验证单GPU卡片显示在左侧网格区域
- [ ] 验证多GPU卡片使用蓝色主题并显示"Multi-GPU (0,1)"标题
- [ ] 验证所有卡片正确显示模型名称、端口号和状态
- [ ] 验证Unload按钮在加载模型后立即可见
- [ ] 验证点击Unload按钮后正确提交gpu_id参数

### 边界条件测试
- [ ] 刷新页面后验证状态持久化
- [ ] 验证GPU被外部进程占用时不显示unload按钮（显示Occupied状态）
- [ ] 验证同时存在单GPU和多GPU模型时的显示
- [ ] 验证快速连续加载/卸载操作不会导致UI状态不一致

## 推荐方案

**使用方案A**：统一键格式，不使用"gpu"前缀，直接使用标准化的GPU ID字符串（"0", "1", "0,1"等）。

**理由**：
1. 与后端 `gpu_instances` 键格式一致
2. 简化前后端数据传递
3. 更容易扩展到任意数量的GPU组合
4. 减少字符串拼接和解析的复杂度

---

**文档版本**: 1.0  
**创建日期**: 2025-11-16  
**状态**: 待实施
