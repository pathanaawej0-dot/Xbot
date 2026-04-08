import os
import subprocess
import tempfile
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult

class ApplyPatchTool(BaseTool):
    """File Patching Tool for multi-line unified diffs.
    
    This tool uses the standard 'patch' utility if available, 
    making it extremely accurate for complex edits.
    """
    
    name = "apply_patch"
    description = """
Apply a unified diff patch to any file on the system.

FEATURES:
- System-wide access: Patch any file on the disk (absolute or relative paths).
- Advanced editing: Perfect for multi-line changes or complex refactoring.
- Robustness: Uses standard 'patch' utility for precision.

PATCH FORMAT:
```diff
--- filename.txt
+++ filename.txt
@@ -1,3 +1,4 @@
 line 1
-line 2
+line 2 modified
+line 3 added
 line 3
```

IMPORTANT: If the target file is outside the current directory, provide the 'path' parameter or ensure the patch header contains the correct absolute path.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "patch": {"type": "string", "description": "The unified diff content."},
                "path": {"type": "string", "description": "The absolute or relative path to the file to patch (optional)."}
            },
            "required": ["patch"]
        }

    async def execute(self, patch: str, path: Optional[str] = None) -> ToolResult:
        """Apply a diff patch to a file on the system."""
        try:
            # 1. Resolve Path from Patch if not provided
            if not path:
                for line in patch.split('\n'):
                    if line.startswith('--- a/') or line.startswith('+++ b/'):
                        # Typical git diff format
                        path = line[6:]
                        break
                    elif line.startswith('--- ') or line.startswith('+++ '):
                        # Standard diff format
                        path = line[4:].strip()
                        break
            
            if not path:
                return ToolResult(success=False, error="Patch Error: Could not determine target filename from patch header.", content="")
                
            # 2. Normalize path
            full_path = os.path.normpath(path)
            if not os.path.isabs(full_path):
                full_path = os.path.abspath(full_path)
            
            # 3. Create Temporary Patch File
            # We use a temporary file to pipe into the 'patch' command.
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch)
                patch_file = f.name
                
            try:
                # 4. Execute Patch Command
                # --forward avoids applying the same patch twice.
                # --reject-file=- outputs rejects to stdout if something fails.
                cmd = ['patch', '-p1', '--forward', '-i', patch_file]
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(full_path) or '.'
                )
                
                if result.returncode != 0:
                    return ToolResult(
                        success=False, 
                        error=f"Patch Operation Failed: {result.stderr}", 
                        content="",
                        details={"stdout": result.stdout}
                    )
                    
                return ToolResult(
                    success=True, 
                    content=f"Successfully applied the patch to '{path}'.",
                    details={"file": path}
                )
            finally:
                if os.path.exists(patch_file):
                    os.unlink(patch_file)
                    
        except Exception as e:
            return ToolResult(success=False, error=f"Patch Operation Failed: {str(e)}", content="")
