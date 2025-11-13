"""
Configuration manager for loading and validating YAML configurations.
"""

import yaml
from pathlib import Path
from typing import Optional
import logging

from ..models.config import (
    AppConfig,
    LlamaCppConfig,
    ModelsConfig,
    AuthConfig,
)

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigManager:
    """
    Manages loading and validation of configuration files.
    
    Loads YAML configuration files and validates them using Pydantic models.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files.
                       Defaults to './config'
        """
        self.config_dir = Path(config_dir or "./config")
        self._config: Optional[AppConfig] = None
        
        if not self.config_dir.exists():
            raise ConfigError(f"Configuration directory not found: {self.config_dir}")
        
        logger.info(f"ConfigManager initialized with directory: {self.config_dir}")
    
    def load_yaml_file(self, filename: str) -> dict:
        """
        Load a YAML file from the config directory.
        
        Args:
            filename: Name of the YAML file to load
            
        Returns:
            Dictionary containing the parsed YAML data
            
        Raises:
            ConfigError: If file cannot be loaded or parsed
        """
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            raise ConfigError(f"Configuration file not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data is None:
                    raise ConfigError(f"Configuration file is empty: {filepath}")
                return data
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML file {filepath}: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to read configuration file {filepath}: {e}")
    
    def load_llama_cpp_config(self) -> LlamaCppConfig:
        """
        Load llama.cpp configuration.
        
        Returns:
            LlamaCppConfig instance
            
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            data = self.load_yaml_file("llamacpp-config.yaml")
            return LlamaCppConfig(**data.get("llama_cpp", {}))
        except ValueError as e:
            raise ConfigError(f"Invalid llama.cpp configuration: {e}")
    
    def load_models_config(self) -> ModelsConfig:
        """
        Load models configuration.
        
        Returns:
            ModelsConfig instance
            
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            data = self.load_yaml_file("models-config.yaml")
            return ModelsConfig(**data)
        except ValueError as e:
            raise ConfigError(f"Invalid models configuration: {e}")
    
    def load_auth_config(self) -> AuthConfig:
        """
        Load authentication configuration.
        
        Returns:
            AuthConfig instance
            
        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            data = self.load_yaml_file("auth-config.yaml")
            return AuthConfig(**data.get("authentication", {}))
        except ValueError as e:
            raise ConfigError(f"Invalid authentication configuration: {e}")
    
    def load_config(self) -> AppConfig:
        """
        Load all configuration files and validate them.
        
        Returns:
            AppConfig instance containing all configurations
            
        Raises:
            ConfigError: If any configuration is invalid
        """
        logger.info("Loading configuration files...")
        
        try:
            llama_cpp_config = self.load_llama_cpp_config()
            logger.info("✓ llama.cpp configuration loaded")
            
            models_config = self.load_models_config()
            logger.info(f"✓ Models configuration loaded ({len(models_config.models)} models)")
            
            auth_config = self.load_auth_config()
            logger.info(f"✓ Authentication configuration loaded ({len(auth_config.users)} users)")
            
            self._config = AppConfig(
                llama_cpp=llama_cpp_config,
                models=models_config,
                auth=auth_config
            )
            
            logger.info("✓ All configurations loaded and validated successfully")
            return self._config
            
        except ConfigError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            raise ConfigError(f"Failed to load configuration: {e}")
    
    def reload_config(self) -> AppConfig:
        """
        Reload all configuration files.
        
        Returns:
            AppConfig instance with reloaded configurations
            
        Raises:
            ConfigError: If any configuration is invalid
        """
        logger.info("Reloading configuration files...")
        return self.load_config()
    
    def get_config(self) -> AppConfig:
        """
        Get the current configuration.
        
        Returns:
            AppConfig instance
            
        Raises:
            ConfigError: If configuration has not been loaded yet
        """
        if self._config is None:
            raise ConfigError("Configuration not loaded. Call load_config() first.")
        return self._config
    
    def validate_config(self) -> list[str]:
        """
        Validate current configuration and return any warnings.
        
        Returns:
            List of warning messages (empty if no warnings)
        """
        warnings = []
        
        if self._config is None:
            return ["Configuration not loaded"]
        
        # Check if any models are configured
        if not self._config.models.models:
            warnings.append("No models configured")
        
        # Check if any users are configured
        if not self._config.auth.users:
            warnings.append("No users configured - authentication will not work")
        
        # Check for default passwords
        for user in self._config.auth.users:
            if user.password in ["admin123", "password", "12345"]:
                warnings.append(
                    f"User '{user.username}' has a weak default password. "
                    "Change it in production!"
                )
        
        return warnings
    
    @property
    def llama_cpp(self) -> LlamaCppConfig:
        """Get llama.cpp configuration."""
        return self.get_config().llama_cpp
    
    @property
    def models(self) -> ModelsConfig:
        """Get models configuration."""
        return self.get_config().models
    
    @property
    def auth(self) -> AuthConfig:
        """Get authentication configuration."""
        return self.get_config().auth
