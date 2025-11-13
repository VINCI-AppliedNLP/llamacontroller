# Web UI GPU Selection Design

## 概述
为模型加载功能设计GPU选择界面,使用checkbox/toggle按钮组而非下拉菜单。

## UI设计方案

### 方案A: Checkbox组 (推荐)

**优势**:
- ✅ 直观显示所有可用GPU
- ✅ 可以选择任意组合
- ✅ 清楚显示已选择的GPU
- ✅ 支持未来扩展到更多GPU

**UI示例**:
```
┌─────────────────────────────────────────┐
│ Load Model                               │
├─────────────────────────────────────────┤
│ Model:  [Phi-4 Reasoning ▼]             │
│                                          │
│ Select GPU(s):                           │
│ ☐ GPU 0 (GeForce RTX 3090)              │
│ ☐ GPU 1 (GeForce RTX 3090)              │
│                                          │
│           [Load Model]                   │
└─────────────────────────────────────────┘
```

**HTML实现**:
```html
<form hx-post="/dashboard/load-model" hx-target="#model-status">
    <div class="mb-4">
        <label class="block text-sm font-medium mb-2">Model</label>
        <select name="model_id" class="w-full border rounded p-2">
            <option value="phi-4">Phi-4 Reasoning Plus</option>
            <option value="qwen-coder">Qwen3 Coder 30B</option>
        </select>
    </div>
    
    <div class="mb-4">
        <label class="block text-sm font-medium mb-2">Select GPU(s)</label>
        <div class="space-y-2">
            <label class="flex items-center">
                <input type="checkbox" name="gpu" value="0" 
                       class="mr-2 h-4 w-4 text-blue-600">
                <span>GPU 0 (GeForce RTX 3090)</span>
            </label>
            <label class="flex items-center">
                <input type="checkbox" name="gpu" value="1" 
                       class="mr-2 h-4 w-4 text-blue-600">
                <span>GPU 1 (GeForce RTX 3090)</span>
            </label>
        </div>
        <p class="text-xs text-gray-500 mt-1">
            Select one or more GPUs for model loading
        </p>
    </div>
    
    <button type="submit" 
            class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
        Load Model
    </button>
</form>
```

### 方案B: Toggle按钮组

**优势**:
- ✅ 更现代的视觉效果
- ✅ 清晰的选中/未选中状态
- ✅ 触摸友好

**UI示例**:
```
┌─────────────────────────────────────────┐
│ Load Model                               │
├─────────────────────────────────────────┤
│ Model:  [Phi-4 Reasoning ▼]             │
│                                          │
│ Select GPU(s):                           │
│  ┌────────┐  ┌────────┐                 │
│  │ GPU 0  │  │ GPU 1  │                 │
│  └────────┘  └────────┘                 │
│   (未选中)     (已选中)                  │
│                                          │
│           [Load Model]                   │
└─────────────────────────────────────────┘
```

**HTML实现** (使用Alpine.js):
```html
<form hx-post="/dashboard/load-model" 
      hx-target="#model-status"
      x-data="{ selectedGpus: [] }">
    <div class="mb-4">
        <label class="block text-sm font-medium mb-2">Model</label>
        <select name="model_id" class="w-full border rounded p-2">
            <option value="phi-4">Phi-4 Reasoning Plus</option>
            <option value="qwen-coder">Qwen3 Coder 30B</option>
        </select>
    </div>
    
    <div class="mb-4">
        <label class="block text-sm font-medium mb-2">Select GPU(s)</label>
        <div class="flex gap-2">
            <!-- GPU 0 Toggle -->
            <button type="button"
                    @click="selectedGpus.includes('0') 
                            ? selectedGpus = selectedGpus.filter(g => g !== '0')
                            : selectedGpus.push('0')"
                    :class="selectedGpus.includes('0') 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gray-200 text-gray-700'"
                    class="px-4 py-2 rounded-lg font-medium transition">
                GPU 0
            </button>
            
            <!-- GPU 1 Toggle -->
            <button type="button"
                    @click="selectedGpus.includes('1') 
                            ? selectedGpus = selectedGpus.filter(g => g !== '1')
                            : selectedGpus.push('1')"
                    :class="selectedGpus.includes('1') 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-gray-200 text-gray-700'"
                    class="px-4 py-2 rounded-lg font-medium transition">
                GPU 1
            </button>
        </div>
        
        <!-- Hidden input for form submission -->
        <input type="hidden" 
               name="gpu_id" 
               :value="selectedGpus.join(',')">
        
        <p class="text-xs text-gray-500 mt-2">
            Selected: <span x-text="selectedGpus.length > 0 ? selectedGpus.join(', ') : 'None'"></span>
        </p>
    </div>
    
    <button type="submit" 
            :disabled="selectedGpus.length === 0"
            :class="selectedGpus.length === 0 ? 'bg-gray-300' : 'bg-blue-500 hover:bg-blue-600'"
            class="text-white px-4 py-2 rounded transition">
        Load Model
    </button>
</form>
```

