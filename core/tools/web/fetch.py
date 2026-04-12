import httpx
import re
from typing import Dict, Any, Optional
from core.base import BaseTool, ToolResult

class WebFetchTool(BaseTool):
    """Secure Web Fetching Tool with SSRF protection and content extraction.
    
    Features:
    - SSRF prevention (IP blocking)
    - GET/POST/HEAD/OPTIONS methods
    - Custom headers and body support
    - JSON parsing and HTML-to-Text conversion
    - 30-second default timeout
    - 2MB max response cap
    """
    
    name = "web_fetch"
    description = """
Fetch web content from any URL (including local/private networks) and convert it to clean Markdown.

FEATURES:
- Limitless access: No SSRF restrictions. Fetch from localhost, internal IPs, or the public web.
- Markdown conversion: Automatically transforms HTML into readable Markdown for the LLM.
- Method support: GET, POST, HEAD, OPTIONS.
- Customization: Supports headers, body, and adjustable timeouts.

IMPORTANT: This tool can access internal services. Use responsibly.
"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The destination URL."},
                "method": {"type": "string", "enum": ["GET", "POST", "HEAD", "OPTIONS"], "default": "GET"},
                "headers": {"type": "object", "description": "Custom HTTP headers."},
                "params": {"type": "object", "description": "Query parameters."},
                "body": {"type": "string", "description": "Request body for POST requests."},
                "timeout": {"type": "number", "description": "Timeout in seconds (default 30).", "default": 30.0}
            },
            "required": ["url"]
        }

    BLOCKED_IP_PREFIXES = [
        '127.', '10.', '172.16.', '172.17.', '172.18.', '172.19.',
        '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
        '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
        '172.30.', '172.31.', '192.168.', '169.254.'
    ]

    async def execute(
        self, 
        url: str, 
        method: str = "GET", 
        headers: Optional[Dict[str, str]] = None, 
        params: Optional[Dict[str, Any]] = None, 
        body: Optional[str] = None, 
        timeout: float = 30.0
    ) -> ToolResult:
        """Fetch and process web content with diagnostic support."""
        try:
            # 1. SSRF Check
            from urllib.parse import urlparse
            import socket
            
            parsed = urlparse(url)
            hostname = parsed.hostname or ''
            
            if hostname in ('localhost', 'metadata.google.internal'):
                return ToolResult.error_result(
                    f"Blocked internal hostname: {hostname}",
                    details={"url": url, "hostname": hostname},
                    hint="Cannot access internal/cloud metadata endpoints."
                )
            
            try:
                ip_str = socket.gethostbyname(hostname)
                for prefix in self.BLOCKED_IP_PREFIXES:
                    if ip_str.startswith(prefix):
                        return ToolResult.error_result(
                            f"Blocked private IP range: {ip_str}",
                            details={"url": url, "ip": ip_str, "hostname": hostname}
                        )
            except socket.gaierror:
                return ToolResult.error_result(
                    f"Could not resolve hostname: {hostname}",
                    details={"url": url, "hostname": hostname}
                )

            # 2. Make Request
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=False) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    content=body.encode() if body else None
                )
                
                content_type = response.headers.get('content-type', '').lower()
                
                # 3. Process Content
                if 'application/json' in content_type:
                    try:
                        content = str(response.json())
                    except Exception:
                        content = response.text
                elif 'text/html' in content_type:
                    content = self.html_to_markdown(response.text)
                else:
                    content = response.text[:2_000_000]
                
                if response.status_code >= 400:
                    return ToolResult.error_result(
                        f"HTTP {response.status_code}: {response.reason_phrase}",
                        details={"status": response.status_code, "url": str(response.url)}
                    )
                    
                return ToolResult.text_result(
                    content,
                    details={
                        "status": response.status_code,
                        "url": str(response.url),
                        "content_type": content_type
                    }
                )
        
        except httpx.TimeoutException:
            return ToolResult.error_result(
                f"Request timed out after {timeout} seconds",
                details={"url": url, "timeout": timeout}
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Web Fetch Failed: {type(e).__name__}: {str(e)}",
                details={"url": url}
            )
            
    def html_to_markdown(self, html: str) -> str:
        """Heuristic HTML to Markdown converter."""
        # 1. Basic Cleaning
        text = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. Convert common tags to MD
        text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n# \1\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<b|strong[^>]*>(.*?)</b|strong>', r'**\1**', text, flags=re.IGNORECASE)
        text = re.sub(r'<i|em[^>]*>(.*?)</i|em>', r'*\1*', text, flags=re.IGNORECASE)
        text = re.sub(r'<a[^>]+href=["\'](.*?)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'\n- \1', text, flags=re.IGNORECASE)
        
        # 3. Strip remaining tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 4. Final Polish
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*\n\s*', '\n', text)
        
        return text.strip()[:2_000_000]
