import os
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult

class EditTool(BaseTool):
    """File Editing Tool for simple string replacements.
    
    This is best for making small, targeted changes.
    """
    
    name = "edit"
    description = """
Find and replace a specific block of text in any file on the system.

FEATURES:
- System-wide access: Edit any file on the disk (absolute or relative paths).
- Precision: Replaces exactly one occurrence of the target text.
- Safety: Fails if the target text is not unique within the file to prevent unintended mass-edits.

IMPORTANT: The 'target' string must be UNIQUE. For complex or multi-line changes, consider 'apply_patch'.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "The absolute or relative path to the file to modify."},
                "target": {"type": "string", "description": "The exact block of text to be replaced."},
                "replacement": {"type": "string", "description": "The new content to insert."}
            },
            "required": ["path", "target", "replacement"]
        }

    async def execute(self, path: str, target: str, replacement: str) -> ToolResult:
        """Edit a file on the system by string replacement with diagnostic support."""
        try:
            # 1. Normalize path
            full_path = os.path.normpath(path)
            
            # 2. Check if file exists
            if not os.path.exists(full_path):
                return ToolResult.error_result(
                    f"File not found: {path}",
                    details={"path": path}
                )
                
            # 3. Read original content
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 4. Check uniqueness
            count = content.count(target)
            if count == 0:
                return ToolResult.error_result(
                    f"Target string not found in '{path}'",
                    details={"path": path, "target_length": len(target)}
                )
            if count > 1:
                return ToolResult.error_result(
                    f"Found {count} occurrences of the target string in '{path}'",
                    details={"path": path, "occurrences": count}
                )
                
            # 5. Replace and Write
            new_content = content.replace(target, replacement)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            return ToolResult.text_result(
                f"Successfully updated '{path}' by replacing the unique target block.",
                details={"file": path, "replaced_count": 1}
            )
            
        except PermissionError:
            return ToolResult.error_result(
                f"Permission denied: {path}",
                details={"path": path}
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Edit Operation Failed: {type(e).__name__}: {str(e)}",
                details={"path": path}
            )
