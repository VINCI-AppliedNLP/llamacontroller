#!/usr/bin/env python3
"""
Test script for GPU memory display feature.

This script tests the GPU memory tracking and display functionality
by loading a model and verifying memory information is captured and displayed.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.core.lifecycle import LifecycleManager
from llamacontroller.core.config import Config
from llamacontroller.core.gpu_detector import GpuDetector


async def test_gpu_memory_display():
    """Test GPU memory display after loading a model."""
    print("=== GPU Memory Display Test ===\n")
    
    # Initialize components
    config = Config()
    gpu_detector = GpuDetector()
    manager = LifecycleManager(config, gpu_detector)
    
    # Check GPU availability
    print("1. Checking GPU availability...")
    gpu_statuses = gpu_detector.detect_gpus()
    gpu_count = len([g for g in gpu_statuses if g.index >= 0])
    print(f"   GPU Count: {gpu_count}")
    
    if gpu_count == 0:
        print("   ⚠️  No GPUs detected. Test requires at least one GPU.")
        return False
    
    # Display initial GPU status
    print("\n2. Initial GPU Status:")
    for gpu in gpu_statuses:
        if gpu.index >= 0:  # Skip CPU fallback
            print(f"   GPU {gpu.index}")
            print(f"      Memory: {gpu.memory_used}MiB / {gpu.memory_total}MiB")
            print(f"      State: {gpu.state}")
    
    # Find an idle GPU for testing
    idle_gpus = [gpu for gpu in gpu_statuses if gpu.index >= 0 and gpu.state == "idle"]
    if not idle_gpus:
        print("\n   ⚠️  No idle GPUs available for testing.")
        return False
    
    test_gpu = idle_gpus[0]
    print(f"\n3. Using GPU {test_gpu.index} for testing")
    
    # Load a model (use a small model for quick testing)
    model_name = "llama3.2:1b"  # Small model for quick testing
    print(f"\n4. Loading model '{model_name}' on GPU {test_gpu.index}...")
    
    try:
        result = await manager.load_model(
            model_name=model_name,
            gpu_ids=[test_gpu.index]
        )
        
        if not result.success:
            print(f"   ❌ Failed to load model: {result.error}")
            return False
        
        print(f"   ✅ Model loaded successfully on port {result.port}")
        
    except Exception as e:
        print(f"   ❌ Exception during model loading: {e}")
        return False
    
    # Get GPU status after loading
    print("\n5. Checking GPU status after model load...")
    status = manager.get_gpu_status(str(test_gpu.index))
    
    if not status:
        print("   ❌ Failed to get GPU status")
        return False
    
    print(f"   Model: {status.model_name}")
    print(f"   Port: {status.port}")
    print(f"   Status: {status.status}")
    
    # Verify memory information
    print("\n6. Verifying memory information...")
    if status.memory_used_mb is None or status.memory_total_mb is None:
        print("   ❌ Memory information not captured")
        success = False
    elif status.memory_total_mb == 0:
        print("   ❌ Invalid memory total (0 MiB)")
        success = False
    else:
        memory_percent = (status.memory_used_mb / status.memory_total_mb) * 100
        print(f"   ✅ Memory Used: {status.memory_used_mb}MiB")
        print(f"   ✅ Memory Total: {status.memory_total_mb}MiB")
        print(f"   ✅ Memory Usage: {memory_percent:.1f}%")
        success = True
    
    # Unload the model
    print("\n7. Unloading model...")
    try:
        unload_result = await manager.unload_model(str(test_gpu.index))
        if unload_result.success:
            print("   ✅ Model unloaded successfully")
        else:
            print(f"   ⚠️  Unload warning: {unload_result.message}")
    except Exception as e:
        print(f"   ⚠️  Exception during unload: {e}")
    
    return success


async def test_multi_gpu_memory():
    """Test multi-GPU memory aggregation."""
    print("\n\n=== Multi-GPU Memory Aggregation Test ===\n")
    
    # Initialize components
    config = Config()
    gpu_detector = GpuDetector()
    manager = LifecycleManager(config, gpu_detector)
    
    # Check GPU availability
    gpu_statuses = gpu_detector.detect_gpus()
    gpu_count = len([g for g in gpu_statuses if g.index >= 0])
    
    if gpu_count < 2:
        print("   ⚠️  Test requires at least 2 GPUs. Skipping multi-GPU test.")
        return True  # Not a failure, just skipped
    
    # Find idle GPUs
    idle_gpus = [gpu for gpu in gpu_statuses if gpu.index >= 0 and gpu.state == "idle"]
    if len(idle_gpus) < 2:
        print("   ⚠️  Need at least 2 idle GPUs for multi-GPU test. Skipping.")
        return True  # Not a failure, just skipped
    
    gpu_ids = [idle_gpus[0].index, idle_gpus[1].index]
    print(f"Using GPUs: {gpu_ids}")
    
    # Load model on multiple GPUs
    model_name = "llama3.2:1b"
    print(f"\nLoading model '{model_name}' on GPUs {gpu_ids}...")
    
    try:
        result = await manager.load_model(
            model_name=model_name,
            gpu_ids=gpu_ids
        )
        
        if not result.success:
            print(f"   ❌ Failed to load model: {result.error}")
            return False
        
        print(f"   ✅ Model loaded successfully on port {result.port}")
        
    except Exception as e:
        print(f"   ❌ Exception during model loading: {e}")
        return False
    
    # Get status for multi-GPU instance
    gpu_key = ",".join(map(str, gpu_ids))
    print(f"\nChecking status for GPU combination: {gpu_key}")
    status = manager.get_gpu_status(gpu_key)
    
    if not status:
        print("   ❌ Failed to get GPU status")
        return False
    
    # Verify memory information (should be sum of both GPUs)
    if status.memory_used_mb is None or status.memory_total_mb is None:
        print("   ❌ Memory information not captured")
        success = False
    else:
        memory_percent = (status.memory_used_mb / status.memory_total_mb) * 100
        print(f"   ✅ Total Memory Used: {status.memory_used_mb}MiB")
        print(f"   ✅ Total Memory: {status.memory_total_mb}MiB")
        print(f"   ✅ Memory Usage: {memory_percent:.1f}%")
        print(f"   (This is the sum across {len(gpu_ids)} GPUs)")
        success = True
    
    # Unload the model
    print("\nUnloading model...")
    try:
        unload_result = await manager.unload_model(gpu_key)
        if unload_result.success:
            print("   ✅ Model unloaded successfully")
        else:
            print(f"   ⚠️  Unload warning: {unload_result.message}")
    except Exception as e:
        print(f"   ⚠️  Exception during unload: {e}")
    
    return success


async def main():
    """Run all tests."""
    print("Starting GPU Memory Display Tests\n")
    print("=" * 50)
    
    # Test 1: Single GPU memory display
    test1_passed = await test_gpu_memory_display()
    
    # Test 2: Multi-GPU memory aggregation
    test2_passed = await test_multi_gpu_memory()
    
    # Summary
    print("\n" + "=" * 50)
    print("\n=== Test Summary ===")
    print(f"Single GPU Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Multi-GPU Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    overall_success = test1_passed and test2_passed
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
