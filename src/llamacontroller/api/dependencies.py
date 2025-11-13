"""
FastAPI dependencies for dependency injection.
"""

from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from functools import lru_cache
from sqlalchemy.orm import Session

from ..core.config import ConfigManager
from ..core.lifecycle import ModelLifecycleManager
from ..db.base import SessionLocal

# Global instances (will be initialized on app startup)
_config_manager: Optional[ConfigManager] = None
_lifecycle_manager: Optional[ModelLifecycleManager] = None

def initialize_managers(config_dir: str = "./config"):
    """
    Initialize global manager instances.
    
    This should be called during application startup.
    
    Args:
        config_dir: Path to configuration directory
    """
    global _config_manager, _lifecycle_manager
    
    _config_manager = ConfigManager(config_dir=config_dir)
    _config_manager.load_config()  # Load configuration first
    _lifecycle_manager = ModelLifecycleManager(_config_manager)

def get_config_manager() -> ConfigManager:
    """
    Get the ConfigManager instance.
    
    Returns:
        ConfigManager instance
        
    Raises:
        HTTPException: If managers not initialized
    """
    if _config_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration manager not initialized"
        )
    return _config_manager

def get_lifecycle_manager() -> ModelLifecycleManager:
    """
    Get the ModelLifecycleManager instance.
    
    Returns:
        ModelLifecycleManager instance
        
    Raises:
        HTTPException: If managers not initialized
    """
    if _lifecycle_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lifecycle manager not initialized"
        )
    return _lifecycle_manager

async def verify_model_loaded(
    lifecycle: ModelLifecycleManager = Depends(get_lifecycle_manager)
) -> ModelLifecycleManager:
    """
    Verify that a model is currently loaded.
    
    Args:
        lifecycle: ModelLifecycleManager instance
        
    Returns:
        ModelLifecycleManager instance
        
    Raises:
        HTTPException: If no model is loaded
    """
    if lifecycle.current_model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No model is currently loaded"
        )
    return lifecycle

def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
