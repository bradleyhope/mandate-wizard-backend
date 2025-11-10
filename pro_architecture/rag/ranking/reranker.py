from __future__ import annotations
from typing import List, Dict, Any, Optional
from config import S

class CohereReranker:
    def __init__(self):
        import cohere
        self.client = cohere.Client(S.COHERE_API_KEY)

    def rerank(self, query: str, texts: List[str], top_n: int = 10) -> List[Dict[str, Any]]:
        """Rerank texts using Cohere Rerank API."""
        if not texts:
            return []
        response = self.client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=texts,
            top_n=min(top_n, len(texts))
        )
        return [{"index": r.index, "score": r.relevance_score} for r in response.results]

_reranker: Optional[Any] = None

def get_reranker():
    global _reranker
    if _reranker is None:
        if S.RERANKER == "cohere":
            _reranker = CohereReranker()
        elif S.RERANKER == "none":
            _reranker = None
        else:
            raise ValueError(f"Unknown RERANKER: {S.RERANKER}")
    return _reranker
