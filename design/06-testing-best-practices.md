# Testing Best Practices for LlamaController

## Overview

This document outlines testing best practices and guidelines for the LlamaController project, based on lessons learned during development.

## Core Principle: Write Real Tests, Not Just Output Scripts

**❌ Bad Practice: Print-Only "Tests"**

Scripts that only print information without assertions are NOT real tests:

```python
# BAD: This is just a demo script, not a test
def main():
    print("Testing configuration...")
    config = load_config()
    print(f"Loaded {len(config.models)} models")  # No verification!
    print("Test complete!")  # Always "passes"
```

**✅ Good Practice: Assertion-Based Tests**

Real tests use assertions to verify behavior:

```python
# GOOD: Real test with assertions
def test_load_models_config():
    config_manager = ConfigManager(config_dir="./config")
    models_config = config_manager.load_models_config()
    
    # Actual verification
    assert isinstance(models_config, ModelsConfig)
    assert len(models_config.models) == 2
    assert models_config.get_model("phi-4-reasoning") is not None
```

## Testing Framework: pytest

### Why pytest?

- Simple, Pythonic syntax
- Excellent test discovery
- Rich assertion introspection
- Extensive plugin ecosystem
- Built-in fixtures and parameterization

### Project Structure

```
llamacontroller/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest configuration and fixtures
│   ├── test_config.py           # Configuration tests
│   ├── test_lifecycle.py        # Model lifecycle tests
│   ├── test_adapter.py          # Process adapter tests
│   └── integration/
│       └── test_end_to_end.py   # Integration tests
```

## Test Categories

### 1. Unit Tests

Test individual components in isolation.

**Example:**
```python
def test_config_manager_validates_paths():
    """Test that ConfigManager validates file paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config with invalid path
        config_file = Path(tmpdir) / "config.yaml"
        config_file.write_text("""
        llama_cpp:
          executable_path: "/nonexistent/llama-server"
        """)
        
        config_manager = ConfigManager(config_dir=tmpdir)
        with pytest.raises(ConfigError, match="not found"):
            config_manager.load_llama_cpp_config()
```

### 2. Integration Tests

Test how components work together.

**Example:**
```python
@pytest.mark.asyncio
async def test_model_lifecycle_integration():
    """Test complete model load/unload cycle."""
    config_manager = ConfigManager()
    lifecycle_manager = ModelLifecycleManager(config_manager)
    
    # Load model
    result = await lifecycle_manager.load_model("phi-4-reasoning")
    assert result.success is True
    
    # Verify it's running
    assert await lifecycle_manager.healthcheck() is True
    
    # Unload model
    await lifecycle_manager.unload_model()
    assert lifecycle_manager.current_model is None
```

### 3. End-to-End Tests

Test complete workflows through the API.

**Example:**
```python
async def test_api_model_switch(test_client):
    """Test switching models via API."""
    # Load first model
    response = await test_client.post("/api/v1/models/load", 
                                      json={"model_id": "phi-4-reasoning"})
    assert response.status_code == 200
    
    # Switch to second model
    response = await test_client.post("/api/v1/models/switch",
                                      json={"model_id": "qwen3-coder-30b"})
    assert response.status_code == 200
    assert response.json()["current_model"] == "qwen3-coder-30b"
```

## Test Organization Best Practices

### 1. Use Test Classes for Grouping

```python
class TestConfigManager:
    """All ConfigManager tests."""
    
    def test_init_with_valid_directory(self):
        pass
    
    def test_init_with_invalid_directory(self):
        pass
    
    def test_load_config(self):
        pass

class TestModelsConfig:
    """All ModelsConfig tests."""
    
    def test_get_model_by_id(self):
        pass
```

### 2. Clear Test Names

Test names should describe what they're testing:

