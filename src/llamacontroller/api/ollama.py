"""
Ollama-compatible API endpoints.
These endpoints mimic Ollama's API for compatibility with existing clients.
"""

import logging
import httpx
import os
from datetime import datetime
from typing import AsyncIterator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse

from ..core.lifecycle import ModelLifecycleManager
from ..core.config import ConfigManager
from ..models.ollama import (
    GenerateRequest,
    GenerateResponse,
    ChatRequest,
    ChatResponse,
    ChatMessage,
    TagsResponse,
    ModelInfo as OllamaModelInfo,
    ModelDetails,
    ShowRequest,
    ShowResponse,
    ProcessResponse,
    RunningModel,
    DeleteRequest,
    ErrorResponse,
)
from .dependencies import get_lifecycle_manager, get_config_manager, verify_model_loaded
from ..auth.dependencies import get_current_user
from ..db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ollama"])

def _get_llama_cpp_url(config: ConfigManager) -> str:
    """Get the llama.cpp server URL."""
    host = config.llama_cpp.default_host
    port = config.llama_cpp.default_port
    return f"http://{host}:{port}"

async def _proxy_to_llama_cpp(
    endpoint: str,
    method: str,
    config: ConfigManager,
    json_data: dict | None = None,
    stream: bool = False
) -> httpx.Response:
    """
    Proxy a request to llama.cpp server.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        config: ConfigManager instance
        json_data: JSON data to send
        stream: Whether to stream the response
        
    Returns:
        httpx.Response from llama.cpp
    """
    base_url = _get_llama_cpp_url(config)
    url = f"{base_url}{endpoint}"
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        if method.upper() == "GET":
            response = await client.get(url)
        elif method.upper() == "POST":
            if stream:
                response = await client.post(url, json=json_data, timeout=None)
            else:
                response = await client.post(url, json=json_data)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        return response

async def _stream_llama_cpp_response(
    endpoint: str,
    json_data: dict,
    config: ConfigManager
) -> AsyncIterator[str]:
    """
    Stream responses from llama.cpp server.
    
    Args:
        endpoint: API endpoint path
        json_data: JSON data to send
        config: ConfigManager instance
        
    Yields:
        JSON strings for streaming response
    """
    base_url = _get_llama_cpp_url(config)
    url = f"{base_url}{endpoint}"
    
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=json_data) as response:
            async for line in response.aiter_lines():
                if line:
                    yield f"{line}\n"

