"""
Management API endpoints for LlamaController.
These are LlamaController-specific endpoints for model management.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.lifecycle import ModelLifecycleManager, LifecycleError
from ..models.api import (
    LoadModelRequest,
    SwitchModelRequest,
    ModelInfoResponse,
    ModelStatusResponse,
    HealthCheckResponse,
    ListModelsResponse,
    ServerLogsResponse,
)
from ..models.lifecycle import LoadModelResponse, UnloadModelResponse, SwitchModelResponse
from .dependencies import get_lifecycle_manager
from ..auth.dependencies import get_current_user
from ..db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["management"])

@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Check the health of the current model/server.
    
    Returns:
        HealthCheckResponse with health status
    """
    try:
        health = await lifecycle.healthcheck()
        return health
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

@router.get("/models", response_model=ListModelsResponse)
async def list_models(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    List all available models.
    
    Returns:
        ListModelsResponse with list of models
    """
    try:
        models = lifecycle.get_available_models()
        
        # Convert to response model
        model_responses = [
            ModelInfoResponse(
                id=model.id,
                name=model.name,
                path=model.path,
                status=model.status,
                loaded=model.loaded,
                description=model.description,
                parameter_count=model.parameter_count,
                quantization=model.quantization,
            )
            for model in models
        ]
        
        return ListModelsResponse(models=model_responses)
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )

@router.get("/models/status", response_model=ModelStatusResponse)
async def get_model_status(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of the currently loaded model.
    
    Returns:
        ModelStatusResponse with current model status
    """
    try:
        status_info = await lifecycle.get_status()
        
        # Construct server URL if server is running
        server_url = None
        if status_info.status == "running" and status_info.host and status_info.port:
            server_url = f"http://{status_info.host}:{status_info.port}"
        
        return ModelStatusResponse(
            model_id=status_info.model_id,
            model_name=status_info.model_name,
            status=status_info.status,
            loaded_at=status_info.loaded_at,
            memory_usage_mb=status_info.memory_usage_mb,
            uptime_seconds=status_info.uptime_seconds,
            pid=status_info.pid,
            host=status_info.host,
            port=status_info.port,
            server_url=server_url,
        )
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )

@router.post("/models/load", response_model=LoadModelResponse)
async def load_model(
    request: LoadModelRequest,
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Load a model by ID.
    
    Args:
        request: LoadModelRequest with model_id
        
    Returns:
        LoadModelResponse with operation result
    """
    try:
        logger.info(f"API request to load model: {request.model_id}")
        result = await lifecycle.load_model(request.model_id)
        return result
    except LifecycleError as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error loading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load model: {str(e)}"
        )

@router.post("/models/unload", response_model=UnloadModelResponse)
async def unload_model(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Unload the currently loaded model.
    
    Returns:
        UnloadModelResponse with operation result
    """
    try:
        logger.info("API request to unload model")
        result = await lifecycle.unload_model()
        return result
    except LifecycleError as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error unloading model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unload model: {str(e)}"
        )

@router.post("/models/switch", response_model=SwitchModelResponse)
async def switch_model(
    request: SwitchModelRequest,
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Switch to a different model.
    
    Args:
        request: SwitchModelRequest with new model_id
        
    Returns:
        SwitchModelResponse with operation result
    """
    try:
        logger.info(f"API request to switch to model: {request.model_id}")
        result = await lifecycle.switch_model(request.model_id)
        return result
    except LifecycleError as e:
        logger.error(f"Failed to switch model: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error switching model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to switch model: {str(e)}"
        )

@router.get("/logs", response_model=ServerLogsResponse)
async def get_server_logs(
    lines: int = 100,
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent server log lines.
    
    Args:
        lines: Number of recent lines to return (default: 100)
        
    Returns:
        ServerLogsResponse with log lines
    """
    try:
        log_lines = await lifecycle.get_server_logs(lines=lines)
        
        return ServerLogsResponse(
            logs=log_lines,
            total_lines=len(log_lines)
        )
    except Exception as e:
        logger.error(f"Failed to get server logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server logs: {str(e)}"
        )
