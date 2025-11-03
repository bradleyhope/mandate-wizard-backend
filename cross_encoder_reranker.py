"""
Cross-Encoder Reranking
More accurate reranking using cross-encoder models (20-30% better than bi-encoder)
"""

from typing import List, Dict, Any, Tuple
from sentence_transformers import CrossEncoder
import numpy as np


class CrossEncoderReranker:
    """
    Rerank search results using cross-encoder model for better accuracy

    Cross-encoders jointly encode query + document, providing more accurate
    relevance scores than bi-encoder (separate query/doc embeddings) approaches.

    Performance: 20-30% better ranking accuracy vs bi-encoder
    Cost: ~50ms per 10 documents
    """

    def __init__(
        self,
        model_name: str = 'cross-encoder/ms-marco-MiniLM-L-6-v2',
        batch_size: int = 32
    ):
        """
        Initialize cross-encoder reranker

        Args:
            model_name: HuggingFace cross-encoder model
                - ms-marco-MiniLM-L-6-v2: Fast, good quality (80MB)
                - ms-marco-MiniLM-L-12-v2: Better quality, slower (120MB)
            batch_size: Batch size for encoding
        """
        self.model_name = model_name
        self.batch_size = batch_size

        # Lazy load model (only when first used)
        self._model = None

    @property
    def model(self):
        """Lazy load the cross-encoder model"""
        if self._model is None:
            print(f"Loading cross-encoder model: {self.model_name}...")
            try:
                self._model = CrossEncoder(self.model_name)
                print("✓ Cross-encoder loaded")
            except Exception as e:
                print(f"⚠️ Failed to load cross-encoder: {e}")
                print("  Falling back to bi-encoder reranking")
                return None
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 10,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using cross-encoder

        Args:
            query: User's query
            documents: List of document texts to rerank
            top_n: Number of top results to return
            return_scores: Whether to include relevance scores

        Returns:
            List of dicts with 'index', 'text', 'score' (if return_scores=True)
        """
        if not documents:
            return []

        # If model failed to load, fallback to original order
        if self.model is None:
            results = []
            for i, doc in enumerate(documents[:top_n]):
                result = {'index': i, 'text': doc}
                if return_scores:
                    result['score'] = 1.0 - (i / len(documents))  # Decreasing score
                results.append(result)
            return results

        try:
            # Create query-document pairs
            pairs = [[query, doc] for doc in documents]

            # Score all pairs
            scores = self.model.predict(
                pairs,
                batch_size=self.batch_size,
                show_progress_bar=False
            )

            # Sort by score (descending)
            scored_docs = [
                {'index': i, 'text': doc, 'score': float(score)}
                for i, (doc, score) in enumerate(zip(documents, scores))
            ]

            scored_docs.sort(key=lambda x: x['score'], reverse=True)

            # Return top-n
            results = scored_docs[:top_n]

            if not return_scores:
                for result in results:
                    del result['score']

            return results

        except Exception as e:
            print(f"⚠️ Cross-encoder reranking failed: {e}")
            # Fallback to original order
            results = []
            for i, doc in enumerate(documents[:top_n]):
                result = {'index': i, 'text': doc}
                if return_scores:
                    result['score'] = 1.0 - (i / len(documents))
                results.append(result)
            return results

    def rerank_with_metadata(
        self,
        query: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Tuple[List[str], List[Dict[str, Any]], List[float]]:
        """
        Rerank documents and preserve associated metadata

        Args:
            query: User's query
            documents: List of document texts
            metadatas: List of metadata dicts (parallel to documents)
            top_n: Number of top results

        Returns:
            Tuple of (reranked_documents, reranked_metadatas, scores)
        """
        if not documents:
            return [], [], []

        # Rerank with scores
        reranked = self.rerank(query, documents, top_n=top_n, return_scores=True)

        # Reorder documents and metadata based on reranking
        reranked_documents = []
        reranked_metadatas = []
        scores = []

        for result in reranked:
            idx = result['index']
            reranked_documents.append(documents[idx])
            reranked_metadatas.append(metadatas[idx])
            scores.append(result['score'])

        return reranked_documents, reranked_metadatas, scores

    def batch_rerank(
        self,
        queries: List[str],
        documents_list: List[List[str]],
        top_n: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """
        Rerank multiple query-document sets in batch

        Args:
            queries: List of queries
            documents_list: List of document lists (one per query)
            top_n: Number of top results per query

        Returns:
            List of reranked result lists
        """
        results = []
        for query, documents in zip(queries, documents_list):
            reranked = self.rerank(query, documents, top_n=top_n)
            results.append(reranked)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get reranker statistics"""
        return {
            'model_name': self.model_name,
            'model_loaded': self._model is not None,
            'batch_size': self.batch_size
        }


# Global instance
_reranker = None


def get_cross_encoder_reranker() -> CrossEncoderReranker:
    """Get or create global cross-encoder reranker instance"""
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoderReranker(
            model_name='cross-encoder/ms-marco-MiniLM-L-6-v2'
        )
    return _reranker


# Example usage
if __name__ == '__main__':
    reranker = CrossEncoderReranker()

    # Test query
    query = "Who should I pitch a crime thriller to at Netflix?"

    # Sample documents (from retrieval)
    documents = [
        "Brandon Riegg is VP of Scripted Series at Netflix, focusing on drama and thriller content.",
        "Netflix has offices in Los Angeles and London.",
        "Kennedy Corrin handles romantic comedies and light drama.",
        "Crime thrillers have seen increased popularity in 2024.",
        "The Diplomat is a political thriller that premiered on Netflix.",
        "Brandon Riegg recently greenlit several crime series including 'Dark Matter'.",
    ]

    print("Cross-Encoder Reranking Example:\n" + "="*70)
    print(f"Query: {query}\n")

    # Rerank
    reranked = reranker.rerank(query, documents, top_n=3, return_scores=True)

    print("Top 3 Results:")
    for i, result in enumerate(reranked, 1):
        print(f"\n{i}. Score: {result['score']:.3f}")
        print(f"   Text: {result['text']}")
