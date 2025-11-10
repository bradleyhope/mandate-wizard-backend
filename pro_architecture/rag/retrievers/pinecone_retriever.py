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
        """Query Pinecone with text and return top-k results."""
        vec = self.embedder.embed_one(text)
        res = self.index.query(vector=vec, top_k=top_k, include_metadata=True, namespace=namespace)
        hits = []
        for m in res.get("matches", []):
            hits.append({
                "id": m.get("id"),
                "score": m.get("score", 0.0),
                "metadata": m.get("metadata", {})
            })
        return hits
