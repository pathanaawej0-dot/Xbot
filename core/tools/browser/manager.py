import os
import json
import shutil
import logging
import subprocess
import time
import socket
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright
from .profiles import profile_registry

logger = logging.getLogger(__name__)

class BrowserManager:
    _instance = None
    _playwright: Playwright = None
    _contexts: dict[str, BrowserContext] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
        return cls._instance

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserManager()
        return cls._instance


    def _get_chrome_path(self):
        """Locates Chrome executable."""
        path = os.getenv("CHROME_EXECUTABLE_PATH")
        if path and os.path.exists(path):
            return path

        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        
        for p in paths:
            if os.path.exists(p):
                return p
        return shutil.which("chrome") or shutil.which("google-chrome")

    async def get_context(self, profile_name: str = "Xbot") -> BrowserContext:
        """Starts playwright and returns a persistent context for the specified profile."""
        if profile_name in self._contexts:
            return self._contexts[profile_name]

        if not self._playwright:
            self._playwright = await async_playwright().start()

        profile = profile_registry.get_profile(profile_name)
        if not profile:
            profile = profile_registry.create_profile(profile_name)

        user_data_dir = profile["user_data_dir"]
        os.makedirs(user_data_dir, exist_ok=True)

        chrome_path = self._get_chrome_path()
        headless = os.getenv("BROWSER_HEADLESS", "False").lower() == "true"

        launch_kwargs = {
            "user_data_dir": user_data_dir,
            "headless": headless,
            "args": [f"--remote-debugging-port={profile['cdp_port']}"],
        }

        if chrome_path:
            launch_kwargs["executable_path"] = chrome_path

        try:
            context = await self._playwright.chromium.launch_persistent_context(**launch_kwargs)
            self._contexts[profile_name] = context
            return context
        except Exception as e:
            logger.error(f"Failed to launch browser context for profile '{profile_name}': {e}")
            raise

    async def get_page(self, profile_name: str = "Xbot") -> Page:
        """Returns the current page or creates a new one for the profile."""
        ctx = await self.get_context(profile_name)
        
        if not ctx.pages:
            page = await ctx.new_page()
        else:
            page = ctx.pages[0]
            
        return page

    async def close(self, profile_name: str = None):
        """Closes a specific profile context or all of them."""
        if profile_name:
            if profile_name in self._contexts:
                await self._contexts[profile_name].close()
                del self._contexts[profile_name]
        else:
            for name in list(self._contexts.keys()):
                await self._contexts[name].close()
                del self._contexts[name]
                
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None

browser_manager = BrowserManager()
