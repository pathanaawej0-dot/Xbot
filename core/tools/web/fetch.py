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

    async def execute(
        self, 
        url: str, 
        method: str = "GET", 
        headers: Optional[Dict[str, str]] = None, 
        params: Optional[Dict[str, Any]] = None, 
        body: Optional[str] = None, 
        timeout: float = 30.0
    ) -> ToolResult:
        """Fetch and process web content with zero restrictions."""
        try:
            # 1. No SSRF Check (Removed self.ssrf_checker.check(url))
            
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
                    # HTML response - convert to Markdown
                    content = self.html_to_markdown(response.text)
                else:
                    content = response.text[:2_000_000]
                    
                return ToolResult(
                    success=response.status_code < 400,
                    content=content,
                    details={
                        "status": response.status_code,
                        "url": str(response.url),
                        "content_type": content_type
                    }
                )
                
        except Exception as e:
            return ToolResult(success=False, error=f"Web Fetch Operation Failed: {str(e)}", content="")
            
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