### 方案C: 快捷按钮组 (混合方案)

**优势**:
- ✅ 常见组合一键选择
- ✅ 也支持自定义选择
- ✅ 最快的用户体验

**UI示例**:
```
┌─────────────────────────────────────────┐
│ Load Model                               │
├─────────────────────────────────────────┤
│ Model:  [Phi-4 Reasoning ▼]             │
│                                          │
│ Quick Select:                            │
│  [GPU 0]  [GPU 1]  [Both GPUs]          │
│                                          │
│ Or select manually:                      │
│ ☐ GPU 0  ☐ GPU 1                        │
│                                          │
│           [Load Model]                   │
└─────────────────────────────────────────┘
```

## 推荐方案

**推荐: 方案B (Toggle按钮组)**

**理由**:
1. **视觉直观**: 按钮状态一目了然
2. **交互友好**: 点击切换,无需理解checkbox语义
3. **现代化**: 符合现代Web应用趋势
4. **触摸友好**: 适合触摸屏设备
5. **扩展性好**: 可以轻松添加更多GPU按钮

## 后端处理

服务器端需要处理checkbox组或逗号分隔的值:

```python
@router.post("/dashboard/load-model")
async def load_model(
    request: Request,
    model_id: str = Form(...),
    gpu_id: str = Form(...),  # "0", "1", 或 "0,1"
    current_user: User = Depends(get_current_user)
):
    # gpu_id已经是正确的格式 "0", "1", "0,1"等
    await lifecycle_manager.load_model(model_id, gpu_id)
    # ...
```

对于checkbox组(方案A),需要JavaScript处理:
```javascript
// 将多个checkbox值合并为逗号分隔字符串
document.querySelector('form').addEventListener('submit', function(e) {
    const checkboxes = document.querySelectorAll('input[name="gpu"]:checked');
    const gpuIds = Array.from(checkboxes).map(cb => cb.value).sort().join(',');
    
    // 创建隐藏字段
    const hiddenField = document.createElement('input');
    hiddenField.type = 'hidden';
    hiddenField.name = 'gpu_id';
    hiddenField.value = gpuIds || '0'; // 默认GPU 0
    this.appendChild(hiddenField);
});
```

## 状态显示

当前已加载模型的GPU状态显示:

```html
<div class="grid grid-cols-2 gap-4">
    <!-- GPU 0 Status -->
    <div class="border rounded-lg p-4">
        <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold">GPU 0</h3>
            <span class="px-2 py-1 bg-green-100 text-green-800 rounded text-xs">
                Running
            </span>
        </div>
        <p class="text-sm text-gray-600">Model: Phi-4 Reasoning Plus</p>
        <p class="text-sm text-gray-600">Port: 8081</p>
        <button class="mt-2 text-sm text-red-600 hover:underline"
                hx-post="/dashboard/unload-model"
                hx-vals='{"gpu_id": "0"}'>
            Unload
        </button>
    </div>
    
    <!-- GPU 1 Status -->
    <div class="border rounded-lg p-4">
        <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold">GPU 1</h3>
            <span class="px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs">
                Idle
            </span>
        </div>
        <p class="text-sm text-gray-400">No model loaded</p>
    </div>
</div>
```

## 验证

客户端验证(使用Alpine.js):
```html
<button type="submit" 
        :disabled="selectedGpus.length === 0"
        x-text="selectedGpus.length === 0 
                ? 'Select at least one GPU' 
                : 'Load Model'"
        class="...">
</button>
```

## 移动端适配

```css
/* 移动端:垂直堆叠按钮 */
@media (max-width: 640px) {
    .gpu-toggle-group {
        flex-direction: column;
    }
    
    .gpu-toggle-btn {
        width: 100%;
    }
}
```

## 无障碍性

```html
<div role="group" aria-labelledby="gpu-selection-label">
    <label id="gpu-selection-label" class="block text-sm font-medium mb-2">
        Select GPU(s)
    </label>
    <button type="button"
            role="switch"
            :aria-checked="selectedGpus.includes('0')"
            aria-label="Toggle GPU 0">
        GPU 0
    </button>
</div>
```

---

**建议**: 使用方案B (Toggle按钮组) + Alpine.js实现
- 最佳用户体验
- 代码简洁
- 易于扩展
