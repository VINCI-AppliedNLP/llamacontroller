"""
GPU detection tests.

Tests for GPU detection functionality including mock GPU support.
"""

import pytest
from pathlib import Path

from llamacontroller.core.config import ConfigManager
from llamacontroller.core.gpu_detector import GpuDetector
from llamacontroller.models.gpu import GpuState

class TestGpuDetector:
    """Test GpuDetector core functionality."""
    
    def test_detect_gpus_returns_valid_statuses(self):
        """Test GPU detection returns valid status list with required fields."""
        detector = GpuDetector(memory_threshold_mb=1024)
        gpu_statuses = detector.detect_gpus()
        
        # Should return list (may have GPUs or CPU fallback)
        assert isinstance(gpu_statuses, list)
        assert len(gpu_statuses) > 0
        
        # Verify all statuses have required fields
        for status in gpu_statuses:
            assert hasattr(status, 'index')
            assert hasattr(status, 'state')
            assert hasattr(status, 'memory_used')
            assert hasattr(status, 'memory_total')
            assert hasattr(status, 'select_enabled')
            assert isinstance(status.state, GpuState)
            assert status.memory_total >= 0
            assert status.memory_used >= 0
    
    def test_memory_threshold_affects_selection(self):
        """Test that memory threshold correctly determines GPU selectability."""
        detector = GpuDetector(memory_threshold_mb=1024)
        gpu_statuses = detector.detect_gpus()
        
        for status in gpu_statuses:
            if status.index >= 0:  # Real GPU
                free_memory = status.memory_total - status.memory_used
                if free_memory >= 1024:
                    assert status.select_enabled, \
                        f"GPU {status.index} with {free_memory}MB free should be selectable"

class TestMockGpuDetection:
    """Test mock GPU detection for CI."""
    
    def test_mock_files_exist(self):
        """Test that mock GPU detection files exist for CI."""
        mock_dir = Path(__file__).parent / "mock"
        mock_nvidia_smi = mock_dir / "nvidia-smi.bat"
        
        # Verify mock files exist for CI testing
        assert mock_dir.exists(), "Mock directory should exist"
        assert mock_nvidia_smi.exists(), "Mock nvidia-smi.bat should exist"
    
    def test_detection_with_config(self):
        """Test GPU detection works with configuration."""
        config_manager = ConfigManager()
        llama_config = config_manager.load_llama_cpp_config()
        
        detector = GpuDetector(
            memory_threshold_mb=llama_config.gpu_detection.memory_threshold_mb
        )
        
        gpu_statuses = detector.detect_gpus()
        
        # Should get some results (real GPUs or CPU fallback)
        assert len(gpu_statuses) > 0
        
        # All detected GPUs should have valid properties
        for gpu in gpu_statuses:
            assert gpu.memory_total > 0
            assert gpu.memory_used >= 0
            assert gpu.state in [GpuState.IDLE, GpuState.MODEL_LOADED, GpuState.OCCUPIED_BY_OTHERS]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
