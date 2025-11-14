from __future__ import annotations
from typing import List, Dict, Any
from pinecone import Pinecone
from config import S
from rag.embedder import get_embedder

class PineconeRetriever:
    def __init__(self):
        self.pc = Pinecone(api_key=S.PINECONE_API_KEY)
        self.index = self.pc.Index(S.PINECONE_INDEX)
        self.embedder = get_embedder()

    def query(self, text: str, top_k: int = 10, namespace: str = "") -> List[Dict[str, Any]]:
        """Query Pinecone with text and return top-k results.
        
        If namespace is empty, queries multiple relevant namespaces and merges results.
        """
        vec = self.embedder.embed_one(text)
        
        # If specific namespace requested, query only that
        if namespace:
            res = self.index.query(vector=vec, top_k=top_k, include_metadata=True, namespace=namespace)
            return self._format_matches(res.get("matches", []))
        
        # Otherwise, query multiple namespaces and merge
        namespaces_to_query = [
            "",  # default
            "senior_executives",
            "executives",
            "pitch_requirements",
            "production_companies",
            "greenlights",
            "greenlights_2024_2025",
            "packaging_intelligence",
            "competitive_intelligence"
        ]
        
        all_hits = []
        for ns in namespaces_to_query:
            try:
                res = self.index.query(
                    vector=vec,
                    top_k=max(5, top_k // len(namespaces_to_query)),  # Get fewer from each namespace
                    include_metadata=True,
                    namespace=ns
                )
                hits = self._format_matches(res.get("matches", []))
                all_hits.extend(hits)
            except Exception as e:
                # Skip namespaces that error
                continue
        
        # Sort by score and return top_k
        all_hits.sort(key=lambda x: x["score"], reverse=True)
        return all_hits[:top_k]
    
    def _format_matches(self, matches: List) -> List[Dict[str, Any]]:
        """Format Pinecone matches into standard format"""
        hits = []
        for m in matches:
            hits.append({
                "id": m.get("id"),
                "score": m.get("score", 0.0),
                "metadata": m.get("metadata", {})
            })
        return hits
