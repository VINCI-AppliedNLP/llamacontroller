# Technical Architecture

## System Architecture Overview

LlamaController follows a modular architecture with clear separation of concerns:

\\\
┌─────────────────────────────────────────────────────────────┐
│                      Web Browser                             │
│                   (User Interface)                           │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS/HTTP
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                  LlamaController Service                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Web UI Module (FastAPI/Flask)            │  │
│  │  • Authentication (Session-based)                     │  │
│  │  • Dashboard Views                                    │  │
│  │  • Token Management UI                                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         REST API Module (FastAPI/Flask)               │  │
│  │  • Ollama-compatible endpoints                        │  │
│  │  • Token-based authentication                         │  │
│  │  • Request validation & routing                       │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Model Lifecycle Manager                      │  │
│  │  • Load/Unload/Switch operations                      │  │
│  │  • Process management                                 │  │
│  │  • Health monitoring                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        llama.cpp Process Adapter                      │  │
│  │  • Process lifecycle management                       │  │
│  │  • Request proxying                                   │  │
│  │  • Log capture & parsing                              │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Configuration Manager                          │  │
│  │  • YAML config loading/validation                     │  │
│  │  • Hot-reload support                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Authentication & Authorization                │  │
│  │  • User authentication (bcrypt)                       │  │
│  │  • Token management (JWT/UUID)                        │  │
│  │  • Session management                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Data Persistence Layer                     │  │
│  │  • SQLite for tokens/sessions/logs                    │  │
│  │  • File-based config storage                          │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │ Subprocess
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              llama.cpp Server Process                        │
│                 (llama-server.exe)                           │
│  • HTTP Server on localhost:8080                            │
│  • Model inference                                          │
│  • Managed by LlamaController                               │
└─────────────────────────────────────────────────────────────┘
\\\

## Technology Stack

### Backend Framework
**Recommended: FastAPI** (Python)
- **Pros**:
  - Built-in OpenAPI documentation
  - Excellent async support for proxying requests
  - Type hints for better code quality
  - Easy WebSocket support for streaming
  - Fast performance
- **Alternative: Flask**
  - Simpler, more mature
  - Large ecosystem
  - Good for synchronous operations

### Web UI Framework
**Options**:
1. **Server-side templates** (Jinja2) - Simple, no JS build process
2. **Modern SPA** (React/Vue) - Better UX but adds complexity
3. **HTMX** - Modern UX with minimal JS (Recommended middle-ground)

### Data Storage
- **SQLite**: User credentials, API tokens, session data, operation logs
- **YAML files**: Configuration (human-editable)

### Key Python Libraries
\\\yaml
dependencies:
  web_framework: "fastapi>=0.104.0"
  server: "uvicorn>=0.24.0"
  config: "pyyaml>=6.0"
  auth: "bcrypt>=4.0.0"
  tokens: "pyjwt>=2.8.0"  # or python-jose
  database: "sqlalchemy>=2.0"
  http_client: "httpx>=0.25.0"  # async requests to llama.cpp
  validation: "pydantic>=2.0"
  templates: "jinja2>=3.1.0"
  
optional:
  monitoring: "prometheus-client"
  testing: "pytest>=7.4.0"
  testing_async: "pytest-asyncio"
\\\

## Core Components

### 1. Model Lifecycle Manager

**Responsibilities**:
- Load models based on configuration
- Manage llama.cpp server process
- Handle model switching atomically
- Monitor model health

**Key Classes**:
\\\python
class ModelLifecycleManager:
    def load_model(model_id: str) -> ModelStatus
    def unload_model() -> None
    def switch_model(from_id: str, to_id: str) -> ModelStatus
    def get_current_model() -> Optional[ModelInfo]
    def get_model_status() -> ModelStatus
    async def healthcheck() -> bool
\\\

### 2. llama.cpp Process Adapter

**Responsibilities**:
- Start/stop llama-server subprocess
- Monitor process health
- Capture and parse logs
- Restart on crash
- Proxy requests to llama.cpp

**Key Classes**:
\\\python
class LlamaCppAdapter:
    def start_server(model_path: str, params: dict) -> Process
    def stop_server(graceful: bool = True) -> None
    def restart_server() -> None
    def is_healthy() -> bool
    async def proxy_request(endpoint: str, data: dict) -> Response
    def get_logs(lines: int = 100) -> List[str]
\\\

### 3. Configuration Manager

**Responsibilities**:
- Load and validate YAML configurations
- Provide configuration access
- Support hot-reload
- Validate paths and parameters

**Key Classes**:
\\\python
class ConfigManager:
    def load_configs() -> Config
    def reload_configs() -> Config
    def validate_config() -> List[ConfigError]
    def get_model_config(model_id: str) -> ModelConfig
    def get_llama_config() -> LlamaCppConfig
\\\

### 4. Authentication Service

**Responsibilities**:
- User authentication
- API token generation and validation
- Session management
- Rate limiting

**Key Classes**:
\\\python
class AuthService:
    def authenticate_user(username: str, password: str) -> Optional[User]
    def create_session(user: User) -> Session
    def validate_session(session_id: str) -> Optional[Session]
    def create_api_token(name: str, user: User) -> ApiToken
    def validate_api_token(token: str) -> Optional[ApiToken]
    def revoke_token(token_id: str) -> bool
\\\

### 5. Ollama API Compatibility Layer

**Responsibilities**:
- Implement Ollama API endpoints
- Transform requests to llama.cpp format
- Transform responses to Ollama format
- Handle streaming responses

