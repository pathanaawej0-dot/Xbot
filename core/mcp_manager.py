import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from core.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

class MCPToolProxy(BaseTool):
    """A proxy tool that routes calls to an MCP server."""
    
    def __init__(self, name: str, description: str, schema: Dict[str, Any], session: ClientSession):
        self.name = name
        self.description = description
        self.schema = schema
        self.session = session

    def get_schema(self) -> Dict[str, Any]:
        return self.schema

    async def execute(self, **kwargs) -> ToolResult:
        try:
            result = await self.session.call_tool(self.name, arguments=kwargs)
            # MCP results can be complex; we extract the text for simplicity in Xbot
            content = []
            for block in result.content:
                if block.type == "text":
                    content.append({"type": "text", "text": block.text})
            
            return ToolResult(content=content, is_error=result.is_error)
        except Exception as e:
            return ToolResult.error_result(f"MCP Tool Execution Error: {str(e)}")

class MCPManager:
    """Manages connections to multiple MCP servers and their tools."""
    
    def __init__(self, config_path: str = "mcp_config.json"):
        self.config_path = config_path
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.exit_stack = AsyncExitStack()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.servers = json.load(f)

    def save_config(self):
        with open(self.config_path, "w") as f:
            json.dump(self.servers, f, indent=4)

    async def connect_server(self, server_id: str) -> List[BaseTool]:
        """Connect to an MCP server and return its tools converted to BaseTools."""
        if server_id not in self.servers:
            raise ValueError(f"Server '{server_id}' not found in config.")

        config = self.servers[server_id]
        transport_type = config.get("type", "stdio")
        
        try:
            if transport_type == "stdio":
                params = StdioServerParameters(
                    command=config["command"],
                    args=config.get("args", []),
                    env={**os.environ, **config.get("env", {})}
                )
                read, write = await self.exit_stack.enter_async_context(stdio_client(params))
            elif transport_type == "sse":
                read, write = await self.exit_stack.enter_async_context(sse_client(config["url"]))
            else:
                raise ValueError(f"Unsupported transport type: {transport_type}")

            session = await self.exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            
            self.sessions[server_id] = session
            
            # Discover tools
            mcp_tools = await session.list_tools()
            proxies = []
            for t in mcp_tools.tools:
                # We prefix tool names to avoid collisions: server_id__tool_name
                proxy = MCPToolProxy(
                    name=f"{server_id}__{t.name}",
                    description=t.description,
                    schema=t.inputSchema,
                    session=session
                )
                proxies.append(proxy)
            
            return proxies
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{server_id}': {e}")
            raise

    async def disconnect_all(self):
        await self.exit_stack.aclose()
        self.sessions.clear()

    def add_server_config(self, server_id: str, config: Dict[str, Any]):
        self.servers[server_id] = config
        self.save_config()
