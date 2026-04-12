from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult
from core.tools.browser.manager import browser_manager
from core.tools.browser.profiles import profile_registry

class BrowserOpenTool(BaseTool):
    name = "browser_open"
    description = """
Opens or focuses the browser for a specific profile.
Use this to ensure the browser is running before performing other actions.
Each profile (e.g., 'default', 'work') maintains isolated cookies and logins.
"""
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object", 
            "properties": {
                "profile": {"type": "string", "description": "Profile name (default: 'default')"}
            }
        }

    async def execute(self, profile: str = "default") -> ToolResult:
        try:
            await browser_manager.get_page(profile)
            return ToolResult.text_result(f"Browser opened/focused for profile '{profile}' successfully.")
        except Exception as e:
            return ToolResult.error_result(f"Failed to open browser: {str(e)}")

class BrowserNavigateTool(BaseTool):
    name = "browser_navigate"
    description = "Navigates the browser to a specific URL."
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to navigate to."},
                "profile": {"type": "string", "description": "Profile name (default: 'default')"}
            },
            "required": ["url"]
        }

    async def execute(self, url: str, profile: str = "default") -> ToolResult:
        try:
            page = await browser_manager.get_page(profile)
            await page.goto(url, wait_until="domcontentloaded")
            return ToolResult.text_result(f"Navigated to {url} in profile '{profile}'")
        except Exception as e:
            return ToolResult.error_result(f"Navigation failed: {str(e)}")

class BrowserInteractTool(BaseTool):
    name = "browser_interact"
    description = """
Interacts with the browser page. Supported actions: click, type, press, scroll.
Example actions:
- { "action": "click", "selector": "#login-button" }
- { "action": "type", "selector": "input[name='q']", "text": "Xbot AI" }
- { "action": "press", "key": "Enter" }
- { "action": "scroll", "direction": "down", "amount": 500 }
"""
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["click", "type", "press", "scroll"]},
                "selector": {"type": "string", "description": "CSS selector for the element."},
                "text": {"type": "string", "description": "Text to type (for 'type' action)."},
                "key": {"type": "string", "description": "Key to press (for 'press' action)."},
                "direction": {"type": "string", "enum": ["up", "down"], "description": "Scroll direction."},
                "amount": {"type": "integer", "description": "Amount in pixels to scroll."},
                "profile": {"type": "string", "description": "Profile name (default: 'default')"}
            },
            "required": ["action"]
        }

    async def execute(self, action: str, profile: str = "default", **kwargs) -> ToolResult:
        try:
            page = await browser_manager.get_page(profile)
            if action == "click":
                await page.click(kwargs["selector"])
                return ToolResult.text_result(f"Clicked {kwargs['selector']}")
            elif action == "type":
                await page.fill(kwargs["selector"], kwargs["text"])
                return ToolResult.text_result(f"Typed text into {kwargs['selector']}")
            elif action == "press":
                await page.keyboard.press(kwargs["key"])
                return ToolResult.text_result(f"Pressed key {kwargs['key']}")
            elif action == "scroll":
                amount = kwargs.get("amount", 300)
                if kwargs["direction"] == "down":
                    await page.evaluate(f"window.scrollBy(0, {amount})")
                else:
                    await page.evaluate(f"window.scrollBy(0, -{amount})")
                return ToolResult.text_result(f"Scrolled {kwargs['direction']} by {amount}px")
            return ToolResult.error_result(f"Unknown action: {action}")
        except Exception as e:
            return ToolResult.error_result(f"Interaction failed: {str(e)}")

class BrowserInspectTool(BaseTool):
    name = "browser_inspect"
    description = "Retrieves information about the current page: title, URL, or takes a screenshot."
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mode": {"type": "string", "enum": ["info", "screenshot"], "default": "info"},
                "profile": {"type": "string", "description": "Profile name (default: 'default')"}
            }
        }

    async def execute(self, mode: str = "info", profile: str = "default") -> ToolResult:
        try:
            page = await browser_manager.get_page(profile)
            if mode == "info":
                title = await page.title()
                url = page.url
                return ToolResult.text_result(f"Profile: {profile}\nTitle: {title}\nURL: {url}")
            elif mode == "screenshot":
                path = f"data/screenshot_{profile}.png"
                await page.screenshot(path=path)
                return ToolResult.text_result(f"Screenshot for profile '{profile}' saved to {path}.")
            return ToolResult.error_result(f"Unknown mode: {mode}")
        except Exception as e:
            return ToolResult.error_result(f"Inspection failed: {str(e)}")

class BrowserProfileCreateTool(BaseTool):
    name = "browser_profile_create"
    description = "Create a new isolated browser profile with its own cookies and identity."
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name for the new profile (e.g., 'work', 'research')."},
                "color": {"type": "string", "description": "Hex color code for the profile theme (e.g., '#00AAFF')."}
            },
            "required": ["name"]
        }

    async def execute(self, name: str, color: Optional[str] = None) -> ToolResult:
        try:
            profile = profile_registry.create_profile(name, color=color)
            return ToolResult.text_result(f"Browser profile '{name}' created successfully.\nData Dir: {profile['user_data_dir']}")
        except Exception as e:
            return ToolResult.error_result(f"Failed to create profile: {str(e)}")

class BrowserProfileListTool(BaseTool):
    name = "browser_profile_list"
    description = "List all existing browser profiles and their identity details."
    
    def get_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self) -> ToolResult:
        try:
            profiles = profile_registry.list_profiles()
            result = "Xbot Browser Profiles:\n"
            for name, data in profiles.items():
                result += f"- {name} (Color: {data['color']}, Port: {data['cdp_port']})\n"
            return ToolResult.text_result(result)
        except Exception as e:
            return ToolResult.error_result(f"Failed to list profiles: {str(e)}")
