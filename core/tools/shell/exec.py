import asyncio
import os
import time
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult

class ExecTool(BaseTool):
    """Execution Tool for running shell commands.
    
    This is the primary interface for the AI to interact with the OS.
    Features:
    - stdout/stderr capture
    - timeout enforcement
    - working directory support
    - environment variable injection
    - background execution
    """
    
    name = "exec"
    description = """
Run shell commands on your system. This is your primary interface to the OS.

CAPABILITIES:
- Run any command, script, or binary.
- Capture stdout, stderr, and the return code.
- Set working directory and environment variables.
- Timeout control (auto-kill if a command runs too long).
- Background execution mode (starts a process without waiting for it).

EXAMPLES:
- "ls -la" → list directory contents.
- "python script.py" → execute local scripts.
- "git status" → check repository state.

IMPORTANT: This tool provides full system access. Use it wisely.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."},
                "timeout_sec": {"type": "number", "description": "Maximum seconds before killing the command (default 30).", "default": 30},
                "workdir": {"type": "string", "description": "Directory to run the command in (absolute or relative to current process)."},
                "env": {"type": "object", "description": "Environment variables to set for the process."},
                "background": {"type": "boolean", "description": "If true, start the process without waiting (returns a session_id).", "default": False}
            },
            "required": ["command"]
        }

    async def execute(
        self, 
        command: str, 
        timeout_sec: float = 30.0, 
        workdir: Optional[str] = None, 
        env: Optional[Dict[str, str]] = None, 
        background: bool = False
    ) -> ToolResult:
        start_time = time.monotonic()
        
        # 1. Resolve workdir (Limitless)
        resolved_workdir = os.path.abspath(workdir) if workdir else os.getcwd()
            
        # 2. Build environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
            
        # 3. Create subprocess
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=resolved_workdir,
                env=exec_env,
                limit=10_000_000  # 10MB safety limit on output
            )
            
            # 4. Handle Background Mode
            if background:
                # In a real implementation, we would register this process with a process manager.
                # Since we're in the middle of a migration, we'll return the PID as the session_id.
                return ToolResult(
                    success=True,
                    content=f"Background process started: PID={process.pid}. Use 'process' tool to interact with it.",
                    details={"pid": process.pid, "session_id": str(process.pid)}
                )
                
            # 5. Handle Synchronous Mode with Timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_sec
                )
            except asyncio.TimeoutError:
                # Force kill if it's hanging
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                return ToolResult(
                    success=False,
                    error=f"Execution Timed Out: Command '{command}' failed to finish within {timeout_sec} seconds.",
                    content="",
                    details={"status": "killed"}
                )
                
            # 6. Success Result
            duration_ms = int((time.monotonic() - start_time) * 1000)
            stdout_str = stdout.decode(errors='replace')
            stderr_str = stderr.decode(errors='replace')
            
            return ToolResult(
                success=(process.returncode == 0),
                content=stdout_str if stdout_str else f"(No stdout) [Exit code: {process.returncode}]",
                details={
                    "returncode": process.returncode,
                    "stderr": stderr_str,
                    "duration_ms": duration_ms
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Shell Execution Failed: {str(e)}",
                content=""
            )
