"""
Web search skill using DuckDuckGo.
"""

from typing import Dict, Any, List
from .base import Skill

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False


class WebSearchSkill(Skill):
    """Web search using DuckDuckGo (no API key required)"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web using DuckDuckGo",
            capabilities=["network"]
        )
        
        if not DDGS_AVAILABLE:
            raise ImportError(
                "duckduckgo-search not installed. "
                "Install with: pip install duckduckgo-search"
            )
    
    def execute(self, query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        """
        Search the web.
        
        Args:
            query: Search query
            max_results: Maximum number of results (default: 5)
            
        Returns:
            Dict with success, results, and optional error
        """
        params = {"query": query, "max_results": max_results}
        
        try:
            # Perform search
            results = self._search(query, max_results)
            
            result = {
                "success": True,
                "result": results,
                "query": query,
                "count": len(results)
            }
            
        except Exception as e:
            result = {
                "success": False,
                "result": None,
                "error": str(e)
            }
        
        # Log execution
        self.log_execution(params, result)
        
        return result
    
    def _search(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Perform DuckDuckGo search"""
        
        results = []
        
        try:
            with DDGS() as ddgs:
                search_results = ddgs.text(query, max_results=max_results)
                
                for item in search_results:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("href", ""),
                        "snippet": item.get("body", "")
                    })
        
        except Exception as e:
            # If DDGS fails, return empty (don't crash)
            print(f"Search error: {e}")
        
        return results
    
    def format_results(self, results: List[Dict[str, str]]) -> str:
        """
        Format search results as readable text.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted string
        """
        if not results:
            return "No results found."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(f"{i}. {result['title']}")
            formatted.append(f"   {result['url']}")
            formatted.append(f"   {result['snippet'][:150]}...")
            formatted.append("")
        
        return "\n".join(formatted)


class MockWebSearchSkill(Skill):
    """Mock search skill for testing (when duckduckgo-search not available)"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Mock web search (for testing)",
            capabilities=["network"]
        )
    
    def execute(self, query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        """Return mock results"""
        
        results = [
            {
                "title": f"Mock result for: {query}",
                "url": "https://example.com",
                "snippet": "This is a mock search result for testing."
            }
        ]
        
        return {
            "success": True,
            "result": results,
            "query": query,
            "count": len(results)
        }
