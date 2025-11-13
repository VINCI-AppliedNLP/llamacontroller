"""
LlamaController - A WebUI-based management system for llama.cpp model lifecycle.

This package provides a web interface and REST API to manage llama.cpp instances
with full model lifecycle control while maintaining Ollama API compatibility.
"""

__version__ = "0.1.0"
__author__ = "LlamaController Team"

# Import only what exists
from .core.config import ConfigManager

__all__ = [
    "ConfigManager",
]
