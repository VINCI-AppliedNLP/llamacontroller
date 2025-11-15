"""
Unit tests for configuration management.

These tests validate the configuration loading and validation logic.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from llamacontroller.core.config import ConfigManager, ConfigError
from llamacontroller.models.config import (
    LlamaCppConfig,
    ModelConfig,
    ModelsConfig,
    AuthConfig,
)


class TestConfigManager:
    """Test ConfigManager class."""
    
    def test_init_with_valid_directory(self):
        """Test initialization with valid config directory."""
        config_manager = ConfigManager(config_dir="./config")
        assert config_manager.config_dir == Path("./config")
    
    def test_init_with_invalid_directory(self):
        """Test initialization with invalid config directory."""
        with pytest.raises(ConfigError, match="Configuration directory not found"):
            ConfigManager(config_dir="./nonexistent")
    
    def test_load_yaml_file_success(self):
        """Test loading a valid YAML file."""
        config_manager = ConfigManager(config_dir="./config")
        data = config_manager.load_yaml_file("llamacpp-config.yaml")
        assert isinstance(data, dict)
        assert "llama_cpp" in data
    
    def test_load_yaml_file_not_found(self):
        """Test loading a non-existent YAML file."""
        config_manager = ConfigManager(config_dir="./config")
        with pytest.raises(ConfigError, match="Configuration file not found"):
            config_manager.load_yaml_file("nonexistent.yaml")
    
    def test_load_llama_cpp_config(self):
        """Test loading llama.cpp configuration."""
        config_manager = ConfigManager(config_dir="./config")
        llama_config = config_manager.load_llama_cpp_config()
        
        assert isinstance(llama_config, LlamaCppConfig)
        assert llama_config.default_host == "127.0.0.1"
        assert llama_config.default_port == 8080
        assert llama_config.log_level == "info"
        assert llama_config.restart_on_crash is True
    
    def test_load_models_config(self):
        """Test loading models configuration."""
        config_manager = ConfigManager(config_dir="./config")
        models_config = config_manager.load_models_config()
        
        assert isinstance(models_config, ModelsConfig)
        assert len(models_config.models) >= 2
        
        # Check first model
        phi4 = models_config.get_model("phi-4-reasoning")
        assert phi4 is not None
        assert phi4.name == "Phi-4 Reasoning Plus"
        assert phi4.metadata.parameter_count == "14B"
        # Parameters may be in cli_params instead of direct fields
        assert phi4.parameters is not None
    
    def test_load_auth_config(self):
        """Test loading authentication configuration."""
        config_manager = ConfigManager(config_dir="./config")
        auth_config = config_manager.load_auth_config()
        
        assert isinstance(auth_config, AuthConfig)
        assert auth_config.session_timeout == 3600
        assert auth_config.max_login_attempts == 5
        assert len(auth_config.users) == 1
        assert auth_config.users[0].username == "admin"
    
    def test_load_config_integration(self):
        """Test loading all configurations together."""
        config_manager = ConfigManager(config_dir="./config")
        config = config_manager.load_config()
        
        # Verify all components loaded
        assert config.llama_cpp is not None
        assert config.models is not None
        assert config.auth is not None
        
        # Verify can access via properties
        assert config_manager.llama_cpp.default_port == 8080
        assert len(config_manager.models.models) == 2
        assert len(config_manager.auth.users) == 1
    
    def test_get_config_before_load(self):
        """Test getting config before loading."""
        config_manager = ConfigManager(config_dir="./config")
        with pytest.raises(ConfigError, match="Configuration not loaded"):
            config_manager.get_config()
    
    def test_validate_config(self):
        """Test configuration validation."""
        config_manager = ConfigManager(config_dir="./config")
        config_manager.load_config()
        
        warnings = config_manager.validate_config()
        
        # Should have warning about weak password
        assert len(warnings) > 0
        assert any("weak default password" in w.lower() for w in warnings)
    
    def test_reload_config(self):
        """Test reloading configuration."""
        config_manager = ConfigManager(config_dir="./config")
        config1 = config_manager.load_config()
        config2 = config_manager.reload_config()
        
        # Both should be valid and independent instances
        assert config1 is not config2
        assert config1.llama_cpp.default_port == config2.llama_cpp.default_port


class TestModelsConfig:
    """Test ModelsConfig class."""
    
    def test_get_model_by_id(self):
        """Test retrieving model by ID."""
        config_manager = ConfigManager(config_dir="./config")
        models_config = config_manager.load_models_config()
        
        model = models_config.get_model("phi-4-reasoning")
        assert model is not None
        assert model.id == "phi-4-reasoning"
    
    def test_get_nonexistent_model(self):
        """Test retrieving non-existent model."""
        config_manager = ConfigManager(config_dir="./config")
        models_config = config_manager.load_models_config()
        
        model = models_config.get_model("nonexistent")
        assert model is None
    
    def test_get_model_ids(self):
        """Test getting all model IDs."""
        config_manager = ConfigManager(config_dir="./config")
        models_config = config_manager.load_models_config()
        
        ids = models_config.get_model_ids()
        assert len(ids) == 2
        assert "phi-4-reasoning" in ids
        assert "qwen3-coder-30b" in ids


class TestAuthConfig:
    """Test AuthConfig class."""
    
    def test_get_user_by_username(self):
        """Test retrieving user by username."""
        config_manager = ConfigManager(config_dir="./config")
        auth_config = config_manager.load_auth_config()
        
        user = auth_config.get_user("admin")
        assert user is not None
        assert user.username == "admin"
        assert user.role == "admin"
    
    def test_get_nonexistent_user(self):
        """Test retrieving non-existent user."""
        config_manager = ConfigManager(config_dir="./config")
        auth_config = config_manager.load_auth_config()
        
        user = auth_config.get_user("nonexistent")
        assert user is None


class TestConfigValidation:
    """Test configuration validation with invalid data."""
    
    def test_invalid_yaml_syntax(self):
        """Test loading YAML with syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid YAML file
            config_file = Path(tmpdir) / "invalid.yaml"
            config_file.write_text("invalid: yaml: : syntax")
            
            config_manager = ConfigManager(config_dir=tmpdir)
            with pytest.raises(ConfigError, match="Failed to parse YAML"):
                config_manager.load_yaml_file("invalid.yaml")
    
    def test_empty_yaml_file(self):
        """Test loading empty YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create empty YAML file
            config_file = Path(tmpdir) / "empty.yaml"
            config_file.write_text("")
            
            config_manager = ConfigManager(config_dir=tmpdir)
            with pytest.raises(ConfigError, match="Configuration file is empty"):
                config_manager.load_yaml_file("empty.yaml")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
