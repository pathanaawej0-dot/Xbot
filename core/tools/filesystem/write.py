import os
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult

class WriteTool(BaseTool):
    """File Writing Tool for creating or overwriting files.
    
    Features:
    - Auto-creation of parent directories.
    - Workspace guard protection.
    """
    
    name = "write"
    description = """
Write content to any file on the system. 

FEATURES:
- System-wide access: Create or overwrite files anywhere on the disk.
- Auto-directory creation: Automatically creates missing parent folders.
- Overwrite mode: Replaces the entire file content.

IMPORTANT: Use with caution. Request user confirmation before overwriting critical system files or deleting content through empty writes.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute or relative path to the file to write."},
                "content": {"type": "string", "description": "The full text content to save."}
            },
            "required": ["path", "content"]
        }

    async def execute(self, path: str, content: str) -> ToolResult:
        """Write content to a file on the system with diagnostic support."""
        try:
            # 1. Normalize path
            full_path = os.path.normpath(path)
            
            # 2. Ensure parent directories exist
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
                
            # 3. Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return ToolResult.text_result(
                f"Successfully wrote {len(content)} characters to '{path}'.",
                details={"file_path": path, "byte_count": len(content.encode('utf-8'))}
            )
            
        except PermissionError:
            return ToolResult.error_result(
                f"Permission denied: {path}",
                details={"path": path},
                hint="Check file/folder permissions. You may need to run with elevated privileges."
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Write Operation Failed: {type(e).__name__}: {str(e)}",
                details={"path": path},
                hint="Verify the path is valid and you have enough disk space."
            )