```python
# ✅ GOOD: Clear what's being tested
def test_load_config_raises_error_when_file_missing():
    pass

def test_model_parameters_validated_correctly():
    pass

# ❌ BAD: Unclear names
def test_config():
    pass

def test_stuff():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_get_model_by_id():
    # Arrange: Set up test data
    config_manager = ConfigManager(config_dir="./config")
    models_config = config_manager.load_models_config()
    
    # Act: Perform the operation
    model = models_config.get_model("phi-4-reasoning")
    
    # Assert: Verify the result
    assert model is not None
    assert model.id == "phi-4-reasoning"
    assert model.name == "Phi-4 Reasoning Plus"
```

## Fixtures and Reusability

### Use conftest.py for Shared Fixtures

```python
# tests/conftest.py
import pytest
from llamacontroller.core.config import ConfigManager

@pytest.fixture
def config_manager():
    """Provide a configured ConfigManager instance."""
    manager = ConfigManager(config_dir="./config")
    manager.load_config()
    return manager

@pytest.fixture
def temp_config_dir(tmp_path):
    """Provide a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir
```

### Use Fixtures in Tests

```python
def test_something(config_manager):
    """Test using the config_manager fixture."""
    assert config_manager.llama_cpp is not None
```

## Testing Async Code

Use `pytest-asyncio` for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation():
    """Test an async function."""
    result = await some_async_function()
    assert result is not None
```

## Mocking External Dependencies

Use `pytest-mock` or `unittest.mock` to mock external dependencies:

```python
def test_adapter_starts_process(mocker):
    """Test that adapter starts subprocess correctly."""
    mock_popen = mocker.patch("subprocess.Popen")
    
    adapter = LlamaCppAdapter(config)
    adapter.start_server(model_path="/path/to/model.gguf")
    
    # Verify subprocess was called correctly
    mock_popen.assert_called_once()
    call_args = mock_popen.call_args[0][0]
    assert "llama-server" in call_args[0]
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_config.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pytest --cov=src/llamacontroller --cov-report=html
```

### Run Only Failed Tests

```bash
pytest --lf
```

## Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Cover all major workflows
- **End-to-End Tests**: Cover critical user paths

## Continuous Integration

Tests should run automatically on:
- Every commit
- Every pull request
- Before deployment

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -v --cov=src/llamacontroller
```

## Common Pitfalls to Avoid

### 1. Testing Implementation Details

```python
# ❌ BAD: Testing internal implementation
def test_config_manager_has_private_variable():
    config_manager = ConfigManager()
    assert hasattr(config_manager, '_config')

# ✅ GOOD: Testing public interface
def test_config_manager_loads_config():
    config_manager = ConfigManager()
    config = config_manager.load_config()
    assert config is not None
```

### 2. Tests That Depend on External State

```python
# ❌ BAD: Depends on specific files existing
def test_load_model():
    # Assumes model file exists at specific location
    model = load_model("/home/user/models/model.gguf")

# ✅ GOOD: Creates own test data
def test_load_model(tmp_path):
    # Create test model file
    model_file = tmp_path / "test.gguf"
    model_file.write_bytes(b"mock model data")
    model = load_model(str(model_file))
```

### 3. Tests That Modify Global State

```python
# ❌ BAD: Modifies global configuration
def test_something():
    set_global_config({"key": "value"})
    # Test runs...
    # Other tests may be affected!

# ✅ GOOD: Uses fixtures that cleanup
@pytest.fixture
def isolated_config():
    old_config = get_global_config()
    set_global_config({"key": "test_value"})
    yield
    set_global_config(old_config)
```

## Summary

- ✅ Write real tests with assertions, not print statements
- ✅ Use pytest for testing
- ✅ Organize tests logically by component
- ✅ Use clear, descriptive test names
- ✅ Follow Arrange-Act-Assert pattern
- ✅ Use fixtures for reusable setup
- ✅ Aim for high test coverage
- ✅ Run tests automatically in CI/CD
- ❌ Avoid testing implementation details
- ❌ Avoid tests that depend on external state
- ❌ Avoid tests that modify global state

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-12  
**Status**: Active Guidelines

**Note**: These practices were established after realizing that initial "test scripts" were merely printing output without actual verification. Always write real tests with assertions!
