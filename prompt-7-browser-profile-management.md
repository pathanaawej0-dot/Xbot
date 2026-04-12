# Xbot Agent: Browser Profile Management System

## Description

This prompt guides the implementation of a **Browser Profile Management System** for Xbot. This feature enables Xbot to manage isolated browser profiles with persistent storage for cookies, localStorage, session storage, and website login sessions. Each profile maintains its own identity, allowing the agent to operate multiple "browser identities" for different tasks - like having multiple Chrome profiles for different accounts.

---

## Overview

You are building Xbot's **Browser Profile Management System**. This gives your agent the ability to:

1. **Create/Manage Multiple Browser Profiles** - Each profile is an isolated browser identity
2. **Persist Website Sessions** - Logins, cookies, localStorage survive across sessions
3. **Switch Between Profiles** - Use different profiles for different tasks/websites
4. **Control Chrome via CDP (Chrome DevTools Protocol)** - Automate browser actions
5. **Attach to Existing Chrome Sessions** - Use user's already-running Chrome with their profiles

---

## What We're Building

### Core Architecture

```
~/.xbot/
├── browser/
│   ├── profiles.json          # Profile registry
│   ├── default/
│   │   └── user-data/         # Chrome profile data for "default" profile
│   │       ├── Default/
│   │       │   ├── Cookies          # Stored cookies
│   │       │   ├── Local Storage/   # localStorage data
│   │       │   ├── Session Storage/ # sessionStorage data
│   │       │   ├── Preferences      # Chrome settings
│   │       │   └── Login Data       # Saved passwords (if enabled)
│   │       └── Local State          # Profile metadata
│   ├── work/
│   │   └── user-data/         # Isolated profile for work accounts
│   ├── personal/
│   │   └── user-data/         # Isolated profile for personal accounts
│   └── research/
│   │   └── user-data/         # Profile for research/scraping
```

---

## Profile Configuration Schema

```python
# profiles.json structure
{
    "profiles": {
        "default": {
            "cdp_port": 9222,
            "color": "#FF4500",
            "driver": "managed",      # "managed" | "existing-session"
            "attach_only": false,
            "user_data_dir": null,    # null = auto-generate path
            "created_at": "2025-01-15T10:00:00Z",
            "last_used": "2025-01-15T12:30:00Z"
        },
        "work": {
            "cdp_port": 9223,
            "color": "#0066CC",
            "driver": "managed",
            "attach_only": false,
            "user_data_dir": null,
            "created_at": "2025-01-15T10:05:00Z"
        },
        "user-chrome": {
            "driver": "existing-session",
            "user_data_dir": "/Users/username/Library/Application Support/Google/Chrome",
            "attach_only": true,
            "color": "#00AA00",
            "created_at": "2025-01-15T11:00:00Z"
        }
    },
    "default_profile": "default",
    "cdp_port_range_start": 9222,
    "cdp_port_range_end": 9321,    # 100 profiles max
    "headless": false,
    "no_sandbox": false
}
```

---

## Profile Drivers (Modes)

### 1. Managed Profile (`driver: "managed"`)

**WHAT IT IS:**
Xbot launches and manages its own Chrome instance with a dedicated user-data directory.

**BEHAVIOR:**
- Xbot starts Chrome with `--remote-debugging-port=<cdp_port>`
- Profile data stored in `~/.xbot/browser/<profile_name>/user-data/`
- Full isolation - no interference with user's personal Chrome
- All cookies, localStorage, session storage persist
- Xbot can reset/delete the profile entirely

**USE CASES:**
- Automated web scraping
- Testing with isolated sessions
- Multiple account management
- Clean slate for each task

### 2. Existing-Session Profile (`driver: "existing-session"`)

**WHAT IT IS:**
Attach to user's already-running Chrome browser with their existing profile.

**BEHAVIOR:**
- No Chrome launch - just attach via Chrome DevTools MCP
- Uses user's existing Chrome profile (e.g., `~/Library/Application Support/Google/Chrome`)
- Inherits all existing logins, cookies, saved passwords
- Cannot reset/delete profile (read-only attachment)
- User's Chrome stays running independently

**USE CASES:**
- Act on behalf of user in their personal accounts
- Continue work in already-logged-in sessions
- Use saved passwords from user's Chrome
- No separate browser window

---

## Tools to Implement

### Tool 1: `browser_profile_create`

Creates a new isolated browser profile.

