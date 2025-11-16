# GPU Memory Display After Model Loading

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-11-16
- **Status**: Implementation Specification
- **Category**: Feature Enhancement

## Overview

This document specifies the requirements and implementation for displaying GPU memory usage after a model is loaded. The goal is to provide users with real-time visibility into how much GPU memory their loaded models are consuming.

## Current State

### Existing Functionality
1. **Hardware GPU Detection**: The system already detects GPU hardware status using `nvidia-smi` via `GpuDetector`
   - Shows total GPU memory
   - Shows current memory usage for all GPUs
   - Displays process information for occupied GPUs

2. **Model Loading**: Models are loaded on specific GPUs via `ModelLifecycleManager`
   - Tracks which model is loaded on which GPU
   - Manages llama.cpp processes per GPU

3. **UI Display**: Dashboard shows GPU status cards
   - Hardware status includes memory for idle/occupied GPUs
   - Loaded model status shows model name and port
   - **Gap**: Loaded model cards do NOT show memory usage

## Requirements

### Functional Requirements

1. **Post-Load Memory Query**
   - After successfully loading a model, the system should query GPU memory usage
   - Memory information should be associated with the loaded model instance
   - Memory data should be refreshed when dashboard is refreshed

2. **Memory Display in UI**
   - Loaded model GPU cards should display memory usage
   - Format: "Memory: XXX MiB / YYYY MiB" (used / total)
   - Should be visually distinct from hardware status

3. **Data Accuracy**
   - Memory usage should reflect actual model consumption
   - Should update when GPU status is refreshed (5-minute auto-refresh)
   - Should be accurate across single-GPU and multi-GPU scenarios

### Non-Functional Requirements

1. **Performance**: Memory queries should not significantly delay model loading
2. **Reliability**: Memory display should degrade gracefully if query fails
3. **Consistency**: Memory data should be consistent across API and UI

## Architecture Changes

### 1. Data Model Updates

**File**: `src/llamacontroller/models/lifecycle.py`

Update `GpuInstanceStatus` to include memory information:

```python
class GpuInstanceStatus(BaseModel):
    """Single GPU instance status"""
    gpu_id: Union[int, str] = Field(..., description="GPU ID")
    port: int = Field(..., description="Service port")
    model_id: Optional[str] = Field(None, description="Loaded model ID")
    model_name: Optional[str] = Field(None, description="Loaded model name")
    status: ProcessStatus = Field(..., description="Process status")
    loaded_at: Optional[datetime] = Field(None, description="Load time")
    uptime_seconds: Optional[int] = Field(None, description="Uptime (seconds)")
    pid: Optional[int] = Field(None, description="Process ID")
    
    # New fields for GPU memory tracking
    memory_used_mb: Optional[int] = Field(None, description="GPU memory used (MiB)")
    memory_total_mb: Optional[int] = Field(None, description="Total GPU memory (MiB)")
    
    model_config = {
        "use_enum_values": True,
        "protected_namespaces": ()
    }
```

### 2. Lifecycle Manager Updates

**File**: `src/llamacontroller/core/lifecycle.py`

#### 2.1 Add Memory Query Method

```python
def _query_gpu_memory(self, gpu_id: str) -> Dict[str, int]:
    """
    Query GPU memory usage for specific GPU(s).
    
    Args:
        gpu_id: GPU ID string (e.g., "0", "1", "0,1")
        
    Returns:
        Dict with 'memory_used' and 'memory_total' in MiB
    """
    try:
        # Get GPU IDs as list
        gpu_ids = self._parse_gpu_ids(gpu_id)
        
        # Query GPU detector for current status
        gpu_statuses = self.gpu_detector.detect_gpus()
        
        # For multi-GPU, sum memory usage
        total_used = 0
        total_capacity = 0
        
        for gid in gpu_ids:
            gpu_status = next((g for g in gpu_statuses if g.index == gid), None)
            if gpu_status:
                total_used += gpu_status.memory_used
                total_capacity += gpu_status.memory_total
        
        return {
            'memory_used': total_used,
            'memory_total': total_capacity
        }
    except Exception as e:
        logger.warning(f"Failed to query GPU memory for {gpu_id}: {e}")
        return {'memory_used': 0, 'memory_total': 0}
```

#### 2.2 Update GpuInstance DataClass

```python
@dataclass
class GpuInstance:
    """GPU instance information"""
    gpu_id: str
    port: int
    process: subprocess.Popen
    model_id: str
    model_name: str
    adapter: LlamaCppAdapter
    start_time: datetime
    
    # New fields
    memory_used_mb: int = 0
    memory_total_mb: int = 0
```

#### 2.3 Update load_model Method

After successful model load, query and store memory:

