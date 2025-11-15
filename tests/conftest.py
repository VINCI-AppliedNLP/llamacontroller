"""
Pytest configuration and fixtures.
"""

import sys
from pathlib import Path
import pytest

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    # Prevent SQLAlchemy table redefinition issues
    import warnings
    warnings.filterwarnings("ignore", message=".*already defined.*")
    
    yield
    
    # Cleanup after tests
    pass