```python
class BrowserProfileCreateTool:
    name = "browser_profile_create"
    description = """
    Create a new browser profile with isolated storage.
    
    Each profile maintains its own:
    - Cookies (website login sessions)
    - localStorage (site-specific data)
    - sessionStorage (session data)
    - Cache, history, downloads
    
    USE THIS WHEN:
    - Setting up a new isolated browser identity
    - Creating separate profiles for different accounts
    - Preparing a clean profile for automated tasks
    
    RETURNS:
    - Profile name
    - CDP port assigned
    - User data directory path
    - Profile color (auto-assigned if not specified)
    """
    
    async def execute(
        self,
        name: str,                 # Profile name (lowercase, alphanumeric, hyphens)
        color: str = None,         # Hex color like "#FF4500" (auto-assigned if None)
        driver: str = "managed",   # "managed" or "existing-session"
        user_data_dir: str = None, # Custom path (for existing-session only)
        attach_only: bool = False  # Skip launch, only attach
    ) -> dict:
        # Validate name (lowercase, alphanumeric, hyphens, max 64 chars)
        if not re.match(r'^[a-z0-9][a-z0-9-]*$', name) or len(name) > 64:
            return {"error": "Invalid profile name"}
        
        # Allocate CDP port (9222-9321 range)
        port = allocate_available_port()
        
        # Auto-assign color if not provided
        if not color:
            color = pick_unused_color(existing_profiles)
        
        # Create profile directory for managed profiles
        if driver == "managed":
            user_data_path = f"~/.xbot/browser/{name}/user-data"
            os.makedirs(user_data_path, exist_ok=True)
        
        # Save to profiles.json
        profiles[name] = {
            "cdp_port": port,
            "color": color,
            "driver": driver,
            "user_data_dir": user_data_dir,
            "attach_only": attach_only,
            "created_at": datetime.utcnow().isoformat()
        }
        
        return {
            "success": True,
            "profile": name,
            "cdp_port": port,
            "color": color,
            "driver": driver,
            "user_data_dir": user_data_path,
            "is_remote": False
        }
```

---

### Tool 2: `browser_profile_delete`

Deletes a browser profile and its data.

```python
class BrowserProfileDeleteTool:
    name = "browser_profile_delete"
    description = """
    Delete a browser profile and all its stored data.
    
    WARNING: This permanently removes:
    - All cookies (logins lost)
    - All localStorage data
    - All sessionStorage data
    - Cache and history
    
    CANNOT delete:
    - Default profile (change default first)
    - Existing-session profiles (user's Chrome)
    
    USE THIS WHEN:
    - Cleaning up unused profiles
    - Resetting a profile to factory state
    - Removing test/automation profiles
    """
    
    async def execute(self, name: str) -> dict:
        # Cannot delete default profile
        if name == config["default_profile"]:
            return {"error": "Cannot delete default profile"}
        
        # Cannot delete existing-session profiles
        profile = profiles.get(name)
        if profile["driver"] == "existing-session":
            return {"error": "Cannot delete existing-session profiles"}
        
        # Stop running Chrome if any
        await stop_browser_for_profile(name)
        
        # Move user-data to trash (safely)
        user_data_path = f"~/.xbot/browser/{name}/user-data"
        shutil.move(user_data_path, trash_dir)
        
        # Remove from profiles.json
        del profiles[name]
        
        return {"success": True, "profile": name, "deleted": True}
```

---

### Tool 3: `browser_profile_list`

Lists all available profiles with their status.

```python
class BrowserProfileListTool:
    name = "browser_profile_list"
    description = """
    List all browser profiles with their current status.
    
    Shows for each profile:
    - Name and color
    - CDP port
    - Driver type (managed/existing-session)
    - Whether browser is running
    - Last used timestamp
    
    USE THIS WHEN:
    - Checking available profiles
    - Deciding which profile to use
    - Verifying profile creation
    """
    
    async def execute(self) -> dict:
        result = []
        for name, profile in profiles.items():
            # Check if browser is reachable
            is_running = await check_cdp_reachable(profile["cdp_port"])
            
            result.append({
                "name": name,
                "color": profile["color"],
                "cdp_port": profile.get("cdp_port"),
                "driver": profile["driver"],
                "is_running": is_running,
                "is_default": name == config["default_profile"],
                "last_used": profile.get("last_used")
            })
        
        return {"success": True, "profiles": result}
```

---

### Tool 4: `browser_start`

Launches or attaches to a browser for a profile.

