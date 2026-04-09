import logging
from typing import Dict, Any, List, Optional
from core.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class ToolExecutor:
    """Central engine for tool registration and limitless execution.
    
    This manager handles the tool lifecycle and exception grouping 
    to ensure the agent receives actionable errors rather than 
    internal crashes.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        
    def register(self, tool: BaseTool):
        """Add a tool to the registry."""
        self.tools[tool.name] = tool
        
    async def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute a tool by its identifier.
        
        This method wraps the entire execution in error handlers, 
        ensuring 'No Invisible Crashes'.
        """
        try:
            # 1. Lookup tool
            tool = self.tools.get(tool_name)
            if not tool:
                return ToolResult.error_result(
                    f"Unrecognized Tool: '{tool_name}'",
                    hint="Check the available tools list (Definition Cache) or verify spelling."
                )
                
            # 2. Execution
            logger.info(f"Executing tool {tool_name} with params {params}")
            result = await tool.execute(**params)
            return result
            
        except Exception as e:
            # Catch-all for tool-specific crashes (The 'No Invisible Crashes' guarantee)
            logger.error(f"Internal Tool Error in '{tool_name}': {str(e)}", exc_info=True)
            return ToolResult.error_result(
                f"Tool Internal Failure: {type(e).__name__}: {str(e)}",
                details={"error_type": type(e).__name__},
                hint="This is an unexpected crash in the tool's backend logic."
            )
            
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return the list of tool specifications for the LLM API."""
        return [tool.to_definition() for tool in self.tools.values()]
