"""
Pydantic models for Ollama-compatible API schemas.
Based on Ollama API specification.
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# Ollama API Models

class GenerateRequest(BaseModel):
    """Request for text generation (Ollama /api/generate endpoint)."""
    model: str = Field(..., description="Model name to use for generation")
    prompt: str = Field(..., description="The prompt to generate a response for")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images for multimodal models")
    format: Optional[Literal["json"]] = Field(None, description="Format of the response (json)")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional model parameters")
    system: Optional[str] = Field(None, description="System message to use")
    template: Optional[str] = Field(None, description="Prompt template to use")
    context: Optional[List[int]] = Field(None, description="Context from previous generation")
    stream: Optional[bool] = Field(True, description="Whether to stream the response")
    raw: Optional[bool] = Field(False, description="Whether to use raw mode (no formatting)")
    keep_alive: Optional[str] = Field(None, description="How long to keep model loaded")

class GenerateResponse(BaseModel):
    """Response for text generation."""
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None

class ChatMessage(BaseModel):
    """A chat message."""
    role: Literal["system", "user", "assistant"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images")

class ChatRequest(BaseModel):
    """Request for chat completion (Ollama /api/chat endpoint)."""
    model: str = Field(..., description="Model name to use")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    format: Optional[Literal["json"]] = Field(None, description="Format of the response")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional model parameters")
    stream: Optional[bool] = Field(True, description="Whether to stream the response")
    keep_alive: Optional[str] = Field(None, description="How long to keep model loaded")

class ChatResponse(BaseModel):
    """Response for chat completion."""
    model: str
    created_at: str
    message: ChatMessage
    done: bool
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None

class ModelDetails(BaseModel):
    """Details about a model."""
    format: str
    family: str
    families: Optional[List[str]] = None
    parameter_size: str
    quantization_level: str

class ModelInfo(BaseModel):
    """Information about a model (Ollama /api/tags response item)."""
    name: str
    model: str
    modified_at: str
    size: int
    digest: str
    details: ModelDetails

class TagsResponse(BaseModel):
    """Response for listing models (Ollama /api/tags endpoint)."""
    models: List[ModelInfo]

class ShowRequest(BaseModel):
    """Request to show model information (Ollama /api/show endpoint)."""
    name: str = Field(..., description="Name of the model to show")

class ShowResponse(BaseModel):
    """Response with model information."""
    model_config = ConfigDict(protected_namespaces=())
    
    modelfile: str
    parameters: str
    template: str
    details: ModelDetails
    model_info: Optional[Dict[str, Any]] = None

class RunningModel(BaseModel):
    """Information about a running model."""
    name: str
    model: str
    size: int
    digest: str
    details: ModelDetails
    expires_at: str
    size_vram: int

class ProcessResponse(BaseModel):
    """Response for listing running models (Ollama /api/ps endpoint)."""
    models: List[RunningModel]

class PullRequest(BaseModel):
    """Request to pull a model (Ollama /api/pull endpoint)."""
    name: str = Field(..., description="Name of the model to pull")
    insecure: Optional[bool] = Field(False, description="Allow insecure connections")
    stream: Optional[bool] = Field(True, description="Stream the response")

class PullResponse(BaseModel):
    """Response for pulling a model."""
    status: str
    digest: Optional[str] = None
    total: Optional[int] = None
    completed: Optional[int] = None

class PushRequest(BaseModel):
    """Request to push a model (Ollama /api/push endpoint)."""
    name: str = Field(..., description="Name of the model to push")
    insecure: Optional[bool] = Field(False, description="Allow insecure connections")
    stream: Optional[bool] = Field(True, description="Stream the response")

class PushResponse(BaseModel):
    """Response for pushing a model."""
    status: str
    digest: Optional[str] = None
    total: Optional[int] = None

class CreateRequest(BaseModel):
    """Request to create a model (Ollama /api/create endpoint)."""
    name: str = Field(..., description="Name of the model to create")
    modelfile: str = Field(..., description="Modelfile contents")
    stream: Optional[bool] = Field(True, description="Stream the response")

class CreateResponse(BaseModel):
    """Response for creating a model."""
    status: str

class DeleteRequest(BaseModel):
    """Request to delete a model (Ollama /api/delete endpoint)."""
    name: str = Field(..., description="Name of the model to delete")

class CopyRequest(BaseModel):
    """Request to copy a model (Ollama /api/copy endpoint)."""
    source: str = Field(..., description="Name of the model to copy from")
    destination: str = Field(..., description="Name of the model to copy to")

class EmbeddingsRequest(BaseModel):
    """Request for embeddings (Ollama /api/embeddings endpoint)."""
    model: str = Field(..., description="Model name to use")
    prompt: str = Field(..., description="Text to generate embeddings for")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional model parameters")
    keep_alive: Optional[str] = Field(None, description="How long to keep model loaded")

class EmbeddingsResponse(BaseModel):
    """Response for embeddings."""
    embedding: List[float]

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
