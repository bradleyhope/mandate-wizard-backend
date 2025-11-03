"""
Cohere Re-ranking Module for Mandate Wizard V5
Phase 3.1: Re-ranking Layer

This module uses Cohere's rerank-english-v3.0 model to re-rank search results
for better context quality before sending to GPT-5.
"""

import cohere
import os
from typing import List, Dict, Any

class CohereReranker:
    """Re-ranks search results using Cohere's rerank API for improved relevance."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize Cohere reranker.
        
        Args:
            api_key: Cohere API key (defaults to COHERE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('COHERE_API_KEY')
        if not self.api_key:
            raise ValueError("COHERE_API_KEY environment variable not set")
        
        self.client = cohere.Client(self.api_key)
        self.model = "rerank-english-v3.0"
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10,
        return_documents: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Re-rank documents using Cohere's rerank API.
        
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
            response = self.client.rerank(
                model=self.model,
                query=query,
                documents=documents,
                top_n=min(top_n, len(documents)),
                return_documents=return_documents
            )
            
            # Convert to list of dicts for easier handling
            results = []
            for result in response.results:
                results.append({
                    'index': result.index,
                    'relevance_score': result.relevance_score,
                    'document': result.document.text if return_documents else None
                })
            
            return results
            
        except Exception as e:
            print(f"⚠️ Cohere rerank error: {e}")
            # Fallback: return original order with dummy scores
            return [
                {
                    'index': i,
                    'relevance_score': 1.0 - (i * 0.1),  # Decreasing scores
                    'document': doc
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


def get_reranker():
    """Get or create singleton Cohere reranker instance."""
    if not hasattr(get_reranker, '_instance'):
        try:
            get_reranker._instance = CohereReranker()
        except ValueError:
            # No API key available, return None
            get_reranker._instance = None
    return get_reranker._instance


# Example usage
if __name__ == "__main__":
    # Test the reranker
    reranker = CohereReranker(api_key="test_key")
    
    query = "Who handles Korean content at Netflix?"
    documents = [
        "Don Kang is VP of Content for Korea at Netflix.",
        "Brandon Riegg oversees unscripted series including dating shows.",
        "Bela Bajaria is Chief Content Officer at Netflix.",
        "Don Kang focuses on local-first Korean storytelling.",
        "Anne Mensah leads UK content strategy."
    ]
    
    results = reranker.rerank(query, documents, top_n=3)
    
    print("Reranked Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['relevance_score']:.3f}")
        print(f"   {result['document']}\n")

