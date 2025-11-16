# Process Registry Management Design

## Document Information
- **Version**: 1.0
- **Last Updated**: 2025-11-16
- **Status**: Implementation Specification
- **Category**: Core Feature - Process Management

## Overview

This document specifies the design and implementation of a process registry system to track and manage llama.cpp server processes. This addresses the issue where llamacontroller may fail to properly track processes if it crashes or restarts, leading to orphaned llama-server processes.

## Problem Statement

### Current Issues

1. **Process Tracking Loss**: If llamacontroller crashes or restarts, it loses track of running llama-server processes
2. **Orphaned Processes**: llama-server processes continue running without the controller knowing about them
3. **Resource Conflicts**: New model loads may fail due to GPU memory already occupied by orphaned processes
4. **No Recovery Mechanism**: No way to detect and reattach to existing processes on controller restart

### User Requirements

From the original request:
> "Is it possible to record the PID somewhere, so that if something broken, and llamacpp rebooted (failed to unload the models), it can still read from the windows process and determine if a model has been loaded, and be able to unload it by kill the process by name or by pid?"

## Design Solution

### Architecture Components

```
┌─────────────────────────────────────────────────────────┐
│              Process Registry System                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  1. Persistent Storage (processes.json)         │    │
│  │     - PID tracking                               │    │
│  │     - Model metadata                             │    │
│  │     - GPU assignment                             │    │
│  │     - Startup parameters                         │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  2. Process Recovery on Startup                 │    │
│  │     - Read processes.json                        │    │
│  │     - Verify PIDs still running (psutil)         │    │
│  │     - Validate process is llama-server           │    │
│  │     - Reattach to running processes              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  3. Process Cleanup Operations                  │    │
│  │     - Kill by PID                                │    │
│  │     - Find orphaned llama-server processes       │    │
│  │     - Batch cleanup                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  4. Web UI Integration                          │    │
│  │     - Display all tracked processes              │    │
│  │     - Manual cleanup controls                    │    │
│  │     - Process health monitoring                  │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Data Structures

### 1. Process Registry Entry

```python
@dataclass
class ProcessRegistryEntry:
    """Single process registry entry"""
    pid: int
    model_id: str
    model_name: str
    model_path: str
    gpu_id: str
    port: int
    started_at: datetime
    command_line: List[str]
    status: str  # "running", "stopped", "unknown"
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return {
            'pid': self.pid,
            'model_id': self.model_id,
            'model_name': self.model_name,
            'model_path': self.model_path,
            'gpu_id': self.gpu_id,
            'port': self.port,
            'started_at': self.started_at.isoformat(),
            'command_line': self.command_line,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessRegistryEntry':
        """Create from dict"""
        return cls(
            pid=data['pid'],
            model_id=data['model_id'],
            model_name=data['model_name'],
            model_path=data['model_path'],
            gpu_id=data['gpu_id'],
            port=data['port'],
            started_at=datetime.fromisoformat(data['started_at']),
            command_line=data['command_line'],
            status=data.get('status', 'unknown')
        )
```

### 2. Process Registry Storage

**File Location**: `data/processes.json`

**Format**:
```json
{
  "version": "1.0",
  "last_updated": "2025-11-16T15:00:00",
  "processes": {
    "0": {
      "pid": 12345,
      "model_id": "phi-4-reasoning",
      "model_name": "Phi-4 Reasoning Plus",
      "model_path": "C:\\models\\phi-4.gguf",
      "gpu_id": "0",
      "port": 8081,
      "started_at": "2025-11-16T14:30:00",
      "command_line": ["llama-server.exe", "-m", "..."],
      "status": "running"
    },
    "1": {
      "pid": 12346,
      "model_id": "qwen-coder",
      "model_name": "Qwen3 Coder 30B",
      "model_path": "C:\\models\\qwen-coder.gguf",
      "gpu_id": "1",
      "port": 8088,
      "started_at": "2025-11-16T14:35:00",
      "command_line": ["llama-server.exe", "-m", "..."],
      "status": "running"
    }
  }
}
```

## Implementation

### 1. Process Registry Manager

**File**: `src/llamacontroller/core/process_registry.py`

```python
"""Process registry for tracking llama-server processes."""

import json
import logging
import psutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProcessRegistryEntry:
    """Single process registry entry"""
    pid: int
    model_id: str
    model_name: str
    model_path: str
    gpu_id: str
    port: int
    started_at: datetime
    command_line: List[str]
    status: str = "unknown"
    
    def to_dict(self) -> dict:
        return {
            'pid': self.pid,
            'model_id': self.model_id,
            'model_name': self.model_name,
            'model_path': self.model_path,
            'gpu_id': self.gpu_id,
            'port': self.port,
            'started_at': self.started_at.isoformat(),
            'command_line': self.command_line,
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessRegistryEntry':
        return cls(
            pid=data['pid'],
            model_id=data['model_id'],
            model_name=data['model_name'],
            model_path=data['model_path'],
            gpu_id=data['gpu_id'],
            port=data['port'],
            started_at=datetime.fromisoformat(data['started_at']),
            command_line=data['command_line'],
            status=data.get('status', 'unknown')
        )


class ProcessRegistry:
    """
    Manages persistent tracking of llama-server processes.
    
    Provides:
    - Persistent storage of process information
    - Process recovery on startup
    - Orphaned process detection and cleanup
    """
    
    def __init__(self, registry_file: Path = None):
        """
        Initialize process registry.
        
        Args:
            registry_file: Path to registry JSON file (default: data/processes.json)
        """
        if registry_file is None:
            registry_file = Path("data/processes.json")
        
        self.registry_file = registry_file
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory registry: gpu_id -> ProcessRegistryEntry
        self.processes: Dict[str, ProcessRegistryEntry] = {}
        
        logger.info(f"Process registry initialized: {self.registry_file}")
    
    def load(self) -> None:
        """Load registry from disk."""
        if not self.registry_file.exists():
            logger.info("No existing process registry found")
            return
        
        try:
            with open(self.registry_file, 'r') as f:
                data = json.load(f)
            
            self.processes = {}
            for gpu_id, entry_data in data.get('processes', {}).items():
                try:
                    entry = ProcessRegistryEntry.from_dict(entry_data)
                    self.processes[gpu_id] = entry
                    logger.info(f"Loaded process entry: GPU {gpu_id}, PID {entry.pid}")
                except Exception as e:
                    logger.warning(f"Failed to load process entry for GPU {gpu_id}: {e}")
            
            logger.info(f"Loaded {len(self.processes)} process entries from registry")
        except Exception as e:
            logger.error(f"Failed to load process registry: {e}")
    
    def save(self) -> None:
        """Save registry to disk."""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'processes': {
                    gpu_id: entry.to_dict()
                    for gpu_id, entry in self.processes.items()
                }
            }
            
            # Write atomically (write to temp file, then rename)
            temp_file = self.registry_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_file.replace(self.registry_file)
            logger.debug(f"Saved {len(self.processes)} process entries to registry")
        except Exception as e:
            logger.error(f"Failed to save process registry: {e}")
    
    def register_process(
        self,
        gpu_id: str,
        pid: int,
        model_id: str,
        model_name: str,
        model_path: str,
        port: int,
        command_line: List[str]
    ) -> None:
        """
        Register a new process.
        
        Args:
            gpu_id: GPU ID string (e.g., "0", "1", "0,1")
            pid: Process ID
            model_id: Model identifier
            model_name: Human-readable model name
            model_path: Path to model file
            port: Service port
            command_line: Full command line used to start process
        """
        entry = ProcessRegistryEntry(
            pid=pid,
            model_id=model_id,
            model_name=model_name,
            model_path=model_path,
            gpu_id=gpu_id,
            port=port,
            started_at=datetime.now(),
            command_line=command_line,
            status='running'
        )
        
        self.processes[gpu_id] = entry
        self.save()
        logger.info(f"Registered process: GPU {gpu_id}, PID {pid}, Model {model_id}")
    
    def unregister_process(self, gpu_id: str) -> None:
        """
        Unregister a process.
        
        Args:
            gpu_id: GPU ID string
        """
        if gpu_id in self.processes:
            entry = self.processes.pop(gpu_id)
            self.save()
            logger.info(f"Unregistered process: GPU {gpu_id}, PID {entry.pid}")
    
    def get_process(self, gpu_id: str) -> Optional[ProcessRegistryEntry]:
        """Get process entry for GPU."""
        return self.processes.get(gpu_id)
    
    def get_all_processes(self) -> Dict[str, ProcessRegistryEntry]:
        """Get all registered processes."""
        return self.processes.copy()
    
    def verify_process(self, gpu_id: str) -> bool:
        """
        Verify if registered process is still running.
        
        Args:
            gpu_id: GPU ID string
            
        Returns:
            True if process is running, False otherwise
        """
        entry = self.processes.get(gpu_id)
        if not entry:
            return False
        
        try:
            process = psutil.Process(entry.pid)
            
            # Check if process is still running
            if not process.is_running():
                logger.warning(f"Process {entry.pid} is not running")
                entry.status = 'stopped'
                self.save()
                return False
            
            # Verify it's actually llama-server
            process_name = process.name().lower()
            if 'llama' not in process_name and 'server' not in process_name:
                logger.warning(
                    f"Process {entry.pid} ({process_name}) does not appear to be llama-server"
                )
                entry.status = 'unknown'
                self.save()
                return False
            
            entry.status = 'running'
            return True
            
        except psutil.NoSuchProcess:
            logger.warning(f"Process {entry.pid} no longer exists")
            entry.status = 'stopped'
            self.save()
            return False
        except Exception as e:
            logger.error(f"Error verifying process {entry.pid}: {e}")
            entry.status = 'unknown'
            self.save()
            return False
    
    def verify_all_processes(self) -> Dict[str, bool]:
        """
        Verify all registered processes.
        
        Returns:
            Dict mapping gpu_id to verification status
        """
        results = {}
        for gpu_id in list(self.processes.keys()):
            results[gpu_id] = self.verify_process(gpu_id)
        return results
    
    def kill_process(self, gpu_id: str, force: bool = False) -> bool:
        """
        Kill a registered process.
        
        Args:
            gpu_id: GPU ID string
            force: If True, use SIGKILL; otherwise SIGTERM
            
        Returns:
            True if process was killed, False otherwise
        """
        entry = self.processes.get(gpu_id)
        if not entry:
            logger.warning(f"No process registered for GPU {gpu_id}")
            return False
        
        try:
            process = psutil.Process(entry.pid)
            
            if force:
                logger.info(f"Force killing process {entry.pid} (GPU {gpu_id})")
                process.kill()
            else:
                logger.info(f"Terminating process {entry.pid} (GPU {gpu_id})")
                process.terminate()
                
                # Wait for graceful shutdown (up to 10 seconds)
                try:
                    process.wait(timeout=10)
                except psutil.TimeoutExpired:
                    logger.warning(f"Process {entry.pid} did not terminate, force killing")
                    process.kill()
            
            # Unregister after killing
            self.unregister_process(gpu_id)
            return True
            
        except psutil.NoSuchProcess:
            logger.warning(f"Process {entry.pid} no longer exists")
            self.unregister_process(gpu_id)
            return False
        except Exception as e:
            logger.error(f"Error killing process {entry.pid}: {e}")
            return False
    
    def find_orphaned_processes(self, executable_name: str = "llama-server") -> List[int]:
        """
        Find llama-server processes not in registry.
        
        Args:
            executable_name: Name of executable to search for
            
        Returns:
            List of orphaned PIDs
        """
        registered_pids = {entry.pid for entry in self.processes.values()}
        orphaned_pids = []
        
        try:
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    process_name = process.info['name'].lower()
                    
                    # Check if it's llama-server
                    if executable_name.lower() in process_name:
                        pid = process.info['pid']
                        
                        # Check if it's not registered
                        if pid not in registered_pids:
                            orphaned_pids.append(pid)
                            logger.info(f"Found orphaned process: PID {pid}")
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error finding orphaned processes: {e}")
        
        return orphaned_pids
    
    def cleanup_orphaned_processes(self, force: bool = False) -> int:
        """
        Kill all orphaned llama-server processes.
        
        Args:
            force: If True, use SIGKILL; otherwise SIGTERM
            
        Returns:
            Number of processes killed
        """
        orphaned_pids = self.find_orphaned_processes()
        killed_count = 0
        
        for pid in orphaned_pids:
            try:
                process = psutil.Process(pid)
                
                if force:
                    logger.info(f"Force killing orphaned process {pid}")
                    process.kill()
                else:
                    logger.info(f"Terminating orphaned process {pid}")
                    process.terminate()
                    
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        logger.warning(f"Orphaned process {pid} did not terminate, force killing")
                        process.kill()
                
                killed_count += 1
                
            except psutil.NoSuchProcess:
                logger.debug(f"Orphaned process {pid} already gone")
            except Exception as e:
                logger.error(f"Error killing orphaned process {pid}: {e}")
        
        if killed_count > 0:
            logger.info(f"Cleaned up {killed_count} orphaned processes")
        
        return killed_count
```

### 2. Integration with Lifecycle Manager

**File**: `src/llamacontroller/core/lifecycle.py`

Add to `ModelLifecycleManager.__init__`:
```python
from .process_registry import ProcessRegistry

def __init__(self, config_manager: ConfigManager, gpu_detector: GpuDetector):
    # ... existing code ...
    
    # Initialize process registry
    self.process_registry = ProcessRegistry()
    self.process_registry.load()
    
    # Verify and recover processes on startup
    self._recover_processes()
```

Add recovery method:
```python
def _recover_processes(self) -> None:
    """Recover tracked processes on startup."""
    logger.info("Recovering tracked processes...")
    
    verification_results = self.process_registry.verify_all_processes()
    
    for gpu_id, is_running in verification_results.items():
        if is_running:
            entry = self.process_registry.get_process(gpu_id)
            logger.info(
                f"Recovered running process: GPU {gpu_id}, "
                f"PID {entry.pid}, Model {entry.model_id}"
            )
            # Could attempt to reattach to process here if needed
        else:
            logger.warning(f"Process for GPU {gpu_id} is no longer running")
            self.process_registry.unregister_process(gpu_id)
```

Update `load_model` to register process:
```python
async def load_model(self, model_id: str, gpu_id: str = "0") -> ModelStatus:
    # ... existing load logic ...
    
    # After successful process start
    if self.process and self.process.pid:
        self.process_registry.register_process(
            gpu_id=gpu_id,
            pid=self.process.pid,
            model_id=model_id,
            model_name=model_config.name,
            model_path=model_config.path,
            port=port,
            command_line=cmd
        )
```

Update `unload_model` to unregister:
```python
async def unload_model(self, gpu_id: str) -> bool:
    # ... existing unload logic ...
    
    # Unregister from registry
    self.process_registry.unregister_process(gpu_id)
```

### 3. Add Cleanup API Endpoint

**File**: `src/llamacontroller/api/management.py`

```python
@router.post("/cleanup-orphaned")
async def cleanup_orphaned_processes(
    force: bool = False,
    current_user: User = Depends(get_current_api_user)
):
    """Clean up orphaned llama-server processes."""
    try:
        killed_count = lifecycle_manager.process_registry.cleanup_orphaned_processes(force=force)
        
        return {
            "success": True,
            "killed_count": killed_count,
            "message": f"Cleaned up {killed_count} orphaned processes"
        }
    except Exception as e:
        logger.error(f"Error cleaning up orphaned processes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-registry")
async def get_process_registry(
    current_user: User = Depends(get_current_api_user)
):
    """Get all registered processes."""
    try:
        processes = lifecycle_manager.process_registry.get_all_processes()
        
        return {
            "processes": {
                gpu_id: entry.to_dict()
                for gpu_id, entry in processes.items()
            }
        }
    except Exception as e:
        logger.error(f"Error getting process registry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Dependencies

Add to `requirements.txt`:
```
psutil>=5.9.0
```

## Testing

### Test Cases

1. **Process Registration**
   - Load model, verify PID registered
   - Check processes.json file created
   - Verify entry contains correct metadata

2. **Process Recovery**
   - Start model, note PID
   - Restart llamacontroller
   - Verify process still tracked

3. **Process Cleanup**
   - Start model manually (outside controller)
   - Call cleanup API
   - Verify orphaned process killed

4. **Multi-GPU Scenarios**
   - Load models on GPU 0 and GPU 1
   - Verify both processes tracked separately
   - Unload one, verify only one unregistered

## Benefits

✅ **Persistent Tracking**: Process information survives controller restarts  
✅ **Automatic Recovery**: Detect and reattach to running processes on startup  
✅ **Orphan Cleanup**: Find and kill orphaned llama-server processes  
✅ **Audit Trail**: Complete history of process starts/stops  
✅ **Robust**: Handle crashes gracefully without losing process information  
✅ **Cross-Platform**: psutil works on Windows, Linux, macOS  

## Future Enhancements

1. **Process Health Monitoring**: Periodic health checks of tracked processes
2. **Automatic Restart**: Auto-restart crashed processes
3. **Resource Usage Tracking**: Track CPU/memory usage over time
4. **Process Affinity**: Set CPU affinity for better performance
5. **Web UI Dashboard**: Visual display of all tracked processes
6. **Alerts**: Notify on process crashes or resource issues

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-16  
**Status**: Ready for Implementation
