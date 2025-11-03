"""
HyDE (Hypothetical Document Embeddings)
Generate hypothetical answers and use them for retrieval
Often finds better results than embedding the question directly
"""

from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer


class HyDERetrieval:
    """
    Hypothetical Document Embeddings (HyDE) for improved retrieval

    How it works:
    1. Generate a hypothetical answer to the user's question
    2. Embed the hypothetical answer (not the question)
    3. Use this embedding to search for similar real documents
    4. Real documents often match hypothetical answers better than questions

    Example:
    Question: "Who handles crime thrillers at Netflix?"
    Hypothetical: "Brandon Riegg, VP of Scripted Series, handles crime thriller content at Netflix..."
    → Embedding this finds documents mentioning Brandon Riegg and crime content

    Performance: 10-20% better retrieval accuracy vs embedding questions directly
    """

    def __init__(
        self,
        embedding_model: SentenceTransformer = None,
        llm_client = None
    ):
        """
        Initialize HyDE retrieval

        Args:
            embedding_model: SentenceTransformer for embeddings
            llm_client: LLM client for generating hypothetical documents
        """
        self.embedding_model = embedding_model or SentenceTransformer('all-MiniLM-L6-v2')
        self.llm_client = llm_client

        # Cache for generated hypothetical documents
        self.cache = {}
        self.cache_max_size = 100

    def generate_hypothetical_document(
        self,
        question: str,
        intent: str = 'HYBRID',
        domain_context: str = 'film industry'
    ) -> str:
        """
        Generate a hypothetical answer to the question

        Args:
            question: User's question
            intent: Query intent
            domain_context: Domain for context

        Returns:
            Hypothetical document text
        """
        # Check cache
        cache_key = question.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]

        # If no LLM client, generate simple hypothetical
        if not self.llm_client:
            return self._generate_simple_hypothetical(question, intent)

        # Generate using LLM (fast tier for speed)
        try:
            prompt = f"""Generate a brief, factual answer to this {domain_context} question. Be specific and mention relevant names, titles, and details that would appear in real documents.

Question: {question}

Answer (2-3 sentences, factual tone):"""

            hypothetical = self.llm_client.create(
                prompt=prompt,
                intent='CLARIFICATION',  # Use fast tier
                temperature=0.3,  # Low temperature for factual
                max_tokens=150
            )

            # Cache the result
            if len(self.cache) >= self.cache_max_size:
                # Remove oldest entry
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = hypothetical

            return hypothetical

        except Exception as e:
            print(f"[WARNING] HyDE generation failed: {e}, using simple fallback")
            return self._generate_simple_hypothetical(question, intent)

    def _generate_simple_hypothetical(
        self,
        question: str,
        intent: str
    ) -> str:
        """
        Generate simple hypothetical without LLM (fallback)

        Uses template-based generation
        """
        question_lower = question.lower()

        # Template-based hypotheticals by intent
        if intent == 'ROUTING' or 'who should i pitch' in question_lower:
            # Extract key terms
            terms = []
            if 'documentary' in question_lower or 'doc' in question_lower:
                terms.append('documentary content')
            if 'thriller' in question_lower:
                terms.append('thriller')
            if 'crime' in question_lower:
                terms.append('crime')
            if 'comedy' in question_lower or 'rom-com' in question_lower:
                terms.append('comedy')

            content_type = ' and '.join(terms) if terms else 'content'

            return f"The executive responsible for {content_type} at Netflix has a mandate focusing on high-quality productions. Recent greenlights include several successful projects in this genre."

        elif intent == 'STRATEGIC' or 'mandate' in question_lower:
            return "The current mandate prioritizes premium content with strong creative talent attached. Recent strategic focus includes international expansion and diverse storytelling."

        elif intent == 'FACTUAL_QUERY' or 'recent' in question_lower or 'latest' in question_lower:
            return "Recent greenlights include multiple projects across various genres. The year 2024 has seen increased investment in international content and limited series formats."

        else:
            # Generic hypothetical
            return f"This relates to Netflix's content strategy and executive priorities. Key factors include genre preferences, regional focus, and current industry trends."

    def hyde_embed(self, question: str, intent: str = 'HYBRID') -> List[float]:
        """
        Generate HyDE embedding for a question

        Args:
            question: User's question
            intent: Query intent

        Returns:
            Embedding vector
        """
        # Generate hypothetical document
        hypothetical = self.generate_hypothetical_document(question, intent)

        # Embed the hypothetical (not the question)
        embedding = self.embedding_model.encode(hypothetical)

        return embedding.tolist()

    def hyde_search(
        self,
        question: str,
        documents: List[str],
        intent: str = 'HYBRID',
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents using HyDE

        Args:
            question: User's question
            documents: List of documents to search
            intent: Query intent
            top_k: Number of top results

        Returns:
            List of top-k results with scores
        """
        # Generate HyDE embedding
        query_embedding = self.hyde_embed(question, intent)

        # Embed all documents
        doc_embeddings = self.embedding_model.encode(documents)

        # Compute cosine similarity
        from numpy import dot
        from numpy.linalg import norm

        similarities = []
        for i, doc_emb in enumerate(doc_embeddings):
            similarity = dot(query_embedding, doc_emb) / (norm(query_embedding) * norm(doc_emb))
            similarities.append({
                'index': i,
                'document': documents[i],
                'score': float(similarity)
            })

        # Sort by similarity
        similarities.sort(key=lambda x: x['score'], reverse=True)

        return similarities[:top_k]

    def compare_hyde_vs_direct(
        self,
        question: str,
        documents: List[str],
        intent: str = 'HYBRID',
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Compare HyDE vs direct question embedding

        Returns:
            Dict with both approaches and performance comparison
        """
        # HyDE approach
        hyde_results = self.hyde_search(question, documents, intent, top_k)

        # Direct approach
        question_embedding = self.embedding_model.encode(question)
        doc_embeddings = self.embedding_model.encode(documents)

        from numpy import dot
        from numpy.linalg import norm

        direct_results = []
        for i, doc_emb in enumerate(doc_embeddings):
            similarity = dot(question_embedding, doc_emb) / (norm(question_embedding) * norm(doc_emb))
            direct_results.append({
                'index': i,
                'document': documents[i],
                'score': float(similarity)
            })

        direct_results.sort(key=lambda x: x['score'], reverse=True)
        direct_results = direct_results[:top_k]

        return {
            'question': question,
            'hypothetical_document': self.generate_hypothetical_document(question, intent),
            'hyde_results': hyde_results,
            'direct_results': direct_results,
            'top_1_same': hyde_results[0]['index'] == direct_results[0]['index'] if hyde_results and direct_results else False,
            'top_3_overlap': len(set(r['index'] for r in hyde_results[:3]) & set(r['index'] for r in direct_results[:3]))
        }

    def clear_cache(self):
        """Clear hypothetical document cache"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get HyDE statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_max_size': self.cache_max_size,
            'has_llm': self.llm_client is not None
        }


# Global instance
_hyde_retrieval = None


def get_hyde_retrieval(llm_client=None) -> HyDERetrieval:
    """Get or create global HyDE retrieval instance"""
    global _hyde_retrieval
    if _hyde_retrieval is None:
        _hyde_retrieval = HyDERetrieval(llm_client=llm_client)
    return _hyde_retrieval


# Example usage
if __name__ == '__main__':
    # Test without LLM (template-based)
    hyde = HyDERetrieval()

    test_questions = [
        ("Who should I pitch a crime thriller to?", "ROUTING"),
        ("What are recent Netflix mandates for documentary content?", "STRATEGIC"),
        ("Latest sci-fi series greenlights", "FACTUAL_QUERY"),
    ]

    print("HyDE Examples (Template-Based):\n" + "="*70)
    for question, intent in test_questions:
        print(f"\nQuestion: {question}")
        print(f"Intent: {intent}")

        hypothetical = hyde.generate_hypothetical_document(question, intent)
        print(f"Hypothetical: {hypothetical}")
