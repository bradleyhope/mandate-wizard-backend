"""
Memory-Optimized Embedding Service for Mandate Wizard
Uses OpenAI API instead of local sentence-transformers to save ~500MB RAM
"""

import os
from typing import List
from openai import OpenAI
import hashlib
import json

class EmbeddingService:
    """
    Lightweight embedding service using OpenAI API
    Replaces sentence-transformers to save ~500MB RAM
    """
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.model = "text-embedding-3-small"  # Cheaper and faster than ada-002
        
        # Simple in-memory cache (limited size to prevent memory bloat)
        self.cache = {}
        self.max_cache_size = 1000  # Limit cache to 1000 embeddings
        
        print(f"✓ Embedding service initialized (using OpenAI {self.model})")
    
    def encode(self, texts: List[str], show_progress_bar: bool = False) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        Compatible with sentence-transformers API
        
        Args:
            texts: List of text strings to embed
            show_progress_bar: Ignored (kept for API compatibility)
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Convert single string to list
        if isinstance(texts, str):
            texts = [texts]
        
        embeddings = []
        
        for text in texts:
            # Check cache first
            cache_key = self._get_cache_key(text)
            
            if cache_key in self.cache:
                embeddings.append(self.cache[cache_key])
                continue
            
            # Generate embedding via OpenAI API
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text[:8000]  # Limit to 8000 chars to avoid token limits
                )
                
                embedding = response.data[0].embedding
                
                # Cache the result (with size limit)
                if len(self.cache) < self.max_cache_size:
                    self.cache[cache_key] = embedding
                
                embeddings.append(embedding)
                
            except Exception as e:
                print(f"Error generating embedding: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 1536)  # text-embedding-3-small is 1536 dimensions
        
        return embeddings
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear the embedding cache to free memory"""
        self.cache.clear()
        print("✓ Embedding cache cleared")


# Singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """Get or create the singleton embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
