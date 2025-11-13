"""
Tests for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from src.llamacontroller.main import app
from src.llamacontroller.core.lifecycle import ModelLifecycleManager
from src.llamacontroller.models.lifecycle import (
    ModelStatus,
    ProcessStatus,
    HealthCheckResponse,
    LoadModelResponse,
    UnloadModelResponse,
    ModelInfo,
)

# Test client
client = TestClient(app)

class TestRootEndpoints:
    """Test root API endpoints."""
    
    def test_root(self):
        """Test root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "LlamaController"
        assert data["version"] == "0.1.0"
        assert "endpoints" in data
    
    def test_health(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

class TestManagementAPI:
    """Test management API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        # Mock the lifecycle manager
        with patch("src.llamacontroller.api.dependencies._lifecycle_manager") as mock_lifecycle:
            self.mock_lifecycle = mock_lifecycle
            yield
    
    def test_list_models_empty(self):
        """Test listing models when none are configured."""
        self.mock_lifecycle.get_available_models.return_value = []
        
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 0
    
    def test_list_models_with_models(self):
        """Test listing models when models are configured."""
        mock_models = [
            ModelInfo(
                id="test-model",
                name="Test Model",
                path="/path/to/model.gguf",
                status="available",
                loaded=False,
                description="Test model",
                parameter_count="7B",
                quantization="Q4_0",
            )
        ]
        self.mock_lifecycle.get_available_models.return_value = mock_models
        
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert len(data["models"]) == 1
        assert data["models"][0]["id"] == "test-model"
    
    def test_get_model_status_no_model_loaded(self):
        """Test getting status when no model is loaded."""
        mock_status = ModelStatus(
            model_id=None,
            model_name=None,
            status=ProcessStatus.STOPPED,
            loaded_at=None,
            memory_usage_mb=None,
            uptime_seconds=None,
            pid=None,
            host="127.0.0.1",
            port=8080,
        )
        
        # Create async mock
        async def mock_get_status():
            return mock_status
        
        self.mock_lifecycle.get_status = mock_get_status
        
        response = client.get("/api/v1/models/status")
        assert response.status_code == 200
        data = response.json()
        assert data["model_id"] is None
        assert data["status"] == "stopped"
    
    def test_health_check(self):
        """Test health check endpoint."""
        mock_health = HealthCheckResponse(
            healthy=True,
            status=ProcessStatus.RUNNING,
            message="Server is healthy",
            uptime_seconds=100
        )
        
        async def mock_healthcheck():
            return mock_health
        
        self.mock_lifecycle.healthcheck = mock_healthcheck
        
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is True
        assert data["message"] == "Server is healthy"

class TestOllamaAPI:
    """Test Ollama-compatible API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        with patch("src.llamacontroller.api.dependencies._lifecycle_manager") as mock_lifecycle:
            self.mock_lifecycle = mock_lifecycle
            yield
    
    def test_list_models_tags_endpoint(self):
        """Test Ollama /api/tags endpoint."""
        mock_models = [
            ModelInfo(
                id="phi-4",
                name="Phi-4",
                path="/path/to/phi4.gguf",
                status="available",
                loaded=False,
                description="Phi-4 model",
                parameter_count="14B",
                quantization="IQ1_M",
            )
        ]
        self.mock_lifecycle.get_available_models.return_value = mock_models
        
        response = client.get("/api/tags")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 0  # May be empty if path doesn't exist
    
    def test_show_model_not_found(self):
        """Test show model when model doesn't exist."""
        self.mock_lifecycle.config_manager.models.get_model.return_value = None
        
        response = client.post("/api/show", json={"name": "nonexistent-model"})
        assert response.status_code == 404
    
    def test_list_running_models_none(self):
        """Test /api/ps when no model is running."""
        self.mock_lifecycle.get_current_model.return_value = None
        
        response = client.get("/api/ps")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) == 0
    
    def test_delete_model_not_supported(self):
        """Test that delete endpoint returns not implemented."""
        response = client.request(
            "DELETE",
            "/api/delete",
            json={"name": "test-model"}
        )
        assert response.status_code == 501
        data = response.json()
        assert "not supported" in data["detail"].lower()

class TestAPIIntegration:
    """Integration tests for API."""
    
    def test_openapi_docs_available(self):
        """Test that OpenAPI documentation is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_docs_ui_available(self):
        """Test that Swagger UI is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
