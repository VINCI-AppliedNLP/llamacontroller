"""
LlamaController startup script.
Run this from the project root directory.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Now import and run
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "llamacontroller.main:app",
        host="0.0.0.0",
        port=3000,
        reload=True,
        log_level="info"
    )
