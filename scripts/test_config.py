"""
Test script to validate configuration loading.

This script tests the configuration manager and validates that all
configuration files are properly loaded and validated.
"""

import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from llamacontroller.utils.logging import setup_logging
from llamacontroller.core.config import ConfigManager, ConfigError

def main():
    """Main test function."""
    print("=" * 70)
    print("LlamaController Configuration Test")
    print("=" * 70)
    print()
    
    # Setup logging
    setup_logging(log_level="INFO", console_output=True)
    
    try:
        # Initialize configuration manager
        print("📋 Initializing ConfigManager...")
        config_manager = ConfigManager(config_dir="./config")
        print("✓ ConfigManager initialized\n")
        
        # Load configuration
        print("📥 Loading configuration files...")
        config = config_manager.load_config()
        print("✓ Configuration loaded successfully\n")
        
        # Display llama.cpp configuration
        print("🔧 llama.cpp Configuration:")
        print(f"  Executable: {config.llama_cpp.executable_path}")
        print(f"  Host: {config.llama_cpp.default_host}")
        print(f"  Port: {config.llama_cpp.default_port}")
        print(f"  Log Level: {config.llama_cpp.log_level}")
        print(f"  Restart on Crash: {config.llama_cpp.restart_on_crash}")
        print(f"  Max Restart Attempts: {config.llama_cpp.max_restart_attempts}")
        print(f"  Timeout: {config.llama_cpp.timeout_seconds}s")
        print()
        
        # Display models configuration
        print(f"📦 Models Configuration ({len(config.models.models)} models):")
        for model in config.models.models:
            print(f"\n  Model ID: {model.id}")
            print(f"  Name: {model.name}")
            print(f"  Path: {model.path}")
            print(f"  Parameters:")
            print(f"    - Context: {model.parameters.n_ctx}")
            print(f"    - GPU Layers: {model.parameters.n_gpu_layers}")
            print(f"    - Threads: {model.parameters.n_threads}")
            print(f"    - Temperature: {model.parameters.temperature}")
            print(f"  Metadata:")
            print(f"    - Description: {model.metadata.description}")
            print(f"    - Size: {model.metadata.parameter_count}")
            print(f"    - Quantization: {model.metadata.quantization}")
            print(f"    - Family: {model.metadata.family}")
        print()
        
        # Display authentication configuration
        print(f"🔐 Authentication Configuration:")
        print(f"  Session Timeout: {config.auth.session_timeout}s")
        print(f"  Max Login Attempts: {config.auth.max_login_attempts}")
        print(f"  Lockout Duration: {config.auth.lockout_duration}s")
        print(f"  Configured Users: {len(config.auth.users)}")
        for user in config.auth.users:
            print(f"    - {user.username} ({user.role})")
        print()
        
        # Validate configuration
        print("✅ Validating configuration...")
        warnings = config_manager.validate_config()
        if warnings:
            print("⚠️  Configuration Warnings:")
            for warning in warnings:
                print(f"  - {warning}")
        else:
            print("✓ No warnings found")
        print()
        
        # Test model retrieval
        print("🔍 Testing model retrieval...")
        model_ids = config.models.get_model_ids()
        print(f"  Available model IDs: {', '.join(model_ids)}")
        
        if model_ids:
            test_id = model_ids[0]
            test_model = config.models.get_model(test_id)
            if test_model:
                print(f"✓ Successfully retrieved model: {test_model.name}")
        print()
        
        # Test user retrieval
        print("👤 Testing user retrieval...")
        if config.auth.users:
            test_username = config.auth.users[0].username
            test_user = config.auth.get_user(test_username)
            if test_user:
                print(f"✓ Successfully retrieved user: {test_user.username}")
        print()
        
        print("=" * 70)
        print("✅ All configuration tests passed!")
        print("=" * 70)
        return 0
        
    except ConfigError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your configuration files and try again.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
