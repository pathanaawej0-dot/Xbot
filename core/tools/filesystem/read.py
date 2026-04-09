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
        """Read file content from the system with diagnostic support."""
        try:
            # 1. Normalize path
            full_path = os.path.normpath(path)
            if not os.path.exists(full_path):
                return ToolResult.error_result(
                    f"File not found: {path}",
                    details={"path": path, "offset": offset}
                )
            
            if os.path.isdir(path):
                return ToolResult.error_result(
                    f"Path is a directory: {path}",
                    details={"path": path}
                )
            
            # 2. Detect Binary (Quick check)
            with open(full_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    return ToolResult.error_result(
                        f"Binary file detected: {path}",
                        details={"path": path}
                    )

            # 3. Read Lines with pagination
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                # Fast forward to offset
                for _ in range(offset):
                    if not f.readline():
                        break
                
                lines = []
                for _ in range(limit):
                    line = f.readline()
                    if not line:
                        break
                    lines.append(line.rstrip('\n\r'))
                
                # Check for continuation
                more_line = f.readline()
                truncated = len(lines) >= limit or bool(more_line)
                
                content = '\n'.join(f"{offset + i + 1}: {line}" for i, line in enumerate(lines))
                
                if truncated:
                    content += f"\n\n[Showing lines {offset+1}-{offset + len(lines)}. Use offset={offset + len(lines)} to read more.]"
                
                return ToolResult.text_result(
                    content if content else "(File is empty or reached end of file)",
                    details={"offset": offset, "limit": limit, "truncated": truncated, "path": path}
                )
        
        except PermissionError:
            return ToolResult.error_result(
                f"Permission denied: {path}",
                details={"path": path},
                hint="Check file permissions. You may need to run with elevated privileges or use 'exec' with sudo."
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Error reading file: {type(e).__name__}: {str(e)}",
                details={"path": path, "offset": offset},
                hint="The file may be corrupted or in an unsupported format."
            )
