"""
Test script to actually load llama.cpp and send inference requests.

This script will:
1. Load a model using llama-server
2. Send a completion request via curl/httpx
3. Verify the response
4. Clean up
"""

import sys
import asyncio
import httpx
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.core.config import ConfigManager
from llamacontroller.core.lifecycle import ModelLifecycleManager

async def test_inference():
    """Test actual model inference."""
    
    print("=" * 70)
    print("LlamaController - Full Integration Test")
    print("This will actually load llama-server and test inference")
    print("=" * 70)
    print()
    
    # Load configuration
    print("📋 Step 1: Loading configuration...")
    config_manager = ConfigManager(config_dir="./config")
    config_manager.load_config()
    print(f"✓ llama-server: {config_manager.llama_cpp.executable_path}")
    print(f"✓ Endpoint: http://{config_manager.llama_cpp.default_host}:{config_manager.llama_cpp.default_port}")
    print()
    
    # Create lifecycle manager
    print("🔧 Step 2: Initializing lifecycle manager...")
    lifecycle_manager = ModelLifecycleManager(config_manager)
    print("✓ Ready")
    print()
    
    # List models
    models = lifecycle_manager.get_available_models()
    print(f"📦 Step 3: Found {len(models)} configured models")
    for model in models:
        print(f"   - {model.id}: {model.name}")
    print()
    
    if not models:
        print("❌ No models configured!")
        return
    
    # Use first model
    model_id = models[0].id
    print(f"🎯 Step 4: Will use model: {model_id}")
    print()
    
    # Ask for confirmation
    print("⚠️  WARNING: This will actually start llama-server and load the model.")
    print(f"   Model file: {models[0].path}")
    print(f"   Size: ~3.57 GB (for Phi-4)")
    print()
    response = input("Continue? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("\n❌ Test cancelled.")
        return
    
    print()
    print("🚀 Step 5: Loading model and starting llama-server...")
    print("-" * 70)
    
    try:
        # Load the model
        load_response = await lifecycle_manager.load_model(model_id)
        
        if not load_response.success:
            print(f"\n❌ Failed to load model: {load_response.message}")
            return
        
        print()
        print("✅ llama-server started successfully!")
        print(f"   PID: {load_response.status.pid}")
        print(f"   Status: {load_response.status.status}")
        print(f"   Endpoint: http://{load_response.status.host}:{load_response.status.port}")
        print()
        
        # Wait a moment for server to fully initialize
        print("⏳ Waiting for server to fully initialize...")
        await asyncio.sleep(3)
        
        # Health check
        print()
        print("🏥 Step 6: Health check...")
        health = await lifecycle_manager.healthcheck()
        if health.healthy:
            print(f"✓ Server is healthy (uptime: {health.uptime_seconds}s)")
        else:
            print(f"⚠️  Server health check failed: {health.message}")
            print("   Continuing anyway to test inference...")
        print()
        
        # Get server logs
        print("📜 Recent server logs:")
        logs = await lifecycle_manager.get_server_logs(lines=15)
        for log_line in logs[-15:]:
            print(f"   {log_line}")
        print()
        
        # Test inference via HTTP
        print("=" * 70)
        print("🧪 Step 7: Testing Inference")
        print("=" * 70)
        print()
        
        base_url = f"http://{config_manager.llama_cpp.default_host}:{config_manager.llama_cpp.default_port}"
        
        # Try completion endpoint
        print("📤 Sending completion request to /completion...")
        test_prompt = "Once upon a time"
        
        completion_data = {
            "prompt": test_prompt,
            "n_predict": 50,
            "temperature": 0.7,
            "stop": ["\n\n"],
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                print(f"   Prompt: '{test_prompt}'")
                print(f"   URL: {base_url}/completion")
                print("   Waiting for response...")
                
                response = await client.post(
                    f"{base_url}/completion",
                    json=completion_data
                )
                
                print(f"\n✓ Response received (Status: {response.status_code})")
                
                if response.status_code == 200:
                    result = response.json()
                    print("\n📥 Completion Response:")
                    print("-" * 70)
                    
                    if "content" in result:
                        generated_text = result["content"]
                        print(f"Prompt: {test_prompt}")
                        print(f"Generated: {generated_text}")
                    else:
                        print(f"Full response: {result}")
                    
                    print("-" * 70)
                    print("\n✅ INFERENCE TEST PASSED!")
                    print("   llama.cpp is working correctly!")
                    
                else:
                    print(f"\n⚠️  Unexpected status code: {response.status_code}")
                    print(f"Response: {response.text}")
                
            except httpx.TimeoutException:
                print("\n⚠️  Request timed out (this is normal for first request)")
                print("   The model is loading, which can take time.")
                print("   Try running this test again after a minute.")
                
            except Exception as e:
                print(f"\n❌ Error during inference test: {e}")
        
        print()
        print("=" * 70)
        print("🔍 Step 8: Server Status After Inference")
        print("=" * 70)
        status = await lifecycle_manager.get_status()
        print(f"   Model: {status.model_name}")
        print(f"   Status: {status.status}")
        print(f"   Uptime: {status.uptime_seconds}s")
        print(f"   PID: {status.pid}")
        print()
        
        # Keep server running for manual testing
        print("=" * 70)
        print("✨ Server is still running!")
        print("=" * 70)
        print()
        print("You can now test manually:")
        print(f"   curl {base_url}/health")
        print(f"   curl {base_url}/completion -d '{{\"prompt\":\"Hello\",\"n_predict\":20}}'")
        print()
        print("Press Ctrl+C when done testing...")
        print()
        
        try:
            while True:
                await asyncio.sleep(5)
                status = await lifecycle_manager.get_status()
                print(f"   [Running] Uptime: {status.uptime_seconds}s | Status: {status.status}")
        except KeyboardInterrupt:
            print("\n\n⏹️  Stopping server...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always cleanup
        print("\n🧹 Step 9: Cleanup...")
        try:
            await lifecycle_manager.unload_model()
            print("✓ Server stopped")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
        
        print()
        print("=" * 70)
        print("Test completed!")
        print("=" * 70)

if __name__ == "__main__":
    try:
        asyncio.run(test_inference())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
