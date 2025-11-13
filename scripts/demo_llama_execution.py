"""
Demo script showing how to execute llama.cpp with the adapter.

This demonstrates the actual execution flow of llama-server.
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from llamacontroller.core.config import ConfigManager
from llamacontroller.core.lifecycle import ModelLifecycleManager

async def main():
    """Demonstrate llama.cpp execution."""
    
    print("=" * 60)
    print("LlamaController - llama.cpp Execution Demo")
    print("=" * 60)
    print()
    
    # Load configuration
    print("📋 Loading configuration...")
    config_manager = ConfigManager(config_dir="./config")
    config_manager.load_config()
    print(f"✓ Configuration loaded")
    print(f"  llama-server path: {config_manager.llama_cpp.executable_path}")
    print(f"  Default host: {config_manager.llama_cpp.default_host}")
    print(f"  Default port: {config_manager.llama_cpp.default_port}")
    print()
    
    # Create lifecycle manager
    print("🔧 Initializing lifecycle manager...")
    lifecycle_manager = ModelLifecycleManager(config_manager)
    print("✓ Lifecycle manager ready")
    print()
    
    # List available models
    print("📦 Available models:")
    models = lifecycle_manager.get_available_models()
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model.id}")
        print(f"     Name: {model.name}")
        print(f"     Path: {model.path}")
        print(f"     Quantization: {model.quantization}")
        print()
    
    if not models:
        print("❌ No models configured!")
        return
    
    # Choose first model for demo
    model_id = models[0].id
    print(f"🎯 Selected model: {model_id}")
    print()
    
    # Ask user if they want to actually load the model
    print("=" * 60)
    print("⚠️  READY TO EXECUTE llama-server")
    print("=" * 60)
    print()
    print("This will:")
    print(f"  1. Start llama-server subprocess")
    print(f"  2. Load model: {models[0].path}")
    print(f"  3. Bind to {config_manager.llama_cpp.default_host}:{config_manager.llama_cpp.default_port}")
    print(f"  4. Wait for server to be ready")
    print()
    
    response = input("Do you want to proceed? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("\n❌ Execution cancelled.")
        return
    
    print()
    print("🚀 Starting llama-server...")
    print("-" * 60)
    
    try:
        # Load the model (this will execute llama-server)
        load_response = await lifecycle_manager.load_model(model_id)
        
        if load_response.success:
            print()
            print("✅ llama-server started successfully!")
            print(f"   Model: {load_response.model_id}")
            print(f"   PID: {load_response.status.pid}")
            print(f"   Status: {load_response.status.status}")
            print(f"   Host: {load_response.status.host}:{load_response.status.port}")
            print()
            
            # Get status
            print("📊 Server status:")
            status = await lifecycle_manager.get_status()
            print(f"   Uptime: {status.uptime_seconds}s")
            print()
            
            # Health check
            print("🏥 Health check:")
            health = await lifecycle_manager.healthcheck()
            if health.healthy:
                print(f"   ✓ Server is healthy and responding")
            else:
                print(f"   ✗ Server is not responding: {health.message}")
            print()
            
            # Get recent logs
            print("📜 Recent logs (last 10 lines):")
            logs = await lifecycle_manager.get_server_logs(lines=10)
            for log_line in logs[-10:]:
                print(f"   {log_line}")
            print()
            
            # Keep running
            print("=" * 60)
            print("Server is running. Press Ctrl+C to stop...")
            print("=" * 60)
            
            try:
                while True:
                    await asyncio.sleep(5)
                    status = await lifecycle_manager.get_status()
                    print(f"Uptime: {status.uptime_seconds}s | Status: {status.status}")
            except KeyboardInterrupt:
                print("\n\n⏹️  Stopping server...")
        
        else:
            print(f"\n❌ Failed to start server: {load_response.message}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await lifecycle_manager.unload_model()
        print("✓ Server stopped")
        print()
        print("Demo completed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