```python
class BrowserStartTool:
    name = "browser_start"
    description = """
    Start Chrome for a specific profile.
    
    For managed profiles:
    - Launches new Chrome instance
    - Uses isolated user-data directory
    - Enables CDP on assigned port
    
    For existing-session profiles:
    - Attaches to user's running Chrome
    - No new browser launched
    
    USE THIS WHEN:
    - Beginning browser automation
    - Opening a profile for the first time
    - After profile was stopped
    """
    
    async def execute(
        self,
        profile: str = None,      # Profile name (default if None)
        headless: bool = False,   # Run headless (no visible window)
        url: str = None           # Open URL on start
    ) -> dict:
        profile_name = profile or config["default_profile"]
        profile_config = profiles[profile_name]
        
        if profile_config["driver"] == "managed":
            # Build Chrome launch args
            args = [
                f"--remote-debugging-port={profile_config['cdp_port']}",
                f"--user-data-dir={profile_config['user_data_dir']}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-sync",
                "--disable-background-networking",
            ]
            
            if headless:
                args.append("--headless=new")
            
            # Launch Chrome process
            process = subprocess.Popen(
                [chrome_path] + args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            # Wait for CDP to be ready
            await wait_for_cdp_ready(profile_config["cdp_port"])
            
            # Connect via Playwright
            browser = await playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{profile_config['cdp_port']}"
            )
            
            if url:
                page = await browser.new_page()
                await page.goto(url)
            
            return {
                "success": True,
                "profile": profile_name,
                "cdp_port": profile_config["cdp_port"],
                "pid": process.pid
            }
        
        else:  # existing-session
            # Attach to user's Chrome via Chrome DevTools MCP
            # (requires user to have Chrome running with remote debugging enabled)
            return {
                "success": True,
                "profile": profile_name,
                "driver": "existing-session",
                "message": "Attached to existing Chrome session"
            }
```

---

### Tool 5: `browser_stop`

Stops the browser for a profile.

```python
class BrowserStopTool:
    name = "browser_stop"
    description = """
    Stop Chrome for a specific profile.
    
    For managed profiles:
    - Sends SIGTERM to Chrome process
    - Waits for graceful shutdown
    - Preserves all profile data (cookies, storage)
    
    For existing-session profiles:
    - Disconnects from Chrome
    - Chrome keeps running (user's browser)
    
    USE THIS WHEN:
    - Done with browser automation
    - Releasing profile resources
    - Before deleting a profile
    """
    
    async def execute(self, profile: str = None) -> dict:
        profile_name = profile or config["default_profile"]
        
        # Disconnect Playwright
        await playwright_connections[profile_name].close()
        
        # Kill Chrome process for managed profiles
        if profiles[profile_name]["driver"] == "managed":
            pid = running_processes[profile_name].pid
            os.kill(pid, signal.SIGTERM)
            await wait_for_process_exit(pid, timeout=5)
        
        return {"success": True, "profile": profile_name}
```

---

### Tool 6: `browser_navigate`

Navigate to URL in a profile's browser.

```python
class BrowserNavigateTool:
    name = "browser_navigate"
    description = """
    Navigate to a URL in the browser.
    
    The navigation happens in the current tab,
    or opens a new tab if no active tab.
    
    USE THIS WHEN:
    - Opening a website
    - Moving between pages
    - Starting automation task
    """
    
    async def execute(
        self,
        url: str,
        profile: str = None,
        new_tab: bool = False,
        timeout_ms: int = 30000
    ) -> dict:
        browser = get_browser_for_profile(profile)
        
        if new_tab:
            page = await browser.new_page()
        else:
            page = await get_active_page(browser)
        
        response = await page.goto(url, timeout=timeout_ms)
        
        return {
            "success": True,
            "url": page.url(),
            "status": response.status if response else None,
            "title": await page.title()
        }
```

---

### Tool 7: `browser_get_cookies`

Get cookies from a profile.

```python
class BrowserGetCookiesTool:
    name = "browser_get_cookies"
    description = """
    Get all cookies stored in a profile.
    
    Returns cookies for specific domain if specified,
    or all cookies if domain is None.
    
    USE THIS WHEN:
    - Checking login status
    - Debugging session issues
    - Extracting auth tokens
    """
    
    async def execute(
        self,
        profile: str = None,
        domain: str = None
    ) -> dict:
        context = get_context_for_profile(profile)
        cookies = await context.cookies()
        
        if domain:
            cookies = [c for c in cookies if domain in c["domain"]]
        
        return {
            "success": True,
            "profile": profile or "default",
            "cookies": cookies,
            "count": len(cookies)
        }
```

