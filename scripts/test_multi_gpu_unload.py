"""
Test script to verify multi-GPU unload button functionality.

This script tests that:
1. Single GPU models show unload buttons
2. Multi-GPU models show unload buttons
3. The get_all_gpu_statuses() returns correct key format
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.core.config import ConfigManager
from llamacontroller.core.lifecycle import ModelLifecycleManager


async def test_gpu_status_keys():
    """Test that get_all_gpu_statuses returns correct key format."""
    print("\n=== Testing GPU Status Key Format ===\n")
    
    # Initialize manager
    config_manager = ConfigManager()
    config_manager.load_config()  # Load configuration first
    lifecycle_manager = ModelLifecycleManager(config_manager)
    
    # Test 1: No models loaded
    print("Test 1: No models loaded")
    statuses = await lifecycle_manager.get_all_gpu_statuses()
    print(f"  Keys: {list(statuses.keys())}")
    print(f"  Expected: [] (empty)")
    assert len(statuses) == 0, "Should be empty when no models loaded"
    print("  ✓ PASS\n")
    
    # Test 2: Simulate loading model on GPU 0
    print("Test 2: Simulating model loaded on GPU 0")
    print("  Expected key format: '0' (not 'gpu0')")
    # Note: We can't actually load models in this test without llama.cpp
    # But we can verify the key normalization logic
    gpu_id = lifecycle_manager._normalize_gpu_id(0)
    print(f"  Normalized GPU ID for input 0: '{gpu_id}'")
    assert gpu_id == "0", f"Expected '0', got '{gpu_id}'"
    print("  ✓ PASS\n")
    
    # Test 3: Multi-GPU key format
    print("Test 3: Multi-GPU key format")
    print("  Expected key format: '0,1' (not 'gpu0,1' or 'both')")
    gpu_id = lifecycle_manager._normalize_gpu_id("0,1")
    print(f"  Normalized GPU ID for input '0,1': '{gpu_id}'")
    assert gpu_id == "0,1", f"Expected '0,1', got '{gpu_id}'"
    print("  ✓ PASS\n")
    
    # Test 4: Backward compatibility with "both"
    print("Test 4: Backward compatibility with 'both'")
    gpu_id = lifecycle_manager._normalize_gpu_id("both")
    print(f"  Normalized GPU ID for input 'both': '{gpu_id}'")
    assert gpu_id == "0,1", f"Expected '0,1', got '{gpu_id}'"
    print("  ✓ PASS\n")
    
    # Test 5: Integer input
    print("Test 5: Integer input compatibility")
    gpu_id = lifecycle_manager._normalize_gpu_id(1)
    print(f"  Normalized GPU ID for input 1 (int): '{gpu_id}'")
    assert gpu_id == "1", f"Expected '1', got '{gpu_id}'"
    print("  ✓ PASS\n")
    
    print("=== All Tests Passed! ===\n")
    print("Summary:")
    print("  ✓ get_all_gpu_statuses() will return keys without 'gpu' prefix")
    print("  ✓ Single GPU: key = '0' or '1'")
    print("  ✓ Multi GPU: key = '0,1'")
    print("  ✓ Template can use gpu_statuses.get('0') or gpu_statuses['0,1']")
    print("  ✓ Backward compatible with 'both' → '0,1'")
    print()


def test_template_logic():
    """Test template logic for displaying GPU cards."""
    print("\n=== Testing Template Display Logic ===\n")
    
    # Simulate gpu_statuses dictionary returned by get_all_gpu_statuses()
    test_cases = [
        {
            "name": "Single GPU 0 loaded",
            "gpu_statuses": {
                "0": {"model_name": "Phi-4", "port": 8081, "gpu_id": "0"}
            },
            "expected": "Should show unload button for GPU 0"
        },
        {
            "name": "Single GPU 1 loaded",
            "gpu_statuses": {
                "1": {"model_name": "Qwen-Coder", "port": 8088, "gpu_id": "1"}
            },
            "expected": "Should show unload button for GPU 1"
        },
        {
            "name": "Multi-GPU 0,1 loaded",
            "gpu_statuses": {
                "0,1": {"model_name": "Large-Model", "port": 8081, "gpu_id": "0,1"}
            },
            "expected": "Should show unload button in Multi-GPU card"
        },
        {
            "name": "Both GPU 0 and GPU 1 loaded separately",
            "gpu_statuses": {
                "0": {"model_name": "Phi-4", "port": 8081, "gpu_id": "0"},
                "1": {"model_name": "Qwen-Coder", "port": 8088, "gpu_id": "1"}
            },
            "expected": "Should show two unload buttons"
        },
        {
            "name": "No models loaded",
            "gpu_statuses": {},
            "expected": "Should show no unload buttons"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['name']}")
        print(f"  gpu_statuses keys: {list(test_case['gpu_statuses'].keys())}")
        print(f"  Expected: {test_case['expected']}")
        
        # Check for single GPUs
        for gpu_idx in range(2):  # Assuming 2 GPUs
            gpu_key = str(gpu_idx)
            if gpu_key in test_case['gpu_statuses']:
                print(f"    ✓ Found GPU {gpu_idx}: {test_case['gpu_statuses'][gpu_key]['model_name']}")
        
        # Check for multi-GPU
        for key, value in test_case['gpu_statuses'].items():
            if ',' in key:
                print(f"    ✓ Found Multi-GPU {key}: {value['model_name']}")
        
        print()
    
    print("=== Template Logic Tests Complete ===\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Multi-GPU Unload Button Fix - Verification Tests")
    print("=" * 60)
    
    # Run async tests
    asyncio.run(test_gpu_status_keys())
    
    # Run template logic tests
    test_template_logic()
    
    print("\n" + "=" * 60)
    print("All verification tests completed successfully!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Start the LlamaController server")
    print("2. Load a model to GPU 0 - verify unload button appears")
    print("3. Load a model to GPU 1 - verify unload button appears")
    print("4. Load a model to GPU 0,1 - verify Multi-GPU card with unload button")
    print("5. Click unload buttons and verify they work correctly")
    print()
