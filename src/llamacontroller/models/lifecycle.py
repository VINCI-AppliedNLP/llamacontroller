"""
Pydantic models for model lifecycle management.
"""

from typing import Optional, Union, Dict
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProcessStatus(str, Enum):
    """llama.cpp process status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    CRASHED = "crashed"
    ERROR = "error"


class ModelStatus(BaseModel):
    """Model status information"""
    model_id: Optional[str] = Field(None, description="Currently loaded model ID")
    model_name: Optional[str] = Field(None, description="Currently loaded model name")
    status: ProcessStatus = Field(ProcessStatus.STOPPED, description="Process status")
    loaded_at: Optional[datetime] = Field(None, description="Model load time")
    memory_usage_mb: Optional[int] = Field(None, description="Memory usage (MB)")
    uptime_seconds: Optional[int] = Field(None, description="Uptime (seconds)")
    pid: Optional[int] = Field(None, description="Process ID")
    host: Optional[str] = Field(None, description="Service host")
    port: Optional[int] = Field(None, description="Service port")
    
    model_config = {
        "use_enum_values": True,
        "protected_namespaces": ()  # Allow model_ prefix
    }


class GpuInstanceStatus(BaseModel):
    """Single GPU instance status"""
    gpu_id: Union[int, str] = Field(..., description="GPU ID (0, 1, or 'both')")
    port: int = Field(..., description="Service port")
    model_id: Optional[str] = Field(None, description="Loaded model ID")
    model_name: Optional[str] = Field(None, description="Loaded model name")
    status: ProcessStatus = Field(..., description="Process status")
    loaded_at: Optional[datetime] = Field(None, description="Load time")
    uptime_seconds: Optional[int] = Field(None, description="Uptime (seconds)")
    pid: Optional[int] = Field(None, description="Process ID")
    
    model_config = {
        "use_enum_values": True,
        "protected_namespaces": ()
    }

class AllGpuStatus(BaseModel):
    """Status of all GPUs"""
    gpu0: Optional[GpuInstanceStatus] = Field(None, description="GPU 0 status")
    gpu1: Optional[GpuInstanceStatus] = Field(None, description="GPU 1 status")
    both: Optional[GpuInstanceStatus] = Field(None, description="Both GPUs status")
    
    model_config = {"protected_namespaces": ()}

class LoadModelRequest(BaseModel):
    """Load model request"""
    model_id: str = Field(..., description="Model ID to load")
    gpu_id: Union[int, str] = Field(0, description="GPU ID (0, 1, or 'both')")
    
    model_config = {"protected_namespaces": ()}


class LoadModelResponse(BaseModel):
    """Load model response"""
    success: bool = Field(..., description="Operation success")
    model_id: str = Field(..., description="Model ID")
    message: str = Field(..., description="Result message")
    status: ModelStatus = Field(..., description="Model status")
    
    model_config = {"protected_namespaces": ()}


class UnloadModelResponse(BaseModel):
    """Unload model response"""
    success: bool = Field(..., description="Operation success")
    message: str = Field(..., description="Result message")


class UnloadModelRequest(BaseModel):
    """Unload model request"""
    gpu_id: Union[int, str] = Field(..., description="GPU ID (0, 1, or 'both')")

class SwitchModelRequest(BaseModel):
    """Switch model request"""
    model_id: str = Field(..., description="Model ID to switch to")
    gpu_id: Union[int, str] = Field(0, description="GPU ID (0, 1, or 'both')")
    
    model_config = {"protected_namespaces": ()}


class SwitchModelResponse(BaseModel):
    """Switch model response"""
    success: bool = Field(..., description="Operation success")
    old_model_id: Optional[str] = Field(None, description="Previous model ID")
    new_model_id: str = Field(..., description="New model ID")
    message: str = Field(..., description="Result message")
    status: ModelStatus = Field(..., description="New model status")
    
    model_config = {"protected_namespaces": ()}


class ModelInfo(BaseModel):
    """Model information"""
    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    path: str = Field(..., description="Model file path")
    status: str = Field(..., description="Model status")
    loaded: bool = Field(..., description="Whether loaded")
    description: str = Field(default="", description="Model description")
    parameter_count: str = Field(default="", description="Parameter count")
    quantization: str = Field(default="", description="Quantization type")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    healthy: bool = Field(..., description="Whether healthy")
    status: ProcessStatus = Field(..., description="Process status")
    message: str = Field(..., description="Status message")
    uptime_seconds: Optional[int] = Field(None, description="Uptime")
