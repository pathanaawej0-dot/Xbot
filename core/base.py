from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Dict

@dataclass
class ToolResult:
    """Standard return type for all Xbot tools with diagnostic support."""
    content: list[dict]   # [{"type": "text", "text": "..."}]
    details: Optional[Dict[str, Any]] = field(default_factory=dict)
    hint: Optional[str] = None
    is_error: bool = False

    @staticmethod
    def text_result(text: str, details: Optional[Dict[str, Any]] = None, hint: Optional[str] = None) -> 'ToolResult':
        """Helper to create a successful text result."""
        return ToolResult(
            content=[{"type": "text", "text": text}],
            details=details,
            hint=hint,
            is_error=False
        )

    @staticmethod
    def error_result(text: str, details: Optional[Dict[str, Any]] = None, hint: Optional[str] = None) -> 'ToolResult':
        """Helper to create an error result."""
        content = [{"type": "text", "text": text}]
        return ToolResult(
            content=content,
            details=details,
            hint=hint,
            is_error=True
        )

class BaseTool(ABC):
    """Base class for all Xbot tools.
    
    Attributes:
        name (str): The identifier for the tool (e.g., 'exec').
        description (str): Detailed docstring the LLM uses to understand when/how to call it.
        owner_only (bool): If True, only the system owner can execute it.
    """
    name: str = ""
    description: str = ""
    owner_only: bool = False
    
    # General context or tools can be injected here as needed
    # But hard-coded system guards are removed to allow native access.
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool logic asynchronously.
        
        Args:
            **kwargs: Arguments passed by the LLM via tool call.
            
        Returns:
            ToolResult: Structured success/failure and content.
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Returns the JSON Schema for the tool's input parameters.
        Must be implemented by subclasses or derived from type hints.
        """
        raise NotImplementedError("Each tool must define its input schema.")

    def to_definition(self) -> Dict[str, Any]:
        """Convert the tool to the format required by the LLM API."""
        return {
            "name": self.name,
            "description": self.description.strip(),
            "input_schema": self.get_schema()
        }
