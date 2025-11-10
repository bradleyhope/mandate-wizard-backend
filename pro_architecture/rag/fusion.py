from __future__ import annotations
from typing import List, Dict, Any, Callable

def dedup_keep_best(items: List[Dict[str, Any]], key: str = "id") -> List[Dict[str, Any]]:
    """Deduplicate items by key, keeping the one with the highest score."""
    seen: Dict[str, Dict[str, Any]] = {}
    for item in items:
        k = item.get(key)
        if not k:
            continue
        if k not in seen or item.get("score", 0) > seen[k].get("score", 0):
            seen[k] = item
    return list(seen.values())

def mmr(items: List[Dict[str, Any]], lambda_param: float = 0.5, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Maximal Marginal Relevance (MMR) for diversity.
    This is a simplified version that just returns the top-k by score.
    A full implementation would require access to vectors for similarity calculation.
    """
    # Sort by score descending
    sorted_items = sorted(items, key=lambda x: x.get("score", 0), reverse=True)
    return sorted_items[:top_k]
