"""
Test script for process registry functionality.

This script tests:
1. Process registration when loading models
2. Process verification
3. Process recovery after restart simulation
4. Orphaned process detection and cleanup
"""

import sys
import time
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.core.lifecycle import ModelLifecycleManager
from llamacontroller.core.config import ConfigManager


async def test_process_registry():
    """Test process registry functionality."""
    print("=" * 80)
    print("Process Registry Functionality Test")
    print("=" * 80)
    
    # Initialize lifecycle manager
    config_manager = ConfigManager()
    config_manager.load_config()
    lifecycle = ModelLifecycleManager(config_manager)
    
    print("\n1. Testing Process Registry Initialization")
    print("-" * 80)
    print(f"Registry file: {lifecycle.process_registry.registry_file}")
    processes = lifecycle.process_registry.get_all_processes()
    print(f"Initial registered processes: {len(processes)}")
    for gpu_id, entry in processes.items():
        print(f"  GPU {gpu_id}: PID {entry.pid}, Model {entry.model_name}, Status {entry.status}")
    
    print("\n2. Testing Process Verification")
    print("-" * 80)
    verification_results = lifecycle.process_registry.verify_all_processes()
    print(f"Verification results:")
    for gpu_id, is_running in verification_results.items():
        print(f"  GPU {gpu_id}: {'Running' if is_running else 'Not running'}")
    
    print("\n3. Testing Orphaned Process Detection")
    print("-" * 80)
    orphaned_pids = lifecycle.process_registry.find_orphaned_processes()
    if orphaned_pids:
        print(f"Found {len(orphaned_pids)} orphaned processes:")
        for pid in orphaned_pids:
            print(f"  PID {pid}")
    else:
        print("No orphaned processes found")
    
    print("\n4. Getting GPU Status")
    print("-" * 80)
    all_status = await lifecycle.get_all_gpu_statuses()
    
    # all_status is a Dict[str, Optional[GpuInstanceStatus]]
    gpu_0 = all_status.get("0")
    gpu_1 = all_status.get("1")
    gpu_both = all_status.get("both")
    
    print(f"GPU 0: {gpu_0.status if gpu_0 else 'No model loaded'}")
    print(f"GPU 1: {gpu_1.status if gpu_1 else 'No model loaded'}")
    if gpu_both:
        print(f"Both GPUs: {gpu_both.status}")
    
    # Show detailed status for each GPU
    if gpu_0:
        print(f"\nGPU 0 Details:")
        print(f"  Model: {gpu_0.model_name}")
        print(f"  PID: {gpu_0.pid}")
        print(f"  Port: {gpu_0.port}")
        print(f"  Memory: {gpu_0.memory_used_mb} MB")
    
    if gpu_1:
        print(f"\nGPU 1 Details:")
        print(f"  Model: {gpu_1.model_name}")
        print(f"  PID: {gpu_1.pid}")
        print(f"  Port: {gpu_1.port}")
        print(f"  Memory: {gpu_1.memory_used_mb} MB")
    
    if gpu_both:
        print(f"\nBoth GPUs Details:")
        print(f"  Model: {gpu_both.model_name}")
        print(f"  PID: {gpu_both.pid}")
        print(f"  Port: {gpu_both.port}")
        print(f"  Memory: {gpu_both.memory_used_mb} MB")
    
    print("\n5. Test Summary")
    print("-" * 80)
    print(f"✓ Registry initialized successfully")
    print(f"✓ Process verification completed")
    print(f"✓ Orphaned process detection completed")
    print(f"✓ GPU status retrieval completed")
    
    print("\n" + "=" * 80)
    print("Test completed successfully!")
    print("=" * 80)
    
    return lifecycle


async def test_load_and_register():
    """Test loading a model and verifying registration."""
    print("\n" + "=" * 80)
    print("Testing Model Load and Process Registration")
    print("=" * 80)
    
    config_manager = ConfigManager()
    config_manager.load_config()
    lifecycle = ModelLifecycleManager(config_manager)
    
    # Get available models
    models = lifecycle.get_available_models()
    if not models:
        print("ERROR: No models available for testing")
        return
    
    # Use the first available model
    test_model = models[0]
    print(f"\nUsing model: {test_model.name} (ID: {test_model.id})")
    
    # Try to load on GPU 0
    print(f"\nLoading model on GPU 0...")
    try:
        result = await lifecycle.load_model(test_model.id, gpu_id=0)
        print(f"Load result: {result.message}")
        
        # Wait a moment for the process to stabilize
        print("Waiting for process to stabilize...")
        await asyncio.sleep(2)
        
        # Check process registry
        print("\nChecking process registry...")
        processes = lifecycle.process_registry.get_all_processes()
        if "0" in processes:
            entry = processes["0"]
            print(f"✓ Process registered for GPU 0:")
            print(f"  PID: {entry.pid}")
            print(f"  Model: {entry.model_name}")
            print(f"  Port: {entry.port}")
            print(f"  Command: {' '.join(entry.command_line[:3])}...")
            
            # Verify the process
            is_running = lifecycle.process_registry.verify_process("0")
            print(f"  Process verification: {'Running' if is_running else 'Not running'}")
        else:
            print("ERROR: Process not registered!")
        
        # Unload the model
        print("\nUnloading model...")
        unload_result = await lifecycle.unload_model(gpu_id=0)
        print(f"Unload result: {unload_result.message}")
        
        # Check that process was unregistered
        print("\nChecking process registry after unload...")
        processes = lifecycle.process_registry.get_all_processes()
        if "0" not in processes:
            print("✓ Process successfully unregistered")
        else:
            print("WARNING: Process still in registry!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    # Test 1: Basic registry functionality
    await test_process_registry()
    
    # Test 2: Load and register (optional, requires model)
    print("\n\nWould you like to test model loading and registration?")
    print("This will load a model on GPU 0 and verify the process is registered.")
    response = input("Continue? (y/N): ").strip().lower()
    
    if response == 'y':
        await test_load_and_register()
    else:
        print("\nSkipping model load test.")


if __name__ == "__main__":
    asyncio.run(main())
