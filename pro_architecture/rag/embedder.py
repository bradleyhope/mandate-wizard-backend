from __future__ import annotations
import hashlib, time
from typing import List, Dict, Tuple
from config import S

# Hosted (OpenAI) embedder
class OpenAIEmbedder:
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=S.OPENAI_API_KEY)
        self.model = S.EMBEDDING_MODEL
        self.cache: Dict[str, Tuple[float, list[float]]] = {}

    def _key(self, text: str) -> str:
        return hashlib.sha1((self.model + "|" + text).encode("utf-8")).hexdigest()

    def _cached(self, k: str, now: float):
        hit = self.cache.get(k)
        if not hit: return None
        ts, vec = hit
        if now - ts > S.EMBED_CACHE_TTL:
            self.cache.pop(k, None); return None
        return vec

    def _evict(self):
        if len(self.cache) <= S.EMBED_CACHE_MAX: return
        items = sorted(self.cache.items(), key=lambda kv: kv[1][0]); cut = max(1, len(items)//10)
        for k,_ in items[:cut]: self.cache.pop(k, None)

    def embed(self, texts: List[str]) -> List[List[float]]:
        out, now = [], time.time()
        for t in texts:
            k = self._key(t[:8000])
            vec = self._cached(k, now)
            if vec is None:
                r = self.client.embeddings.create(model=self.model, input=t[:8000])
                vec = r.data[0].embedding
                self.cache[k] = (now, vec); self._evict()
            out.append(vec)
        return out

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]

_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        if S.EMBEDDER == "openai":
            _embedder = OpenAIEmbedder()
        else:
            raise ValueError(f"Unknown EMBEDDER: {S.EMBEDDER}")
    return _embedder
