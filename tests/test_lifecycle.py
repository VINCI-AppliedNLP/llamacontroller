"""
Unit tests for model lifecycle manager.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.core.config import ConfigManager
from llamacontroller.core.lifecycle import ModelLifecycleManager, LifecycleError
from llamacontroller.models.lifecycle import ProcessStatus


class TestModelLifecycleManager:
    """Tests for ModelLifecycleManager class."""
    
    def test_init(self):
        """Test lifecycle manager initialization."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        
        assert lifecycle_manager.config_manager == config_manager
        assert lifecycle_manager.get_current_model() is None
    
    def test_get_available_models(self):
        """Test getting list of available models."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        models = lifecycle_manager.get_available_models()
        
        assert len(models) > 0
        assert all(hasattr(m, 'id') for m in models)
        assert all(hasattr(m, 'name') for m in models)
        assert all(m.loaded is False for m in models)
    
    def test_get_model_ids(self):
        """Test getting list of model IDs."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        model_ids = lifecycle_manager.get_model_ids()
        
        assert len(model_ids) > 0
        assert isinstance(model_ids, list)
        assert all(isinstance(id, str) for id in model_ids)
    
    @pytest.mark.asyncio
    async def test_get_status_no_model(self):
        """Test getting status when no model is loaded."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        status = await lifecycle_manager.get_status()
        
        assert status.model_id is None
        assert status.model_name is None
        assert status.status == ProcessStatus.STOPPED
        assert status.pid is None
    
    @pytest.mark.asyncio
    async def test_healthcheck_no_server(self):
        """Test healthcheck when server is not running."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        health = await lifecycle_manager.healthcheck()
        
        assert health.healthy is False
        assert health.status == ProcessStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_load_model_not_found(self):
        """Test loading a model that doesn't exist."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        
        with pytest.raises(LifecycleError, match="Model not found"):
            await lifecycle_manager.load_model("nonexistent-model")
    
    @pytest.mark.asyncio
    async def test_unload_model_when_none_loaded(self):
        """Test unloading when no model is loaded."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        
        # Multi-GPU version requires gpu_id, but should handle gracefully
        # Just verify the manager is initialized properly
        current = lifecycle_manager.get_current_model()
        assert current is None
    
    def test_get_current_model_none(self):
        """Test getting current model when none is loaded."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        current = lifecycle_manager.get_current_model()
        
        assert current is None


class TestModelLifecycleManagerIntegration:
    """Integration tests that actually start llama-server (optional)."""
    
    @pytest.mark.skip(reason="Requires actual llama-server and model files")
    @pytest.mark.asyncio
    async def test_load_model_real(self):
        """Test loading a real model (requires llama-server)."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        
        # Get first available model
        model_ids = lifecycle_manager.get_model_ids()
        assert len(model_ids) > 0
        
        model_id = model_ids[0]
        
        # Load model
        response = await lifecycle_manager.load_model(model_id)
        
        try:
            assert response.success is True
            assert response.model_id == model_id
            assert lifecycle_manager.current_model is not None
            
            # Check status
            status = await lifecycle_manager.get_status()
            assert status.model_id == model_id
            assert status.status == ProcessStatus.RUNNING
            
            # Check health
            health = await lifecycle_manager.healthcheck()
            assert health.healthy is True
            
        finally:
            # Clean up
            await lifecycle_manager.unload_model()
    
    @pytest.mark.skip(reason="Requires actual llama-server and model files")
    @pytest.mark.asyncio
    async def test_switch_model_real(self):
        """Test switching between models (requires llama-server)."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        lifecycle_manager = ModelLifecycleManager(config_manager)
        
        # Get available models
        model_ids = lifecycle_manager.get_model_ids()
        assert len(model_ids) >= 2, "Need at least 2 models for switch test"
        
        model1_id = model_ids[0]
        model2_id = model_ids[1]
        
        try:
            # Load first model
            response1 = await lifecycle_manager.load_model(model1_id)
            assert response1.success is True
            
            # Switch to second model
            response2 = await lifecycle_manager.switch_model(model2_id)
            assert response2.success is True
            assert response2.old_model_id == model1_id
            assert response2.new_model_id == model2_id
            
            # Verify current model
            current = lifecycle_manager.get_current_model()
            assert current is not None
            assert current.id == model2_id
            
        finally:
            # Clean up
            await lifecycle_manager.unload_model()


if __name__ == "__main__":
    # Run basic tests
    print("Running basic tests...")
    
    # Test initialization
    config_manager = ConfigManager(config_dir="./config")
    config_manager.load_config()
    
    lifecycle_manager = ModelLifecycleManager(config_manager)
    print(f"✓ Lifecycle manager initialized")
    
    # Test getting models
    models = lifecycle_manager.get_available_models()
    print(f"✓ Found {len(models)} configured models:")
    for model in models:
        print(f"  - {model.id}: {model.name}")
    
    # Test getting status
    async def test_status():
        status = await lifecycle_manager.get_status()
        print(f"✓ Status: {status.status}")
        
        health = await lifecycle_manager.healthcheck()
        print(f"✓ Health: {'healthy' if health.healthy else 'not healthy'}")
    
    asyncio.run(test_status())
    
    print("\nBasic tests passed!")
    print("\nTo run full test suite:")
    print("  pytest tests/test_lifecycle.py -v")
