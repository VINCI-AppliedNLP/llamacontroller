# LlamaController

A WebUI-based management system for llama.cpp model lifecycle with Ollama API compatibility.

## 🎯 Project Overview

LlamaController provides a secure, web-based interface to manage llama.cpp instances with full model lifecycle control (load, unload, switch) while maintaining compatibility with Ollama's REST API ecosystem. This allows existing Ollama-compatible applications to seamlessly work with llama.cpp deployments.

## ✨ Features

- **Centralized Model Management**: Single interface to control multiple models
- **API Compatibility**: Drop-in replacement for Ollama in existing workflows
- **Configuration Isolation**: Separate llama.cpp binaries from model configurations
- **Secure Access**: Protected by authentication with token-based API access
- **Multi-tenancy Support**: Different tokens for different applications/users
- **Web Interface**: User-friendly dashboard for model management

## 📋 Prerequisites

- Python 3.8+ (Conda environment recommended)
- llama.cpp installed with `llama-server` executable
- GGUF model files

## 🚀 Quick Start

### 1. Set up Conda Environment

```powershell
# Create and activate conda environment
conda create -n llama.cpp python=3.11 -y
conda activate llama.cpp
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure

Copy the example configurations and edit with your paths:

```powershell
# The config files are already in config/ directory
# Edit them to match your system:
# - config/llamacpp-config.yaml
# - config/models-config.yaml
# - config/auth-config.yaml
```

### 4. Run LlamaController

```powershell
# Coming soon - main entry point
python -m src.llamacontroller.main
```

## 📁 Project Structure

```
llamacontroller/
├── src/llamacontroller/       # Main application code
│   ├── core/                  # Core business logic
│   ├── api/                   # REST API endpoints
│   ├── auth/                  # Authentication
│   ├── db/                    # Database models
│   ├── web/                   # Web UI
│   ├── models/                # Pydantic models
│   └── utils/                 # Utilities
├── config/                    # Configuration files
├── tests/                     # Test suite
├── docs/                      # Documentation
├── design/                    # Design documents
├── scripts/                   # Utility scripts
├── logs/                      # Application logs
└── data/                      # Runtime data
```

## 🔧 Development Status

This project is currently under active development.

### Phase 1: Foundation ✅ (In Progress)
- [x] Project structure
- [x] Configuration files
- [ ] Configuration manager
- [ ] llama.cpp process adapter
- [ ] Logging system

### Phase 2: Model Lifecycle 🔄 (Planned)
- [ ] Model lifecycle manager
- [ ] Load/unload/switch operations

### Phase 3: API Layer 🔄 (Planned)
- [ ] FastAPI application
- [ ] Ollama-compatible endpoints

### Phase 4: Authentication 🔄 (Planned)
- [ ] User authentication
- [ ] API token system

### Phase 5: Web UI 🔄 (Planned)
- [ ] Dashboard interface
- [ ] Token management

### Phase 6: Testing & Documentation 🔄 (Planned)
- [ ] Comprehensive testing
- [ ] User documentation

## 📖 Documentation

- [Project Overview](design/01-overview.md)
- [Development Setup](design/03-development-setup.md)
- [Architecture](design/04-architecture.md)
- [Implementation Guide](design/05-implementation-guide.md)

## 🤝 Contributing

This project is currently in initial development. Contribution guidelines will be added soon.

## 📝 License

To be determined.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) - The underlying inference engine
- [Ollama](https://ollama.ai/) - API specification inspiration

---

**Status**: Development Phase  
**Version**: 0.1.0  
**Last Updated**: 2025-11-12
