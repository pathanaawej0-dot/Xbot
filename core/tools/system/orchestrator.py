import subprocess
import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.base import BaseTool, ToolResult

class SpawnAgentTool(BaseTool):
    """Tool for spawning child Xbot agents for background tasks."""
    
    name = "spawn_agent"
    description = "Spawns a sub-agent to perform a background task. Use for long project audits or migrations."

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The specific instruction for the child agent."}
            },
            "required": ["task"]
        }

    async def execute(self, task: str) -> ToolResult:
        """Spawn a child agent with diagnostic support."""
        try:
            # Command to run main.py with the task as first argument
            cmd = [sys.executable, "main.py", task]
            
            # Start process in background
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            return ToolResult.text_result(
                f"Agent spawned successfully with Task: '{task}'. PID: {process.pid}",
                details={"pid": process.pid}
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Failed to spawn agent: {str(e)}",
                details={"task": task},
                hint="Verify that 'main.py' exists and Python is properly configured in the PATH."
            )

class InstallSkillTool(BaseTool):
    """Tool for downloading skills from remote URLs into the local skills library."""
    
    name = "install_skill"
    description = "Downloads a skill from ClawHub or any URL. Use to extend capabilities."

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to the raw SKILL.md file."},
                "name": {"type": "string", "description": "Optional name for the local skill folder."}
            },
            "required": ["url"]
        }

    async def execute(self, url: str, name: Optional[str] = None) -> ToolResult:
        """Download and install a skill with diagnostic support."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            
            # If name is not provided, try to extract from github URL or use 'remote_skill'
            if not name:
                name = url.split("/")[-1].replace(".md", "").replace("SKILL", "").strip("-") or "remote_skill"
            
            target_dir = Path("skills") / name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            with open(target_dir / "SKILL.md", "w", encoding="utf-8") as f:
                f.write(content)
                
            return ToolResult.text_result(
                f"Skill '{name}' installed successfully from {url}.",
                details={"target_dir": str(target_dir)}
            )
        except requests.RequestException as e:
            return ToolResult.error_result(
                f"Network error during installation: {str(e)}",
                details={"url": url}
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Failed to install skill: {type(e).__name__}: {str(e)}",
                details={"url": url}
            )