**Key Endpoints**:
\\\python
@app.post("/api/generate")
async def generate_completion(request: GenerateRequest)

@app.post("/api/chat")
async def chat_completion(request: ChatRequest)

@app.get("/api/tags")
async def list_models()

@app.post("/api/show")
async def show_model(request: ShowRequest)

@app.get("/api/ps")
async def list_running_models()

@app.delete("/api/delete")
async def delete_model(request: DeleteRequest)
\\\

## Data Flow

### 1. Model Loading Flow
\\\
User → Web UI → POST /api/v1/models/load
  ↓
Authentication Check
  ↓
Model Lifecycle Manager
  ↓
Configuration Manager (validate model exists)
  ↓
llama.cpp Adapter (start subprocess with params)
  ↓
Health Check (wait for server ready)
  ↓
Update Model Status
  ↓
Return Success/Failure
\\\

### 2. Inference Request Flow (Ollama API)
\\\
Client App → POST /api/generate (with token)
  ↓
Token Validation
  ↓
Request Validation (Pydantic model)
  ↓
Check Model Loaded
  ↓
llama.cpp Adapter (proxy to localhost:8080)
  ↓
Stream/Return Response
  ↓
Log Request (async task)
\\\

### 3. Model Switch Flow
\\\
User → Web UI → POST /api/v1/models/switch
  ↓
Authentication Check
  ↓
Model Lifecycle Manager
  ↓
Queue Pending Requests
  ↓
Graceful Stop Current llama-server
  ↓
Start New llama-server with New Model
  ↓
Health Check
  ↓
Process Queued Requests / Reject Old Requests
  ↓
Return Success/Failure
\\\

## Security Architecture

### Authentication Layers

1. **Web UI Authentication**
   - Session-based authentication
   - HTTP-only cookies
   - CSRF protection
   - Password hashing with bcrypt (cost factor 12)

2. **API Token Authentication**
   - Bearer token in Authorization header
   - Tokens stored as hashes in database
   - Optional expiration
   - Rate limiting per token

### Security Best Practices

- Passwords hashed with bcrypt (never stored plain)
- API tokens cryptographically random (secrets.token_urlsafe)
- HTTPS enforcement option
- Configurable CORS policies
- Input validation on all endpoints
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (template escaping)
- Rate limiting on authentication endpoints

## Deployment Architecture

### Single-Server Deployment (Initial Version)
\\\
┌─────────────────────────────────────────┐
│         Server Machine                  │
│                                         │
│  ┌────────────────────────────────┐   │
│  │  LlamaController Service       │   │
│  │  (Python app on port 3000)     │   │
│  └────────────────────────────────┘   │
│              ↓                          │
│  ┌────────────────────────────────┐   │
│  │  llama-server subprocess       │   │
│  │  (port 8080 - localhost only)  │   │
│  └────────────────────────────────┘   │
│                                         │
│  ┌────────────────────────────────┐   │
│  │  SQLite Database               │   │
│  └────────────────────────────────┘   │
│                                         │
│  ┌────────────────────────────────┐   │
│  │  Config Files (YAML)           │   │
│  └────────────────────────────────┘   │
└─────────────────────────────────────────┘
\\\

### Reverse Proxy Setup (Production)
\\\
Internet → Nginx/Caddy (HTTPS, port 443)
              ↓
          LlamaController (port 3000)
              ↓
          llama-server (port 8080, localhost)
\\\

## Configuration File Locations

\\\
llamacontroller/
├── config/
│   ├── llamacpp-config.yaml    # llama.cpp settings
│   ├── models-config.yaml      # Model definitions
│   └── auth-config.yaml        # Auth settings
├── data/
│   ├── llamacontroller.db      # SQLite database
│   └── sessions/               # Session files (optional)
└── logs/
    ├── app.log                 # Application logs
    └── llamacpp.log            # llama.cpp output
\\\

## Error Handling Strategy

### Error Categories

1. **Configuration Errors**: Fail fast at startup
2. **Model Loading Errors**: Return error, keep controller running
3. **llama.cpp Crashes**: Auto-restart with backoff
4. **Request Errors**: Return appropriate HTTP status codes
5. **Authentication Errors**: Log and rate limit

### Logging Levels

- **DEBUG**: Detailed request/response logs
- **INFO**: Model operations, API calls
- **WARNING**: Retry attempts, deprecated usage
- **ERROR**: Failed operations, caught exceptions
- **CRITICAL**: System failures, security issues

## Performance Considerations

### Async Operations

- Use async/await for I/O operations
- Non-blocking request proxying to llama.cpp
- Async logging to avoid blocking requests

### Resource Management

- Connection pooling for database
- Request timeout configuration
- Memory limits for log buffering
- Graceful shutdown handling

### Scalability Limits (v1.0)

- **Concurrent Users**: Limited by llama.cpp (typically 1-10 concurrent)
- **Models**: One active model at a time
- **Requests/sec**: Limited by model inference speed
- **Storage**: SQLite suitable for < 100K tokens/sessions

## Future Architecture Enhancements

### Potential Future Features

1. **Multiple llama.cpp Instances**: Load multiple models simultaneously
2. **Model Pools**: Pre-warm multiple models for fast switching
3. **Distributed Setup**: Multiple LlamaController nodes
4. **Redis Session Store**: For multi-instance deployments
5. **PostgreSQL**: For larger deployments
6. **Prometheus Metrics**: Advanced monitoring
7. **GraphQL API**: Alternative to REST
8. **WebSocket Support**: Real-time updates

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-11  
**Status**: Design Phase