```python
async def load_model(self, model_id: str, gpu_id: str = "0") -> ModelStatus:
    """Load a model on specified GPU(s)."""
    # ... existing load logic ...
    
    # After successful load and health check
    if model_status.status == ProcessStatus.RUNNING:
        # Query GPU memory usage
        memory_info = self._query_gpu_memory(gpu_id)
        
        # Update instance with memory info
        if gpu_id in self.gpu_instances:
            instance = self.gpu_instances[gpu_id]
            instance.memory_used_mb = memory_info['memory_used']
            instance.memory_total_mb = memory_info['memory_total']
            
            logger.info(
                f"Model {model_id} loaded on GPU {gpu_id}: "
                f"{memory_info['memory_used']}MiB / {memory_info['memory_total']}MiB"
            )
    
    return model_status
```

#### 2.4 Update get_gpu_status Method

Include memory information in status:

```python
async def get_gpu_status(self, gpu_id: str) -> Optional[GpuInstanceStatus]:
    """Get status of specific GPU instance."""
    instance = self.gpu_instances.get(gpu_id)
    if not instance:
        return None
    
    # Query current memory (fresh data)
    memory_info = self._query_gpu_memory(gpu_id)
    
    return GpuInstanceStatus(
        gpu_id=instance.gpu_id,
        port=instance.port,
        model_id=instance.model_id,
        model_name=instance.model_name,
        status=instance.adapter.get_status(),
        loaded_at=instance.start_time,
        uptime_seconds=instance.adapter.get_uptime_seconds(),
        pid=instance.adapter.get_pid(),
        memory_used_mb=memory_info['memory_used'],
        memory_total_mb=memory_info['memory_total']
    )
```

### 3. UI Template Updates

**File**: `src/llamacontroller/web/templates/partials/dashboard_content.html`

Update GPU status cards to display memory for loaded models:

```html
{% if gpu_instance %}
    <p class="text-sm text-gray-600">Model: {{ gpu_instance.model_name }}</p>
    <p class="text-xs text-gray-500">Port: {{ gpu_instance.port }}</p>
    
    <!-- Add memory display -->
    {% if gpu_instance.memory_used_mb is not none and gpu_instance.memory_total_mb > 0 %}
    <p class="text-xs text-gray-500 mt-1">
        Memory: {{ gpu_instance.memory_used_mb }}MiB / {{ gpu_instance.memory_total_mb }}MiB
        <span class="text-gray-400">
            ({{ ((gpu_instance.memory_used_mb / gpu_instance.memory_total_mb) * 100) | round(1) }}%)
        </span>
    </p>
    {% endif %}
    
    <form hx-post="/dashboard/unload-model" hx-target="#dashboard-content" hx-disabled-elt="button" class="mt-2">
        <input type="hidden" name="gpu_id" value="{{ gpu_idx }}">
        <button type="submit" class="text-sm text-red-600 hover:text-red-800 font-medium">Unload Model</button>
    </form>
{% endif %}
```

## Implementation Steps

1. ✅ Update `GpuInstanceStatus` model with memory fields
2. ✅ Update `GpuInstance` dataclass with memory fields
3. ✅ Implement `_query_gpu_memory()` method in lifecycle manager
4. ✅ Update `load_model()` to query memory after load
5. ✅ Update `get_gpu_status()` to include current memory
6. ✅ Update UI template to display memory for loaded models
7. ✅ Test with single-GPU model loading
8. ✅ Test with multi-GPU model loading
9. ✅ Verify memory display on dashboard refresh

## Testing Scenarios

### Test Case 1: Single GPU Model Load
1. Load model on GPU 0
2. Verify memory displayed in GPU 0 card
3. Verify memory values are reasonable (> 0, < total)
4. Verify percentage calculation is correct

### Test Case 2: Multi-GPU Model Load
1. Load model on GPU "0,1"
2. Verify memory is summed across both GPUs
3. Verify multi-GPU card shows total memory usage

### Test Case 3: Dashboard Refresh
1. Load model on GPU 0
2. Wait for auto-refresh (5 minutes) or manual refresh
3. Verify memory values update correctly
4. Verify no stale data

### Test Case 4: Error Handling
1. Simulate nvidia-smi failure during memory query
2. Verify UI shows graceful fallback (no memory or "N/A")
3. Verify system continues to function

### Test Case 5: Memory Growth Detection
1. Load small model
2. Note initial memory usage
3. Send inference requests
4. Refresh dashboard
5. Verify memory usage reflects inference load (if applicable)

## Success Criteria

✅ Loaded model GPU cards display memory usage  
✅ Memory values are accurate and updated  
✅ Multi-GPU scenarios show correct summed memory  
✅ UI gracefully handles missing memory data  
✅ No performance degradation during model loading  
✅ Memory display updates on dashboard refresh  

## Future Enhancements

1. **Memory History**: Track memory usage over time, show trend graph
2. **Memory Alerts**: Warn if memory usage exceeds threshold
3. **Per-Process Memory**: Break down memory by process for multi-model scenarios
4. **Memory Prediction**: Estimate memory needed before loading model
5. **Memory Optimization**: Suggest GPU with most available memory

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-16  
**Status**: Ready for Implementation
