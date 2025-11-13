"""
Model lifecycle manager for high-level model operations.
"""

import logging
import asyncio
from typing import Optional, List
from datetime import datetime

from .config import ConfigManager
from .adapter import LlamaCppAdapter, AdapterError
from ..models.config import ModelConfig
from ..models.lifecycle import (
    ProcessStatus,
    ModelStatus,
    LoadModelResponse,
    UnloadModelResponse,
    SwitchModelResponse,
    ModelInfo,
    HealthCheckResponse,
)

logger = logging.getLogger(__name__)

class LifecycleError(Exception):
    """Exception raised for lifecycle management errors."""
    pass

class ModelLifecycleManager:
    """
    High-level model lifecycle management.
    
    Provides operations for loading, unloading, and switching models
    while managing the underlying llama.cpp process adapter.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the lifecycle manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.current_model: Optional[ModelConfig] = None
        self.load_time: Optional[datetime] = None
        
        # Initialize adapter with llama.cpp config
        llama_config = config_manager.llama_cpp
        self.adapter = LlamaCppAdapter(llama_config)
        
        logger.info("ModelLifecycleManager initialized")
    
    async def load_model(self, model_id: str) -> LoadModelResponse:
        """
        Load a model by ID.
        
        Args:
            model_id: ID of the model to load
            
        Returns:
            LoadModelResponse with operation result
            
        Raises:
            LifecycleError: If model loading fails
        """
        logger.info(f"Loading model: {model_id}")
        
        try:
            # Get model configuration
            model_config = self.config_manager.models.get_model(model_id)
            if model_config is None:
                raise LifecycleError(f"Model not found: {model_id}")
            
            # Check if a model is already loaded
            if self.current_model is not None:
                raise LifecycleError(
                    f"Model '{self.current_model.id}' is already loaded. "
                    f"Unload it first or use switch_model()."
                )
            
            # Start llama-server with the model
            try:
                self.adapter.start_server(
                    model_path=model_config.path,
                    params=model_config.parameters
                )
            except AdapterError as e:
                raise LifecycleError(f"Failed to start server: {e}")
            
            # Wait for server to be ready
            logger.info("Waiting for server to be ready...")
            ready = await self._wait_for_ready(timeout=60)
            
            if not ready:
                # Server didn't become ready in time
                self.adapter.stop_server()
                raise LifecycleError("Server failed to become ready within timeout")
            
            # Update state
            self.current_model = model_config
            self.load_time = datetime.now()
            
            status = await self.get_status()
            
            logger.info(f"Model '{model_id}' loaded successfully")
            
            return LoadModelResponse(
                success=True,
                model_id=model_id,
                message=f"Model '{model_config.name}' loaded successfully",
                status=status
            )
            
        except LifecycleError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading model: {e}")
            raise LifecycleError(f"Failed to load model: {e}")
    
    async def unload_model(self) -> UnloadModelResponse:
        """
        Unload the currently loaded model.
        
        Returns:
            UnloadModelResponse with operation result
        """
        logger.info("Unloading current model")
        
        if self.current_model is None:
            return UnloadModelResponse(
                success=True,
                message="No model loaded"
            )
        
        model_id = self.current_model.id
        
        try:
            # Stop the server
            success = self.adapter.stop_server(graceful=True, timeout=30)
            
            if not success:
                raise LifecycleError("Failed to stop server")
            
            # Clear state
            self.current_model = None
            self.load_time = None
            
            logger.info(f"Model '{model_id}' unloaded successfully")
            
            return UnloadModelResponse(
                success=True,
                message=f"Model '{model_id}' unloaded successfully"
            )
            
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
            raise LifecycleError(f"Failed to unload model: {e}")
    
    async def switch_model(self, new_model_id: str) -> SwitchModelResponse:
        """
        Switch from current model to a new model.
        
        Args:
            new_model_id: ID of the model to switch to
            
        Returns:
            SwitchModelResponse with operation result
        """
        old_model_id = self.current_model.id if self.current_model else None
        
        logger.info(f"Switching model from '{old_model_id}' to '{new_model_id}'")
        
        try:
            # Validate new model exists
            new_model_config = self.config_manager.models.get_model(new_model_id)
            if new_model_config is None:
                raise LifecycleError(f"Model not found: {new_model_id}")
            
            # If same model, just return current status
            if old_model_id == new_model_id:
                status = await self.get_status()
                return SwitchModelResponse(
                    success=True,
                    old_model_id=old_model_id,
                    new_model_id=new_model_id,
                    message=f"Model '{new_model_id}' is already loaded",
                    status=status
                )
            
            # Unload current model if any
            if self.current_model is not None:
                logger.info(f"Unloading current model: {old_model_id}")
                await self.unload_model()
                # Brief pause to ensure clean shutdown
                await asyncio.sleep(1)
            
            # Load new model
            logger.info(f"Loading new model: {new_model_id}")
            load_response = await self.load_model(new_model_id)
            
            if not load_response.success:
                raise LifecycleError(f"Failed to load new model: {load_response.message}")
            
            logger.info(f"Successfully switched to model '{new_model_id}'")
            
            return SwitchModelResponse(
                success=True,
                old_model_id=old_model_id,
                new_model_id=new_model_id,
                message=f"Successfully switched to model '{new_model_config.name}'",
                status=load_response.status
            )
            
        except LifecycleError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error switching model: {e}")
            raise LifecycleError(f"Failed to switch model: {e}")
    
    def get_current_model(self) -> Optional[ModelConfig]:
        """
        Get the currently loaded model configuration.
        
        Returns:
            ModelConfig if a model is loaded, None otherwise
        """
        return self.current_model
    
    async def get_status(self) -> ModelStatus:
        """
        Get current model status.
        
        Returns:
            ModelStatus with current state
        """
        status = ModelStatus(
            model_id=self.current_model.id if self.current_model else None,
            model_name=self.current_model.name if self.current_model else None,
            status=self.adapter.get_status(),
            loaded_at=self.load_time,
            memory_usage_mb=None,  # TODO: Implement memory tracking
            uptime_seconds=self.adapter.get_uptime_seconds(),
            pid=self.adapter.get_pid(),
            host=self.config_manager.llama_cpp.default_host,
            port=self.config_manager.llama_cpp.default_port,
        )
        
        return status
    
    async def healthcheck(self) -> HealthCheckResponse:
        """
        Check if the current model is healthy.
        
        Returns:
            HealthCheckResponse with health status
        """
        status = self.adapter.get_status()
        
        if status != ProcessStatus.RUNNING:
            return HealthCheckResponse(
                healthy=False,
                status=status,
                message=f"Server is {status.value}",
                uptime_seconds=None
            )
        
        # Check if server is responding
        is_healthy = await self.adapter.is_healthy()
        
        uptime = self.adapter.get_uptime_seconds()
        
        if is_healthy:
            return HealthCheckResponse(
                healthy=True,
                status=status,
                message="Server is healthy and responding",
                uptime_seconds=uptime
            )
        else:
            return HealthCheckResponse(
                healthy=False,
                status=status,
                message="Server is running but not responding to health checks",
                uptime_seconds=uptime
            )
    
    def get_available_models(self) -> List[ModelInfo]:
        """
        Get list of available models.
        
        Returns:
            List of ModelInfo for all configured models
        """
        models = []
        current_id = self.current_model.id if self.current_model else None
        
        for model_config in self.config_manager.models.models:
            is_loaded = (model_config.id == current_id)
            status = "loaded" if is_loaded else "available"
            
            models.append(ModelInfo(
                id=model_config.id,
                name=model_config.name,
                path=model_config.path,
                status=status,
                loaded=is_loaded,
                description=model_config.metadata.description,
                parameter_count=model_config.metadata.parameter_count,
                quantization=model_config.metadata.quantization,
            ))
        
        return models
    
    def get_model_ids(self) -> List[str]:
        """
        Get list of available model IDs.
        
        Returns:
            List of model IDs
        """
        return self.config_manager.models.get_model_ids()
    
    async def _wait_for_ready(self, timeout: int = 60) -> bool:
        """
        Wait for llama-server to be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if server became ready, False if timeout
        """
        start_time = asyncio.get_event_loop().time()
        check_interval = 1.0  # Check every second
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if server is healthy
            is_healthy = await self.adapter.is_healthy()
            
            if is_healthy:
                logger.info("Server is ready")
                return True
            
            # Wait before next check
            await asyncio.sleep(check_interval)
        
        logger.warning(f"Server did not become ready within {timeout}s")
        return False
    
    async def get_server_logs(self, lines: int = 300) -> List[str]:
        """
        Get recent server log lines.
        
        Args:
            lines: Number of recent lines to return (default: 300, max: 300)
            
        Returns:
            List of log lines
        """
        # Cap at 300 since that's the buffer size
        lines = min(lines, 300)
        return self.adapter.get_logs(lines=lines)
    
    def __del__(self):
        """Cleanup when lifecycle manager is destroyed."""
        if self.current_model is not None:
            logger.warning("LifecycleManager being destroyed with loaded model")
            # Note: Can't use async in __del__, so we just log
