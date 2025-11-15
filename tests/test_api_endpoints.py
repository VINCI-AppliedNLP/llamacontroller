"""
API endpoints integration tests.

Tests for management and Ollama-compatible API endpoints.
Requires the server to be running on localhost:3000.
"""

import pytest
import requests

# Test configuration
BASE_URL = "http://localhost:3000"
TIMEOUT = 5

class TestAPIEndpoints:
    """Test essential API endpoints."""
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        assert response.status_code == 200
    
    def test_list_models(self):
        """Test listing available models."""
        response = requests.get(f"{BASE_URL}/api/v1/models", timeout=TIMEOUT)
        assert response.status_code == 200
        assert isinstance(response.json(), (list, dict))
    
    def test_model_status(self):
        """Test getting current model status."""
        response = requests.get(f"{BASE_URL}/api/v1/models/status", timeout=TIMEOUT)
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    def test_ollama_tags(self):
        """Test Ollama-compatible tags endpoint."""
        response = requests.get(f"{BASE_URL}/api/tags", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is valid."""
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert len(data["paths"]) > 0

# Pytest markers for integration tests
pytestmark = pytest.mark.integration

# Skip all tests if server is not running
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires running server)"
    )

@pytest.fixture(scope="session", autouse=True)
def check_server_running():
    """Check if server is running before running tests."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            pytest.skip(f"Server not responding correctly at {BASE_URL}")
    except requests.exceptions.ConnectionError:
        pytest.skip(f"Server not running at {BASE_URL}")
    except requests.exceptions.Timeout:
        pytest.skip(f"Server timeout at {BASE_URL}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