@router.post("/generate")
async def generate(
    request: GenerateRequest,
    lifecycle: ModelLifecycleManager = Depends(verify_model_loaded),
    config: ConfigManager = Depends(get_config_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Generate completion from a prompt (Ollama-compatible endpoint).
    
    Args:
        request: GenerateRequest with prompt and options
        
    Returns:
        StreamingResponse or JSONResponse with generated text
    """
    try:
        logger.info(f"Generate request for model: {request.model}")
        
        # Transform Ollama request to llama.cpp format
        llama_request = {
            "prompt": request.prompt,
            "stream": request.stream if request.stream is not None else True,
        }
        
        # Add optional parameters
        if request.system:
            llama_request["system_prompt"] = request.system
        
        if request.options:
            # Map Ollama options to llama.cpp parameters
            if "temperature" in request.options:
                llama_request["temperature"] = request.options["temperature"]
            if "top_p" in request.options:
                llama_request["top_p"] = request.options["top_p"]
            if "top_k" in request.options:
                llama_request["top_k"] = request.options["top_k"]
            if "num_predict" in request.options:
                llama_request["n_predict"] = request.options["num_predict"]
        
        # Stream or non-stream response
        if llama_request["stream"]:
            # Return streaming response
            return StreamingResponse(
                _stream_llama_cpp_response("/completion", llama_request, config),
                media_type="application/x-ndjson"
            )
        else:
            # Return single response
            response = await _proxy_to_llama_cpp(
                "/completion",
                "POST",
                config,
                json_data=llama_request,
                stream=False
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"llama.cpp error: {response.text}"
                )
            
            # Transform llama.cpp response to Ollama format
            llama_response = response.json()
            
            ollama_response = GenerateResponse(
                model=request.model,
                created_at=datetime.utcnow().isoformat() + "Z",
                response=llama_response.get("content", ""),
                done=True,
                context=request.context,
                total_duration=llama_response.get("timings", {}).get("total_ms"),
                load_duration=llama_response.get("timings", {}).get("load_ms"),
                prompt_eval_count=llama_response.get("timings", {}).get("prompt_n"),
                prompt_eval_duration=llama_response.get("timings", {}).get("prompt_ms"),
                eval_count=llama_response.get("timings", {}).get("predicted_n"),
                eval_duration=llama_response.get("timings", {}).get("predicted_ms"),
            )
            
            return ollama_response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )

@router.post("/chat")
async def chat(
    request: ChatRequest,
    lifecycle: ModelLifecycleManager = Depends(verify_model_loaded),
    config: ConfigManager = Depends(get_config_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Chat completion endpoint (Ollama-compatible).
    
    Args:
        request: ChatRequest with messages
        
    Returns:
        StreamingResponse or JSONResponse with chat completion
    """
    try:
        logger.info(f"Chat request for model: {request.model}")
        
        # Transform messages to llama.cpp format
        # llama.cpp uses a different chat format, we need to convert
        messages_for_llama = []
        for msg in request.messages:
            messages_for_llama.append({
                "role": msg.role,
                "content": msg.content
            })
        
        llama_request = {
            "messages": messages_for_llama,
            "stream": request.stream if request.stream is not None else True,
        }
        
        if request.options:
            if "temperature" in request.options:
                llama_request["temperature"] = request.options["temperature"]
            if "top_p" in request.options:
                llama_request["top_p"] = request.options["top_p"]
        
        # Use chat endpoint if available, otherwise use completion
        endpoint = "/v1/chat/completions"  # OpenAI-compatible endpoint
        
        if llama_request["stream"]:
            return StreamingResponse(
                _stream_llama_cpp_response(endpoint, llama_request, config),
                media_type="application/x-ndjson"
            )
        else:
            response = await _proxy_to_llama_cpp(
                endpoint,
                "POST",
                config,
                json_data=llama_request,
                stream=False
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"llama.cpp error: {response.text}"
                )
            
            llama_response = response.json()
            
            # Extract assistant message
            assistant_content = ""
            if "choices" in llama_response and len(llama_response["choices"]) > 0:
                assistant_content = llama_response["choices"][0].get("message", {}).get("content", "")
            
            ollama_response = ChatResponse(
                model=request.model,
                created_at=datetime.utcnow().isoformat() + "Z",
                message=ChatMessage(role="assistant", content=assistant_content, images=None),
                done=True,
            )
            
            return ollama_response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

@router.get("/tags")
async def list_models(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    List available models (Ollama-compatible endpoint).
    
    Returns:
        TagsResponse with list of models
    """
    try:
        models = lifecycle.get_available_models()
        
        ollama_models = []
        for model in models:
            # Get file size if file exists
            size = 0
            if os.path.exists(model.path):
                size = os.path.getsize(model.path)
            
            ollama_models.append(
                OllamaModelInfo(
                    name=model.id,
                    model=model.id,
                    modified_at=datetime.utcnow().isoformat() + "Z",
                    size=size,
                    digest=f"sha256:{model.id}",  # Simplified digest
                    details=ModelDetails(
                        format="gguf",
                        family=model.description or "unknown",
                        parameter_size=model.parameter_count or "unknown",
                        quantization_level=model.quantization or "unknown"
                    )
                )
            )
        
        return TagsResponse(models=ollama_models)
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )

@router.post("/show")
async def show_model(
    request: ShowRequest,
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Show model information (Ollama-compatible endpoint).
    
    Args:
        request: ShowRequest with model name
        
    Returns:
        ShowResponse with model details
    """
    try:
        # Find model by ID
        model_config = lifecycle.config_manager.models.get_model(request.name)
        
        if model_config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found: {request.name}"
            )
        
        # Build modelfile representation
        modelfile = f"FROM {model_config.path}\n"
        
        # Build parameters string
        params_list = []
        params_dict = model_config.parameters.model_dump()
        for key, value in params_dict.items():
            params_list.append(f"{key} {value}")
        parameters = "\n".join(params_list)
        
        response = ShowResponse(
            modelfile=modelfile,
            parameters=parameters,
            template="",  # Template info not available in our config
            details=ModelDetails(
                format="gguf",
                family=model_config.metadata.family or "unknown",
                parameter_size=model_config.metadata.parameter_count or "unknown",
                quantization_level=model_config.metadata.quantization or "unknown"
            )
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to show model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to show model: {str(e)}"
        )

@router.get("/version")
async def get_version():
    """
    Get Ollama-compatible version information.
    
    Returns:
        Version information
    """
    return {
        "version": "0.1.0",
        "go_version": "n/a",
        "git_commit": "llamacontroller"
    }

@router.get("/ps")
async def list_running_models(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    List running models (Ollama-compatible endpoint).
    
    Returns:
        ProcessResponse with running models
    """
    try:
        current_model = lifecycle.get_current_model()
        
        if current_model is None:
            return ProcessResponse(models=[])
        
        # Get file size
        size = 0
        if os.path.exists(current_model.path):
            size = os.path.getsize(current_model.path)
        
        running_model = RunningModel(
            name=current_model.id,
            model=current_model.id,
            size=size,
            digest=f"sha256:{current_model.id}",
            details=ModelDetails(
                format="gguf",
                family=current_model.metadata.family or "unknown",
                parameter_size=current_model.metadata.parameter_count or "unknown",
                quantization_level=current_model.metadata.quantization or "unknown"
            ),
            expires_at=datetime.utcnow().isoformat() + "Z",
            size_vram=0  # VRAM size not tracked yet
        )
        
        return ProcessResponse(models=[running_model])
        
    except Exception as e:
        logger.error(f"Failed to list running models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list running models: {str(e)}"
        )

@router.delete("/delete")
async def delete_model(
    request: DeleteRequest,
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a model (Ollama-compatible endpoint).
    
    Note: This endpoint is not fully supported as we don't manage model files,
    only model configurations.
    
    Args:
        request: DeleteRequest with model name
        
    Returns:
        Success response
    """
    logger.warning(f"Delete model requested but not supported: {request.name}")
    
    # We don't actually delete models, just return an error
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Model deletion is not supported. LlamaController manages model configurations, not model files."
    )
