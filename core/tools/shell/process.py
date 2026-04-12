import asyncio
from typing import Dict, Any, Optional, List
from core.base import BaseTool, ToolResult
from core.process_registry import ProcessRegistry

class ProcessTool(BaseTool):
    """Process Management Tool for inspecting and controlling background commands.
    
    This tool allows the AI to:
    - List active processes
    - Poll for completion and output
    - Kill hanging processes
    - Send stdin to interactive processes
    """
    
    name = "process"
    description = """
Inspect and control running processes initiated by the 'exec' tool's background mode.

ACTIONS:
- "list": Show all currently running background processes.
- "poll": Check if a process has finished and retrieve its final output.
- "kill": Force alternate termination of a running process.
- "send": Send input (stdin) to a process that is waiting for data.

Use the 'session_id' (PID) returned by the 'exec' tool's background mode response.
"""

    def __init__(self, registry: ProcessRegistry = None):
        super().__init__()
        self.registry = registry

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "poll", "kill", "send"], "description": "The control action to perform."},
                "session_id": {"type": "string", "description": "The process identifier (PID) returned from background exec."},
                "data": {"type": "string", "description": "Content to send to process stdin (for 'send' action)."}
            },
            "required": ["action"]
        }

    async def execute(self, action: str, session_id: Optional[str] = None, data: Optional[str] = None) -> ToolResult:
        """Handle process lifecycle management with diagnostic support."""
        
        # 1. Action: List
        if action == "list":
            active_list = self.registry.list_processes() if self.registry else []
            return ToolResult.text_result(
                f"Active Background Processes: {active_list}",
                details={"active_count": len(active_list)}
            )
            
        # 2. Validation for targeted actions
        if not session_id:
            return ToolResult.error_result(
                "Parameter 'session_id' is required for this action."
            )
            
        proc = self.registry.get_process(session_id) if self.registry else None
        if not proc:
            return ToolResult.error_result(
                f"No active process found with session_id '{session_id}'",
                details={"session_id": session_id}
            )
            
        # 3. Action: Poll
        if action == "poll":
            if proc.returncode is not None:
                # Process already finished
                stdout, stderr = await proc.communicate()
                if self.registry:
                    self.registry.remove_process(session_id)
                return ToolResult.text_result(
                    stdout.decode(errors='replace'),
                    details={"status": "finished", "returncode": proc.returncode, "stderr": stderr.decode(errors='replace')}
                )
            else:
                # Still running check
                try:
                    await asyncio.wait_for(proc.wait(), timeout=0.1)
                    stdout, stderr = await proc.communicate()
                    if self.registry:
                        self.registry.remove_process(session_id)
                    return ToolResult.text_result(
                        stdout.decode(errors='replace'),
                        details={"status": "finished", "returncode": proc.returncode}
                    )
                except asyncio.TimeoutError:
                    return ToolResult.text_result(
                        "(Process is still running. No new output captured.)",
                        details={"status": "running", "pid": proc.pid}
                    )
                    
        # 4. Action: Kill
        if action == "kill":
            try:
                proc.kill()
                await proc.wait()
                if self.registry:
                    self.registry.remove_process(session_id)
                return ToolResult.text_result(f"Process {session_id} terminated successfully.")
            except Exception as e:
                return ToolResult.error_result(f"Kill Failure: {str(e)}")
                
        # 5. Action: Send
        if action == "send":
            if not data:
                return ToolResult.error_result("Parameter 'data' is required for the 'send' action.")
            try:
                if proc.stdin:
                    proc.stdin.write(data.encode())
                    await proc.stdin.drain()
                    return ToolResult.text_result("Data transmitted to process stdin.")
                else:
                    return ToolResult.error_result("Process Error: stdin is not available for this process.")
            except Exception as e:
                return ToolResult.error_result(f"Send Failure: {str(e)}")
                
        return ToolResult.error_result(f"Unknown Action: '{action}'")
