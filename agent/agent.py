import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
from dotenv import load_dotenv

# Import Core System
from core.executor import ToolExecutor
from core.skills.registry import SkillRegistry
from core.prompts import SYSTEM_PROMPT

# Import Tools
from core.tools.shell.exec import ExecTool
from core.tools.shell.process import ProcessTool
from core.tools.filesystem.read import ReadTool
from core.tools.filesystem.write import WriteTool
from core.tools.filesystem.edit import EditTool
from core.tools.filesystem.list import ListTool
from core.tools.filesystem.apply_patch import ApplyPatchTool
from core.tools.web.fetch import WebFetchTool
from core.tools.web.search import WebSearchTool
from core.tools.system.orchestrator import SpawnAgentTool, InstallSkillTool

load_dotenv()

class XbotAgent:
    """Xbot Autonomous Agent powered by Minimax M2.7 and a limitless tool system."""
    
    def __init__(self):
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic")
        self.model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
        
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not found in .env file.")
            
        self.client = Anthropic(api_key=self.api_key, base_url=self.base_url)
        self.messages = []
        
        # 1. Initialize Tool System (No workspace root needed for limitless access)
        self.executor = ToolExecutor()
        
        # 1.1 Initialize Skill System
        self.skill_registry = SkillRegistry(skills_dir="skills")
        
        # 2. Register All Tools
        self.executor.register(ExecTool())
        self.executor.register(ProcessTool(self.executor.tools)) # Share process state
        self.executor.register(ReadTool())
        self.executor.register(WriteTool())
        self.executor.register(EditTool())
        self.executor.register(ListTool())
        self.executor.register(ApplyPatchTool())
        self.executor.register(WebFetchTool())
        self.executor.register(WebSearchTool())
        self.executor.register(SpawnAgentTool())
        self.executor.register(InstallSkillTool())
        
        # 3. Cache Tool Definitions for LLM
        self.tools = self.executor.get_tool_definitions()
        
        # 4. Use Hardcoded System Prompt
        self.base_prompt = SYSTEM_PROMPT

    def get_system_prompt(self) -> str:
        """Constructs the full system prompt by combining base prompt and dynamic skills."""
        skills_xml = self.skill_registry.format_for_prompt()
        return f"{self.base_prompt}\n\n{skills_xml}"

    async def execute_tool(self, name: str, tool_input: Dict[str, Any]) -> list[dict]:
        """Execute a tool and return structured content blocks."""
        result = await self.executor.execute(name, tool_input)
        return result.content

    async def run(self, prompt: str):
        """Standard ReAct loop with raw streaming and structured tool execution."""
        self.messages.append({"role": "user", "content": prompt})
        
        while True:
            print("\n", end="", flush=True)
            
            # Get fully assembled system prompt
            system_prompt = self.get_system_prompt()

            # Using stream for real-time thoughts
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=self.tools,
                messages=self.messages
            ) as stream:
                # Tracking for spacing
                last_block_type = None
                
                for event in stream:
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            if last_block_type in ["thinking", "reasoning"]:
                                print("\n\n", end="", flush=True)
                            
                            print(event.delta.text, end="", flush=True)
                            last_block_type = "text"
                            
                        elif hasattr(event.delta, "thinking"):
                            print(f"\033[90m{event.delta.thinking}\033[0m", end="", flush=True)
                            last_block_type = "thinking"
                            
                        elif hasattr(event.delta, "reasoning"):
                            print(f"\033[90m{event.delta.reasoning}\033[0m", end="", flush=True)
                            last_block_type = "reasoning"
                
                response = stream.get_final_message()
            
            # Update history
            self.messages.append({"role": "assistant", "content": response.content})
            
            # Process tool calls
            tool_use_found = False
            for content_block in response.content:
                if content_block.type == "tool_use":
                    tool_use_found = True
                    tool_name = content_block.name
                    tool_input = content_block.input
                    tool_id = content_block.id
                    
                    print(f"\n\n\033[1;34m[Action: {tool_name}]\033[0m\n\033[90mInput: {tool_input}\033[0m")
                    result_blocks = await self.execute_tool(tool_name, tool_input)
                    
                    # Display result in terminal
                    joined_text = "\n".join([b["text"] for b in result_blocks if b["type"] == "text"])
                    # Simple heuristic: if it looks like an error or rejection, color it.
                    color = "\033[0m" # Default
                    print(f"{color}[Observation]\033[0m\n{joined_text}\n")
                    
                    self.messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_id,
                                "content": result_blocks
                            }
                        ]
                    })
            
            if not tool_use_found or response.stop_reason == "end_turn":
                print("\n")
                break
