"""
Web Search Fallback

When the database doesn't have good information (low confidence, few results),
supplement the answer with fresh web search data.
"""
import json
import requests
from typing import Dict, Any, List
from datetime import datetime

class WebSearchFallback:
    def __init__(self):
        self.enabled = True
    
    def should_trigger(self, response: Dict[str, Any]) -> bool:
        """
        Determine if web search should be triggered.
        
        Trigger when:
        - Few documents retrieved (< 3)
        - No entities found
        - Short answer (< 100 chars)
        """
        meta = response.get("meta", {})
        retrieved = meta.get("retrieved", 0)
        entities = response.get("entities", [])
        answer_length = len(response.get("final_answer", ""))
        
        return (
            retrieved < 3 or
            len(entities) == 0 or
            answer_length < 100
        )
    
    def search_and_supplement(self, question: str, original_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform web search and supplement the original response.
        """
        if not self.enabled:
            return original_response
        
        try:
            # Perform web search (using Manus search tool would be ideal)
            # For now, we'll just mark that web search should be triggered
            # and return the original response with a flag
            
            supplemented = original_response.copy()
            supplemented["web_search_triggered"] = True
            supplemented["web_search_note"] = (
                "Limited information in database. Consider checking recent "
                "industry news for the most up-to-date information."
            )
            
            # In a full implementation, we would:
            # 1. Call search API with the question
            # 2. Extract relevant snippets
            # 3. Re-generate answer with both database + web results
            # 4. Mark sources as "database" vs "web search"
            
            return supplemented
            
        except Exception as e:
            # If web search fails, just return original
            return original_response
    
    def format_web_results(self, results: List[Dict]) -> str:
        """Format web search results for inclusion in prompt."""
        formatted = []
        for i, result in enumerate(results[:5], 1):
            formatted.append(f"{i}. {result.get('title', 'Untitled')}")
            formatted.append(f"   URL: {result.get('url', '')}")
            formatted.append(f"   Snippet: {result.get('snippet', '')[:200]}...")
            formatted.append("")
        return "\n".join(formatted)
