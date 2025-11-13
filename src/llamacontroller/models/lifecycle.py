"""
Pydantic models for model lifecycle management.
"""

from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ProcessStatus(str, Enum):
    """llama.cpp 进程状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    CRASHED = "crashed"
    ERROR = "error"


class ModelStatus(BaseModel):
    """模型状态信息"""
    model_id: Optional[str] = Field(None, description="当前加载的模型 ID")
    model_name: Optional[str] = Field(None, description="当前加载的模型名称")
    status: ProcessStatus = Field(ProcessStatus.STOPPED, description="进程状态")
    loaded_at: Optional[datetime] = Field(None, description="模型加载时间")
    memory_usage_mb: Optional[int] = Field(None, description="内存使用量(MB)")
    uptime_seconds: Optional[int] = Field(None, description="运行时长(秒)")
    pid: Optional[int] = Field(None, description="进程 ID")
    host: Optional[str] = Field(None, description="服务主机")
    port: Optional[int] = Field(None, description="服务端口")
    
    model_config = {
        "use_enum_values": True,
        "protected_namespaces": ()  # 允许 model_ 前缀
    }


class LoadModelRequest(BaseModel):
    """加载模型请求"""
    model_id: str = Field(..., description="要加载的模型 ID")
    
    model_config = {"protected_namespaces": ()}


class LoadModelResponse(BaseModel):
    """加载模型响应"""
    success: bool = Field(..., description="操作是否成功")
    model_id: str = Field(..., description="模型 ID")
    message: str = Field(..., description="结果消息")
    status: ModelStatus = Field(..., description="模型状态")
    
    model_config = {"protected_namespaces": ()}


class UnloadModelResponse(BaseModel):
    """卸载模型响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="结果消息")


class SwitchModelRequest(BaseModel):
    """切换模型请求"""
    model_id: str = Field(..., description="要切换到的模型 ID")
    
    model_config = {"protected_namespaces": ()}


class SwitchModelResponse(BaseModel):
    """切换模型响应"""
    success: bool = Field(..., description="操作是否成功")
    old_model_id: Optional[str] = Field(None, description="之前的模型 ID")
    new_model_id: str = Field(..., description="新的模型 ID")
    message: str = Field(..., description="结果消息")
    status: ModelStatus = Field(..., description="新模型状态")
    
    model_config = {"protected_namespaces": ()}


class ModelInfo(BaseModel):
    """模型信息"""
    id: str = Field(..., description="模型 ID")
    name: str = Field(..., description="模型名称")
    path: str = Field(..., description="模型文件路径")
    status: str = Field(..., description="模型状态")
    loaded: bool = Field(..., description="是否已加载")
    description: str = Field(default="", description="模型描述")
    parameter_count: str = Field(default="", description="参数量")
    quantization: str = Field(default="", description="量化类型")


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    healthy: bool = Field(..., description="是否健康")
    status: ProcessStatus = Field(..., description="进程状态")
    message: str = Field(..., description="状态消息")
    uptime_seconds: Optional[int] = Field(None, description="运行时长")
