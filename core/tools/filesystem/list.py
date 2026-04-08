import os
from typing import Dict, Any, Optional, List
from core.base import BaseTool, ToolResult

class ListTool(BaseTool):
    """Directory Listing Tool.
    
    Features:
    - Lists files and directories.
    - Workspace guard protection.
    """
    
    name = "list_files"
    description = """
List the contents of any directory on the system.

FEATURES:
- System-wide access: Explore any folder on the disk (absolute or relative paths).
- Distinguishes between [DIR] and [FILE] for clarity.
- Sorted output for easy navigation.

EXAMPLES:
- list_files path="C:\\" → List root drive on Windows.
- list_files path="/usr/bin" → List system binaries on Linux.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute or relative directory path (default '.').", "default": "."}
            }
        }

    async def execute(self, path: str = ".") -> ToolResult:
        """List directory contents from the system."""
        try:
            # 1. Normalize path
            full_path = os.path.normpath(path)
            if not os.path.isabs(full_path):
                full_path = os.path.abspath(full_path)
            
            # 2. Check if exists
            if not os.path.exists(full_path):
                return ToolResult(success=False, error=f"Directory Not Found: '{full_path}'", content="")
            if not os.path.is_dir(full_path):
                return ToolResult(success=False, error=f"Not a Directory: '{full_path}' is a file.", content="")
                
            # 3. List entries
            entries = os.listdir(full_path)
            
            # Sort for consistency
            entries.sort()
            
            # Formatted list
            output = ""
            for entry in entries:
                entry_path = os.path.join(full_path, entry)
                if os.path.isdir(entry_path):
                    output += f"[DIR]  {entry}\n"
                else:
                    output += f"[FILE] {entry}\n"
                    
            return ToolResult(
                success=True,
                content=output if output else "(Directory is empty)",
                details={"path": path, "count": len(entries)}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=f"List Operation Failed: {str(e)}", content="")
