from __future__ import annotations

def classify(question: str) -> str:
    """
    Lightweight intent classification.
    Returns one of: 'pitch', 'trend', 'person', 'deal', 'comparison', 'general'
    """
    q = question.lower()
    
    if any(w in q for w in ["pitch", "where should i", "who should i pitch"]):
        return "pitch"
    elif any(w in q for w in ["trend", "greenlight", "what's hot", "buying"]):
        return "trend"
    elif any(w in q for w in ["executive", "who is", "person", "profile"]):
        return "person"
    elif any(w in q for w in ["deal", "overall deal", "first-look"]):
        return "deal"
    elif any(w in q for w in ["vs", "versus", "compare", "difference between"]):
        return "comparison"
    else:
        return "general"
