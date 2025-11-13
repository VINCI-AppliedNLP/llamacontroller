"""
LlamaController FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import management, ollama, auth, tokens, users
from .web import routes as web_routes
from .api.dependencies import initialize_managers
from .utils.logging import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting LlamaController...")
    
    try:
        # Initialize managers
        initialize_managers(config_dir="./config")
        logger.info("Managers initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize managers: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down LlamaController...")

# Create FastAPI application
app = FastAPI(
    title="LlamaController",
    description="WebUI-based management system for llama.cpp model lifecycle with Ollama API compatibility",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# Web UI routes (must be first for / to work)
app.include_router(web_routes.router)

# API routes
app.include_router(auth.router)
app.include_router(tokens.router)
app.include_router(users.router)
app.include_router(management.router)
app.include_router(ollama.router)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    from .api.dependencies import get_lifecycle_manager
    
    # Get current server status
    lifecycle = get_lifecycle_manager()
    status = await lifecycle.get_status()
    
    response = {
        "name": "LlamaController",
        "version": "0.1.0",
        "description": "llama.cpp model lifecycle management with Ollama API compatibility",
        "endpoints": {
            "management": "/api/v1",
            "ollama_compatible": "/api",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }
    
    # Add llama-server URL if running
    if status.status == "running" and status.host and status.port:
        response["llama_server"] = {
            "status": "running",
            "url": f"http://{status.host}:{status.port}",
            "web_interface": f"http://{status.host}:{status.port}",
            "model": status.model_name or status.model_id
        }
    else:
        response["llama_server"] = {
            "status": "stopped",
            "message": "Load a model to start llama-server"
        }
    
    return response

@app.get("/health")
async def health():
    """Basic health check endpoint."""
    return {"status": "ok"}

# Exception handler for uncaught exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions globally."""
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "llamacontroller.main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