---

### Tool 8: `browser_set_cookies`

Set cookies in a profile.

```python
class BrowserSetCookiesTool:
    name = "browser_set_cookies"
    description = """
    Set/add cookies to a profile.
    
    This lets you inject authentication cookies,
    session tokens, or any custom cookies.
    
    USE THIS WHEN:
    - Injecting auth tokens
    - Setting session cookies
    - Testing with specific cookie states
    """
    
    async def execute(
        self,
        cookies: list,   # List of cookie objects
        profile: str = None
    ) -> dict:
        context = get_context_for_profile(profile)
        await context.add_cookies(cookies)
        
        return {
            "success": True,
            "profile": profile or "default",
            "added": len(cookies)
        }
```

---

### Tool 9: `browser_clear_storage`

Clear cookies/storage for a profile.

```python
class BrowserClearStorageTool:
    name = "browser_clear_storage"
    description = """
    Clear cookies, localStorage, or sessionStorage for a profile.
    
    OPTIONS:
    - "cookies" - Clear all cookies (logs out of all sites)
    - "local_storage" - Clear localStorage
    - "session_storage" - Clear sessionStorage
    - "all" - Clear everything
    
    USE THIS WHEN:
    - Logging out of all sites
    - Resetting session state
    - Cleaning up before new task
    """
    
    async def execute(
        self,
        profile: str = None,
        storage_type: str = "all",  # "cookies" | "local_storage" | "session_storage" | "all"
        domain: str = None          # Only clear for specific domain
    ) -> dict:
        context = get_context_for_profile(profile)
        
        if storage_type in ["cookies", "all"]:
            await context.clear_cookies()
        
        if storage_type in ["local_storage", "all"]:
            # Iterate all pages and clear localStorage
            for page in context.pages():
                if domain:
                    await page.evaluate(f"""
                        localStorage.clear();
                    """)
                else:
                    await page.evaluate("localStorage.clear()")
        
        if storage_type in ["session_storage", "all"]:
            for page in context.pages():
                await page.evaluate("sessionStorage.clear()")
        
        return {
            "success": True,
            "profile": profile or "default",
            "cleared": storage_type
        }
```

---

## Chrome Launch Arguments

```python
# Recommended Chrome args for profile isolation
CHROME_ARGS = [
    "--remote-debugging-port={port}",
    "--user-data-dir={user_data_dir}",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-features=Translate,MediaRouter",
    "--disable-session-crashed-bubble",
    "--hide-crash-restore-bubble",
    "--password-store=basic",
]

# Optional args
OPTIONAL_ARGS = {
    "headless": "--headless=new",
    "no_sandbox": "--no-sandbox --disable-setuid-sandbox",
    "linux_container": "--disable-dev-shm-usage",
    "custom_window": "--window-size=1920,1080",
    "disable_infobars": "--disable-infobars",
}
```

---

## Profile Decoration

When creating a managed profile, "decorate" Chrome's Preferences to give it identity:

```python
def decorate_profile(user_data_dir: str, name: str, color: str):
    """Set profile name and color in Chrome's preference files."""
    
    # Parse hex color to Chrome's SkColor int format
    color_int = hex_to_skcolor(color)  # #FF4500 → signed int
    
    # Update Local State
    local_state_path = f"{user_data_dir}/Local State"
    local_state = read_json(local_state_path) or {}
    local_state["profile"]["info_cache"]["Default"]["name"] = name
    local_state["profile"]["info_cache"]["Default"]["profile_color_seed"] = color_int
    write_json(local_state_path, local_state)
    
    # Update Preferences
    prefs_path = f"{user_data_dir}/Default/Preferences"
    prefs = read_json(prefs_path) or {}
    prefs["profile"]["name"] = name
    prefs["autogenerated"]["theme"]["color"] = color_int
    prefs["browser"]["theme"]["user_color2"] = color_int
    write_json(prefs_path, prefs)
```

---

## CDP Connection (Playwright)

```python
import playwright.async_api

async def connect_to_browser(cdp_port: int):
    """Connect Playwright to Chrome via CDP."""
    
    browser = await playwright.chromium.connect_over_cdp(
        f"http://127.0.0.1:{cdp_port}",
        timeout=5000
    )
    
    # Get default context
    context = browser.contexts[0]
    
    # Track console, errors, network
    for page in context.pages():
        setup_page_monitoring(page)
    
    context.on("page", setup_page_monitoring)
    
    return browser, context

def setup_page_monitoring(page):
    """Monitor page events for debugging."""
    page.on("console", lambda msg: log_console(msg))
    page.on("pageerror", lambda err: log_error(err))
    page.on("request", lambda req: log_request(req))
    page.on("response", lambda resp: log_response(resp))
```

