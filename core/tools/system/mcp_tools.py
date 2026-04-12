from typing import Dict, Any, List
from core.base import BaseTool, ToolResult
from core.mcp_manager import MCPManager
from core.executor import ToolExecutor

class ConnectMCPTool(BaseTool):
    """Adds or reconnects to an MCP server."""
    name = "connect_mcp"
    description = """
    Connect to a Model Context Protocol (MCP) server to gain new tools.
    You can connect to local servers (stdio) or remote servers (sse).
    
    If the server is not yet configured, provide the full config.
    If it requires an API Key or Code, the connection might fail; use the observation to ask the user.
    """
    
    def __init__(self, mcp_manager: MCPManager, executor: ToolExecutor):
        self.mcp_manager = mcp_manager
        self.executor = executor

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server_id": {"type": "string", "description": "Unique identifier for this server (e.g., 'google-maps')"},
                "transport_type": {"type": "string", "enum": ["stdio", "sse"], "description": "Type of connection"},
                "command": {"type": "string", "description": "Command to run the server (for stdio)"},
                "args": {"type": "array", "items": {"type": "string"}, "description": "Arguments for the command (for stdio)"},
                "url": {"type": "string", "description": "SSE endpoint URL (for sse)"},
                "env": {"type": "object", "description": "Environment variables if needed (e.g., API keys)"}
            },
            "required": ["server_id", "transport_type"]
        }

    async def execute(self, server_id: str, transport_type: str, **kwargs) -> ToolResult:
        try:
            # 1. Update config if provided
            config = {"type": transport_type, **kwargs}
            self.mcp_manager.add_server_config(server_id, config)
            
            # 2. Attempt connection
            proxies = await self.mcp_manager.connect_server(server_id)
            
            # 3. Register discovered tools
            for proxy in proxies:
                self.executor.register(proxy)
            
            tool_names = [p.name for p in proxies]
            return ToolResult.text_result(
                f"Successfully connected to '{server_id}'. Discovered {len(proxies)} tools: {', '.join(tool_names)}.\n"
                f"These tools are now available for use in the next turn."
            )
        except Exception as e:
            return ToolResult.error_result(f"Failed to connect to MCP server '{server_id}': {str(e)}")

class ListMCPTool(BaseTool):
    """Lists all configured and active MCP servers."""
    name = "list_mcp_servers"
    description = "List all MCP servers currently configured and show which ones are active."
    
    def __init__(self, mcp_manager: MCPManager):
        self.mcp_manager = mcp_manager

    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        servers = self.mcp_manager.servers
        active = self.mcp_manager.sessions.keys()
        
        if not servers:
            return ToolResult.text_result("No MCP servers configured.")
            
        lines = ["## MCP Server Configurations:"]
        for sid, config in servers.items():
            status = "🟢 Active" if sid in active else "🔴 Inactive"
            lines.append(f"- **{sid}**: {config.get('type')} ({status})")
            
        return ToolResult.text_result("\n".join(lines))
