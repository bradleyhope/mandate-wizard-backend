"""
Semantic Quote Ranker - Phase 2.3
Ranks quotes by semantic similarity to user's question for context-aware selection
"""

from typing import List, Dict, Tuple
from openai import OpenAI
import os
import numpy as np

class SemanticQuoteRanker:
    """Ranks quotes by semantic relevance to user's question"""
    
    def __init__(self):
        """Initialize with OpenAI for embeddings"""
        self.client = OpenAI(api_key=os.getenv('MY_OPENAI_API_KEY'))
        self.embedding_model = "text-embedding-3-small"  # Fast and cheap
        self.cache = {}  # Cache embeddings to save API calls
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text, with caching"""
        # Use first 500 chars as cache key
        cache_key = text[:500]
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            embedding = response.data[0].embedding
            self.cache[cache_key] = embedding
            return embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def rank_quotes(self, question: str, quotes: List[Dict], top_k: int = 2) -> List[Dict]:
        """
        Rank quotes by semantic similarity to question
        
        Args:
            question: User's question
            quotes: List of quote dicts with 'quote', 'context', 'date' fields
            top_k: Number of top quotes to return
        
        Returns:
            Top K quotes ranked by relevance
        """
        if not quotes:
            return []
        
        # Get question embedding
        question_embedding = self.get_embedding(question)
        if not question_embedding:
            # Fallback to most recent quotes
            return sorted(quotes, key=lambda q: q.get('date', ''), reverse=True)[:top_k]
        
        # Calculate similarity for each quote
        scored_quotes = []
        for quote in quotes:
            # Combine quote text and context for better matching
            quote_text = quote.get('quote', '')
            quote_context = quote.get('context', '')
            combined_text = f"{quote_text} {quote_context}"
            
            quote_embedding = self.get_embedding(combined_text)
            if quote_embedding:
                similarity = self.cosine_similarity(question_embedding, quote_embedding)
                scored_quotes.append((similarity, quote))
        
        # Sort by similarity (highest first)
        scored_quotes.sort(key=lambda x: x[0], reverse=True)
        
        # Return top K
        return [quote for _, quote in scored_quotes[:top_k]]

# Global instance
_ranker = None

def get_semantic_ranker() -> SemanticQuoteRanker:
    """Get or create global SemanticQuoteRanker instance"""
    global _ranker
    if _ranker is None:
        _ranker = SemanticQuoteRanker()
    return _ranker

