import os
import json
import socket
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

XBOT_HOME = Path.home() / ".xbot"
BROWSER_DIR = XBOT_HOME / "browser"
PROFILES_FILE = BROWSER_DIR / "profiles.json"

class ProfileManager:
    def __init__(self):
        BROWSER_DIR.mkdir(parents=True, exist_ok=True)
        self.profiles = self._load_profiles()

    def _load_profiles(self):
        if PROFILES_FILE.exists():
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load profiles: {e}")
        
        # Default registry structure
        default_registry = {
            "profiles": {
                "default": {
                    "cdp_port": 9222,
                    "color": "#FF4500",
                    "driver": "managed",
                    "user_data_dir": str(BROWSER_DIR / "default" / "user-data"),
                    "created_at": datetime.utcnow().isoformat()
                }
            },
            "default_profile": "default",
            "cdp_port_range_start": 9222,
            "cdp_port_range_end": 9321
        }
        self._save_profiles(default_registry)
        return default_registry

    def _save_profiles(self, registry=None):
        if registry:
            self.profiles = registry
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")

    def get_profile(self, name):
        return self.profiles["profiles"].get(name)

    def list_profiles(self):
        return self.profiles["profiles"]

    def create_profile(self, name, color=None, driver="managed"):
        if name in self.profiles["profiles"]:
            return self.profiles["profiles"][name]

        port = self._allocate_port()
        user_data_dir = str(BROWSER_DIR / name / "user-data")
        
        profile = {
            "cdp_port": port,
            "color": color or "#FF4500",
            "driver": driver,
            "user_data_dir": user_data_dir,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.profiles["profiles"][name] = profile
        self._save_profiles()
        return profile

    def _allocate_port(self):
        start = self.profiles["cdp_port_range_start"]
        end = self.profiles["cdp_port_range_end"]
        
        used_ports = {p["cdp_port"] for p in self.profiles["profiles"].values()}
        
        for port in range(start, end):
            if port not in used_ports and self._is_port_free(port):
                return port
        return start # Fallback

    def _is_port_free(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) != 0

profile_registry = ProfileManager()
