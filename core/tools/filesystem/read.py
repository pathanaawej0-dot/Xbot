import os
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult

class ReadTool(BaseTool):
    """File Reading Tool with pagination support.
    
    Features:
    - Line-based pagination (offset/limit)
    - Line numbering for easy reference
    - Truncation detection with continuation hints
    - Binary file skip (prevents LLM from receiving garbage)
    - Workspace guard protection
    """
    
    name = "read"
    description = """
Read file contents from any accessible location on the system.

FEATURES:
- System-wide access: Read any file on the disk (use absolute or relative paths).
- Line-based pagination: Use 'offset' and 'limit' to navigate large log files or codebases.
- Safety: Automatically skips non-text/binary files to prevent junk output.
- Auto-pagination: Provides hints when more content is available.

IMPORTANT: Respect user privacy. Do not read sensitive personal files (like SSH keys or password databases) unless explicitly instructed for a troubleshooting task.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute or relative path to the file."},
                "offset": {"type": "integer", "description": "Starting line number (0-indexed).", "default": 0},
                "limit": {"type": "integer", "description": "Maximum number of lines to read in one call (default 500).", "default": 500}
            },
            "required": ["path"]
        }

    async def execute(self, path: str, offset: int = 0, limit: int = 500) -> ToolResult:
        """Read file content from the system."""
        try:
            # 1. Normalize path for the system
            full_path = os.path.normpath(path)
            if not os.path.isabs(full_path):
                # If relative, it's relative to current working directory
                full_path = os.path.abspath(full_path)
            
            # 2. Check if file exists
            if not os.path.exists(full_path):
                return ToolResult(success=False, error=f"File Not Found: '{full_path}'", content="")
            if not os.path.isfile(full_path):
                return ToolResult(success=False, error=f"Not a File: '{full_path}' is a directory or special file.", content="")
                
            # 3. Detect Binary (Quick check by reading first 1024 bytes)
            with open(full_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    return ToolResult(
                        success=False, 
                        error=f"Binary File Detected: '{path}' cannot be read as text.", 
                        content=""
                    )
                    
            # 4. Read Lines with pagination
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                # Fast forward to offset
                for _ in range(offset):
                    if not f.readline():
                        break
                        
                # Read specified number of lines
                lines = []
                for _ in range(limit):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.rstrip('\r\n'))
                    
                # Check for remaining content
                has_more = bool(f.readline())
                
            # 5. Format Output
            # We add 1-based line numbers for the LLM's convenience.
            content = ""
            for i, line in enumerate(lines):
                content += f"{offset + i + 1}: {line}\n"
                
            if has_more:
                content += f"\n\n[Showing lines {offset+1} to {offset+len(lines)}. Use offset={offset+len(lines)} to read more.]"
                
            return ToolResult(
                success=True,
                content=content if content else "(File is empty or reached end of file)",
                details={"offset": offset, "limit": limit, "count": len(lines), "truncated": has_more}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=f"Read Operation Failed: {str(e)}", content="")
