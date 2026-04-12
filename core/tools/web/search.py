import os
import httpx
import json
from typing import Dict, Any, Optional, List
from core.base import BaseTool, ToolResult

class WebSearchTool(BaseTool):
    """Web Search Tool using Google Gemini grounding API.
    
    This provides up-to-date, real-time information from the web.
    """
    
    name = "web_search"
    description = """
Search the web using Gemini AI with real-time grounding.

GEMINI WITH GROUNDING:
Unlike regular model data that stops at its training date, this tool 
searches the live internet for every query. This gives you current prices, 
breaking news, and up-to-date documentation.

WHAT IT RETURNS:
- Ranked search results with titles, URLs, and snippets.
- Real-time ground truth for historical or factual questions.

EXAMPLES:
- "latest BTC price" → gets live data.
- "Premier League table today" → gets current standings.
- "Python 3.12 release notes" → gets real docs.

LATENCY AWARENESS:
This tool involves a real-time internet search and LLM grounding. It typically takes 5-10 seconds to complete. 
If you are running this as part of a larger plan, explain to the user that you are "Searching the web..." before calling the tool.
"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        # Use Google GenAI REST API for high-fidelity grounding
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."},
                "num_results": {"type": "integer", "description": "Number of results to return (default 10).", "default": 10}
            },
            "required": ["query"]
        }

    async def execute(self, query: str, num_results: int = 10) -> ToolResult:
        """Execute a grounded search via Gemini with diagnostic support."""
        if not self.api_key:
            return ToolResult.error_result(
                "GOOGLE_API_KEY not found in environment.",
                hint="You must set the 'GOOGLE_API_KEY' in your .env file to enable web search capabilities."
            )
            
        # Internal search prompt
        prompt = f"""Search the live web for: {query}
Return exactly {num_results} search results in this JSON array format:
[
  {{"title": "Result Title", "url": "https://example.com", "snippet": "A brief summary of the result..."}},
  ...
]
Return ONLY the JSON."""

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"},
                        "tools": [{"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "MODE_DYNAMIC", "dynamic_threshold": 0.3}}}]
                    },
                    timeout=30
                )
                
                if response.status_code != 200:
                    return ToolResult.error_result(
                        f"Search Engine Error: Status {response.status_code}",
                        details={"response": response.text},
                        hint="The Google API might be down or your key is quota-limited. Check Google Cloud Console."
                    )
                    
                data = response.json()
                results_json = ""
                
                try:
                    candidates = data.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        for part in parts:
                            if 'text' in part:
                                results_json = part['text']
                                break
                    
                    if not results_json:
                        return ToolResult.error_result("No valid content returned from Gemini.")
                        
                    results = json.loads(results_json)
                    formatted_results = ""
                    for i, res in enumerate(results):
                        formatted_results += f"{i+1}. {res.get('title')}\n   URL: {res.get('url')}\n   Snippet: {res.get('snippet')}\n\n"
                    
                    return ToolResult.text_result(
                        formatted_results if formatted_results else "(No results found)",
                        details={"query": query, "count": len(results)}
                    )
                    
                except Exception as parse_err:
                    return ToolResult.error_result(
                        f"Search Parsing Error: {str(parse_err)}",
                        details={"raw_response": results_json}
                    )
                    
        except httpx.TimeoutException:
            return ToolResult.error_result(
                "Search request timed out"
            )
        except Exception as e:
            return ToolResult.error_result(f"Web Search Operation Failed: {type(e).__name__}: {str(e)}")