---

## Security Considerations

### SSRF Protection

```python
def validate_url_for_navigation(url: str, ssrf_policy: dict):
    """Block navigation to internal/private networks."""
    
    parsed = urlparse(url)
    hostname = parsed.hostname
    
    # Block private networks by default
    if not ssrf_policy.get("allow_private_network"):
        if is_private_ip(hostname):
            raise BlockedNavigationError(f"Blocked private network: {hostname}")
    
    # Check hostname allowlist
    allowed = ssrf_policy.get("allowed_hostnames", [])
    if hostname not in allowed and hostname != "localhost":
        if is_loopback(hostname) and "localhost" not in allowed:
            raise BlockedNavigationError(f"Blocked loopback: {hostname}")
```

### Profile Isolation

```python
# Each profile has separate:
# - user-data directory (no data sharing)
# - CDP port (no connection collision)
# - Process (no memory/process sharing)

# Port range: 9222-9321 (100 profiles max)
# Reserved ports:
#   9222-9229: Gateway/control services
#   9230-9321: Browser profiles

def allocate_port():
    """Find next available port in range."""
    for port in range(PORT_RANGE_START, PORT_RANGE_END):
        if not is_port_in_use(port):
            return port
    raise NoAvailablePortsError()
```

---

## Summary: Profile Storage Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    BROWSER PROFILE LIFECYCLE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. CREATE PROFILE                                               │
│     └─> Allocate CDP port                                        │
│     └─> Create ~/.xbot/browser/<name>/user-data/                 │
│     └─> Register in profiles.json                                │
│     └─> Assign color                                             │
│                                                                  │
│  2. START BROWSER                                                │
│     └─> Launch Chrome with --user-data-dir                       │
│     └─> Chrome creates Default/ profile structure                │
│     └─> Connect via CDP                                          │
│                                                                  │
│  3. USE BROWSER                                                  │
│     ┌──────────────────────────────────────────────┐             │
│     │  Chrome stores data in user-data/Default/:   │             │
│     │  ├── Cookies         → Login sessions        │             │
│     │  ├── Local Storage/  → Site data (persisted) │             │
│     │  ├── Session Storage/→ Session data          │             │
│     │  ├── Login Data      → Saved passwords       │             │
│     │  ├── Cache/          → Cached resources      │             │
│     │  └── History         → Visited URLs          │             │
│     └──────────────────────────────────────────────┘             │
│     └─> All data persists across browser restarts                │
│     └─> Each profile = isolated identity                         │
│                                                                  │
│  4. STOP BROWSER                                                 │
│     └─> Send SIGTERM                                             │
│     └─> Chrome saves all data                                    │
│     └─> All cookies/storage preserved                            │
│                                                                  │
│  5. DELETE PROFILE                                               │
│     └─> Stop browser                                             │
│     └─> Move user-data to trash                                  │
│     └─> Remove from profiles.json                                │
│     └─> Port freed for reuse                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

1. **HIGH**: `browser_profile_create`, `browser_profile_list`, `browser_start`, `browser_stop`
2. **MEDIUM**: `browser_navigate`, `browser_get_cookies`, `browser_set_cookies`
3. **LOW**: `browser_profile_delete`, `browser_clear_storage` (useful but destructive)

---

## Dependencies

```python
# Required packages
playwright        # Browser automation via CDP
asyncio           # Async subprocess management
json              # Profile registry
pathlib           # Path handling
shutil            # Directory operations
signal            # Process termination
psutil            # Port/process checking
```

Install: `pip install playwright psutil`

Playwright browsers: `playwright install chromium`

---

## Quick Start Example

```python
# Create a profile
await browser_profile_create(name="research", color="#FF9900")

# Start browser
await browser_start(profile="research")

# Navigate
await browser_navigate(url="https://example.com", profile="research")

# Login (cookies saved automatically)
await browser_navigate(url="https://example.com/login")
await browser_fill_form(...)  # Login form

# Cookies persist - next session starts logged in
await browser_stop(profile="research")

# Days later...
await browser_start(profile="research")  # Still logged in!
await browser_navigate(url="https://example.com/dashboard")
```

---

This system gives Xbot persistent browser identities with full control over website sessions, cookies, and storage - enabling multi-account automation, web scraping, and authenticated actions across sessions.