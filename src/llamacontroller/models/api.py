"""
Pydantic models for API request/response schemas.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Management API Models (LlamaController specific)

class LoadModelRequest(BaseModel):
    """Request to load a model."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str = Field(..., description="ID of the model to load")
    gpu_id: Union[int, str] = Field(0, description="GPU ID (0, 1, or 'both')")

class UnloadModelRequest(BaseModel):
    """Request to unload current model."""
    gpu_id: Union[int, str] = Field(..., description="GPU ID (0, 1, or 'both')")

class SwitchModelRequest(BaseModel):
    """Request to switch to a different model."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: str = Field(..., description="ID of the model to switch to")
    gpu_id: Union[int, str] = Field(0, description="GPU ID (0, 1, or 'both')")

class ModelInfoResponse(BaseModel):
    """Information about a model."""
    id: str
    name: str
    path: str
    status: str
    loaded: bool
    description: Optional[str] = None
    parameter_count: Optional[str] = None
    quantization: Optional[str] = None

class ModelStatusResponse(BaseModel):
    """Current model status."""
    model_config = ConfigDict(protected_namespaces=())
    
    model_id: Optional[str]
    model_name: Optional[str]
    status: str
    loaded_at: Optional[datetime]
    memory_usage_mb: Optional[float]
    uptime_seconds: Optional[float]
    pid: Optional[int]
    host: Optional[str]
    port: Optional[int]
    server_url: Optional[str] = Field(None, description="URL to llama-server web interface")

class HealthCheckResponse(BaseModel):
    """Health check response."""
    healthy: bool
    status: str
    message: str
    uptime_seconds: Optional[float]

class ListModelsResponse(BaseModel):
    """Response listing available models."""
    models: List[ModelInfoResponse]

class ServerLogsResponse(BaseModel):
    """Server logs response."""
    logs: List[str]
    total_lines: int
