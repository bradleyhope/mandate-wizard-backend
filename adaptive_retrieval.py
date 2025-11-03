"""
Adaptive Top-K Retrieval
Dynamically adjusts the number of retrieved documents based on query complexity
Simple queries → fewer documents, Complex queries → more documents
"""

import re
from typing import Dict, Any


class AdaptiveRetrieval:
    """
    Intelligently determines optimal top-k for retrieval based on query characteristics

    Factors considered:
    - Query length (words)
    - Query complexity (conjunctions, subclauses)
    - Intent type (factual vs strategic)
    - Specificity (mentions of names, dates, regions)
    """

    def __init__(
        self,
        min_top_k: int = 3,
        max_top_k: int = 20,
        base_top_k: int = 10
    ):
        """
        Initialize adaptive retrieval

        Args:
            min_top_k: Minimum documents to retrieve
            max_top_k: Maximum documents to retrieve
            base_top_k: Default for medium complexity queries
        """
        self.min_top_k = min_top_k
        self.max_top_k = max_top_k
        self.base_top_k = base_top_k

    def compute_top_k(
        self,
        question: str,
        intent: str = 'HYBRID',
        attributes: Dict[str, Any] = None
    ) -> int:
        """
        Compute optimal top-k for a given query

        Args:
            question: User's question
            intent: Query intent
            attributes: Extracted attributes (region, genre, etc.)

        Returns:
            Optimal top-k value
        """
        score = 0

        # 1. Query length score
        words = question.split()
        word_count = len(words)

        if word_count <= 5:
            score += 0  # Short and simple
        elif word_count <= 10:
            score += 2  # Medium length
        elif word_count <= 15:
            score += 4  # Long query
        else:
            score += 6  # Very long, likely complex

        # 2. Complexity indicators
        complexity_patterns = [
            r'\band\b',  # Conjunctions
            r'\bor\b',
            r'\bbut\b',
            r'\bhowever\b',
            r'\balthough\b',
            r'\bwhile\b',
            r'\bwhereas\b',
            r'\bcompare\b',  # Comparison requests
            r'\bversus\b',
            r'\bvs\b',
            r'\bdifference\b',
            r'\bmultiple\b',  # Multiple items
            r'\bseveral\b',
            r'\bmany\b',
            r'\bvarious\b',
        ]

        question_lower = question.lower()
        complexity_count = sum(1 for pattern in complexity_patterns if re.search(pattern, question_lower))
        score += complexity_count * 1.5

        # 3. Intent-based adjustment
        intent_scores = {
            'CLARIFICATION': -3,  # Very simple
            'FACTUAL_QUERY': 0,  # Simple to medium
            'MARKET_INFO': 1,  # Medium
            'ROUTING': 2,  # Medium-complex
            'HYBRID': 3,  # Medium-complex
            'STRATEGIC': 4,  # Complex
            'COMPARATIVE': 5,  # Very complex
            'PROCESS_QUERY': 3,  # Medium-complex
        }
        score += intent_scores.get(intent, 2)

        # 4. Specificity indicators (specific queries need fewer docs)
        if attributes:
            specificity = 0
            if attributes.get('region'):
                specificity += 1
            if attributes.get('genre'):
                specificity += 1
            if attributes.get('format'):
                specificity += 1

            # More specific → need fewer documents
            score -= specificity * 0.5

        # Check for specific names (very specific → fewer docs needed)
        # Names typically have capital letters in middle of sentence
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        if re.search(name_pattern, question):
            score -= 2

        # Check for dates/years (specific → fewer docs)
        date_pattern = r'\b(20\d{2}|19\d{2}|january|february|march|april|may|june|july|august|september|october|november|december)\b'
        if re.search(date_pattern, question_lower):
            score -= 1

        # 5. Question type indicators
        if question_lower.startswith(('who ', 'what ', 'where ')):
            score -= 1  # Direct questions often simpler
        elif question_lower.startswith(('why ', 'how ')):
            score += 1  # Explanatory questions often complex

        # Convert score to top-k
        # Score typically ranges from -5 to 15
        # Map to min_top_k to max_top_k
        normalized_score = max(0, min(20, score + 5))  # Normalize to 0-20

        top_k = int(
            self.min_top_k +
            (self.max_top_k - self.min_top_k) * (normalized_score / 20)
        )

        # Ensure within bounds
        top_k = max(self.min_top_k, min(self.max_top_k, top_k))

        return top_k

    def get_analysis(
        self,
        question: str,
        intent: str = 'HYBRID',
        attributes: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get detailed analysis of why a particular top-k was chosen

        Returns:
            Dict with top_k and reasoning
        """
        top_k = self.compute_top_k(question, intent, attributes)

        # Analyze factors
        words = question.split()
        word_count = len(words)

        complexity_patterns = [r'\band\b', r'\bor\b', r'\bcompare\b', r'\bmultiple\b']
        question_lower = question.lower()
        complexity_count = sum(1 for pattern in complexity_patterns if re.search(pattern, question_lower))

        has_name = bool(re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', question))
        has_date = bool(re.search(r'\b(20\d{2}|19\d{2})\b', question_lower))

        specificity = 0
        if attributes:
            specificity = sum(1 for k in ['region', 'genre', 'format'] if attributes.get(k))

        return {
            'top_k': top_k,
            'reasoning': {
                'word_count': word_count,
                'complexity_indicators': complexity_count,
                'intent': intent,
                'specificity': specificity,
                'has_specific_name': has_name,
                'has_date': has_date,
                'classification': self._classify_complexity(top_k)
            }
        }

    def _classify_complexity(self, top_k: int) -> str:
        """Classify query complexity based on top-k"""
        if top_k <= 5:
            return "Simple"
        elif top_k <= 10:
            return "Medium"
        elif top_k <= 15:
            return "Complex"
        else:
            return "Very Complex"


# Global instance
_adaptive_retrieval = None


def get_adaptive_retrieval() -> AdaptiveRetrieval:
    """Get or create global adaptive retrieval instance"""
    global _adaptive_retrieval
    if _adaptive_retrieval is None:
        _adaptive_retrieval = AdaptiveRetrieval(
            min_top_k=3,
            max_top_k=20,
            base_top_k=10
        )
    return _adaptive_retrieval


# Example usage and testing
if __name__ == '__main__':
    ar = AdaptiveRetrieval()

    test_queries = [
        ("Who is Brandon Riegg?", "FACTUAL_QUERY", {'region': 'US'}),
        ("Tell me about Netflix's strategy in MENA and Asia", "STRATEGIC", {'region': 'mena'}),
        ("Compare Brandon Riegg and Kennedy Corrin's mandates", "COMPARATIVE", {}),
        ("Recent thrillers", "FACTUAL_QUERY", {'genre': 'thriller'}),
        ("Who should I pitch my documentary about climate change in Scandinavia to, and what are the current priorities for documentary content in that region, considering both Netflix Originals and licensed content?", "STRATEGIC", {'region': 'nordics', 'format': 'documentary'}),
    ]

    print("Adaptive Top-K Examples:\n" + "="*70)
    for question, intent, attrs in test_queries:
        analysis = ar.get_analysis(question, intent, attrs)
        print(f"\nQuery: {question[:60]}...")
        print(f"Intent: {intent}")
        print(f"Top-K: {analysis['top_k']} ({analysis['reasoning']['classification']})")
        print(f"Factors: words={analysis['reasoning']['word_count']}, "
              f"complexity={analysis['reasoning']['complexity_indicators']}, "
              f"specificity={analysis['reasoning']['specificity']}")
