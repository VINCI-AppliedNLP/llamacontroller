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


class ProcessRegistry:
    """
    Manages persistent tracking of llama-server processes.
    
    Provides:
    - Persistent storage of process information
    - Process recovery on startup
    - Orphaned process detection and cleanup
    """
    
    def __init__(self, registry_file: Optional[Path] = None):
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
