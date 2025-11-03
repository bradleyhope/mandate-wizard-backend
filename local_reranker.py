"""
Local Cross-Encoder Re-ranking Module for Mandate Wizard V5
Phase 3.1: Re-ranking Layer (Plan B - Local Implementation)

This module uses a local cross-encoder model for re-ranking search results.
Can be replaced with Cohere later for better performance.
"""

from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
import numpy as np


class LocalReranker:
    """Re-ranks search results using a local cross-encoder model."""
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize local reranker with cross-encoder model.
        
        Args:
            model_name: HuggingFace model name for cross-encoder
                       Default: ms-marco-MiniLM-L-6-v2 (fast, accurate)
                       Alternative: ms-marco-MiniLM-L-12-v2 (slower, more accurate)
        """
        print(f"Loading cross-encoder model: {model_name}...")
        self.model = CrossEncoder(model_name)
        print("✅ Cross-encoder model loaded successfully")
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10,
        return_documents: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents using cross-encoder model.
        
        Args:
            query: The user's question
            documents: List of document texts to rerank
            top_n: Number of top results to return
            return_documents: Whether to return document text in results
        
        Returns:
            List of reranked results with scores and indices
        """
        if not documents:
            return []
        
        try:
            # Create query-document pairs for cross-encoder
            pairs = [[query, doc] for doc in documents]
            
            # Get relevance scores
            scores = self.model.predict(pairs)
            
            # Sort by score (descending)
            ranked_indices = np.argsort(scores)[::-1]
            
            # Return top N results
            results = []
            for idx in ranked_indices[:top_n]:
                results.append({
                    'index': int(idx),
                    'relevance_score': float(scores[idx]),
                    'document': documents[idx] if return_documents else None
                })
            
            return results
            
        except Exception as e:
            print(f"⚠️ Local rerank error: {e}")
            # Fallback: return original order with dummy scores
            return [
                {
                    'index': i,
                    'relevance_score': 1.0 - (i * 0.1),
                    'document': doc if return_documents else None
                }
                for i, doc in enumerate(documents[:top_n])
            ]
    
    def rerank_with_metadata(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        text_key: str = 'text',
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents with metadata preservation.
        
        Args:
            query: The user's question
            documents: List of document dicts with metadata
            text_key: Key in document dict containing text to rank
            top_n: Number of top results to return
        
        Returns:
            List of reranked documents with metadata preserved
        """
        if not documents:
            return []
        
        # Extract texts for ranking
        texts = [doc.get(text_key, '') for doc in documents]
        
        # Get reranked results
        reranked = self.rerank(query, texts, top_n, return_documents=False)
        
        # Map back to original documents with scores
        results = []
        for result in reranked:
            idx = result['index']
            doc = documents[idx].copy()
            doc['relevance_score'] = result['relevance_score']
            results.append(doc)
        
        return results


# Singleton instance
_reranker_instance = None

def get_reranker():
    """Get or create singleton local reranker instance."""
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = LocalReranker()
    return _reranker_instance


# Example usage
if __name__ == "__main__":
    # Test the reranker
    reranker = LocalReranker()
    
    query = "Who handles Korean content at Netflix?"
    documents = [
        "Don Kang is VP of Content for Korea at Netflix.",
        "Brandon Riegg oversees unscripted series including dating shows.",
        "Bela Bajaria is Chief Content Officer at Netflix.",
        "Don Kang focuses on local-first Korean storytelling.",
        "Anne Mensah leads UK content strategy.",
        "Francisco Ramos oversees Latin American content.",
        "Don Kang works with emerging Korean filmmakers."
    ]
    
    results = reranker.rerank(query, documents, top_n=3)
    
    print("\nReranked Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['relevance_score']:.3f}")
        print(f"   {result['document']}\n")

