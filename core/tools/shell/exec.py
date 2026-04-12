import asyncio
import os
import time
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult
from core.process_registry import ProcessRegistry

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

    def __init__(self, registry: ProcessRegistry = None):
        super().__init__()
        self.registry = registry

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
        
        # 1. Build environment
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
            
        try:
            # 2. Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workdir,
                env=exec_env,
                limit=10_000_000  # 10MB safety limit on output
            )
            
            # 3. Handle Background Mode
            if background:
                session_id = str(process.pid)
                if self.registry:
                    self.registry.add_process(session_id, process, command, workdir)
                return ToolResult.text_result(
                    f"Background process started: PID={process.pid}",
                    details={"pid": process.pid, "session_id": session_id}
                )
                
            # 4. Handle Synchronous Mode with Timeout
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
                try:
                    stdout, stderr = await process.communicate()
                except Exception:
                    stdout, stderr = b"", b""
                
                return ToolResult.error_result(
                    f"Command timed out after {timeout_sec} seconds",
                    details={
                        "timeout": True,
                        "timeout_sec": timeout_sec,
                        "stdout": stdout.decode(errors='replace'),
                        "stderr": stderr.decode(errors='replace'),
                        "duration_ms": int((time.monotonic() - start_time) * 1000)
                    }
                )
                
            # 5. Check Exit Code
            if process.returncode != 0:
                return ToolResult.error_result(
                    f"Command exited with code {process.returncode}",
                    details={
                        "returncode": process.returncode,
                        "stdout": stdout.decode(errors='replace'),
                        "stderr": stderr.decode(errors='replace'),
                        "duration_ms": int((time.monotonic() - start_time) * 1000)
                    }
                )

            # 6. Success Result
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return ToolResult.text_result(
                stdout.decode(errors='replace') if stdout else "",
                details={
                    "returncode": 0,
                    "stderr": stderr.decode(errors='replace'),
                    "duration_ms": duration_ms
                }
            )
            
        except FileNotFoundError as e:
            cmd_name = command.split()[0] if command else "unknown"
            return ToolResult.error_result(
                f"Command not found: {cmd_name}",
                details={"error": str(e), "command": command}
            )
        except PermissionError as e:
            return ToolResult.error_result(
                f"Permission denied: {command}",
                details={"error": str(e)}
            )
        except Exception as e:
            error_type = type(e).__name__
            return ToolResult.error_result(
                f"Shell Execution Error ({error_type}): {str(e)}",
                details={"error_type": error_type, "command": command}
            )
