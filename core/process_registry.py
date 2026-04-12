import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ProcessRegistry:
    """Singleton-like registry for tracking background processes across tools.
    
    This ensures that background processes started by 'exec' can be 
    inspected or killed by 'process'.
    """
    
    def __init__(self):
        # session_id -> asyncio.subprocess.Process
        self.processes: Dict[str, Any] = {}
        # metadata for visualization/status
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def add_process(self, session_id: str, process: Any, command: str, workdir: Optional[str] = None):
        """Register a new background process."""
        self.processes[session_id] = process
        self.metadata[session_id] = {
            "command": command,
            "workdir": workdir,
            "start_time": asyncio.get_event_loop().time()
        }
        logger.info(f"Process {session_id} registered in registry.")

    def get_process(self, session_id: str) -> Optional[Any]:
        """Retrieve a process by its ID."""
        return self.processes.get(session_id)

    def list_processes(self) -> List[Dict[str, Any]]:
        """List all tracked processes and their basic status."""
        active = []
        for sid, proc in self.processes.items():
            active.append({
                "session_id": sid,
                "pid": proc.pid,
                "command": self.metadata.get(sid, {}).get("command", "unknown"),
                "running": proc.returncode is None
            })
        return active

    def remove_process(self, session_id: str):
        """Cleanup process entry if it's finished or killed."""
        if session_id in self.processes:
            del self.processes[session_id]
        if session_id in self.metadata:
            del self.metadata[session_id]
        logger.info(f"Process {session_id} removed from registry.")
