"""
MEMORY-OPTIMIZED HybridRAG Query Engine for Mandate Wizard
Key optimizations:
1. Uses OpenAI embeddings API instead of local sentence-transformers (saves ~500MB)
2. Lazy-loads Neo4j persons cache with pagination (saves ~100MB)
3. Removes LangChain dependency (saves ~100MB)
4. Implements strict cache size limits (prevents memory bloat)
"""

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pinecone import Pinecone
from neo4j import GraphDatabase
from embedding_service_optimized import get_embedding_service
from datetime import datetime, timedelta
import hashlib

class HybridRAGEngineOptimized:
    """Memory-optimized hybrid RAG engine using Pinecone and Neo4j"""
    
    def __init__(self, pinecone_api_key: str, pinecone_index_name: str = "netflix-mandate-wizard",
                 neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        """Initialize the hybrid RAG engine"""
        
        print("Initializing Memory-Optimized HybridRAG Engine...")
        
        # Initialize Pinecone
        try:
            self.pc = Pinecone(api_key=pinecone_api_key)
            self.index = self.pc.Index(pinecone_index_name)
            print("✓ Connected to Pinecone")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Pinecone: {e}")
        
        # Initialize Neo4j (optional)
        self.neo4j_driver = None
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    connection_timeout=10,
                    max_connection_lifetime=30
                )
                # Test connection
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                print("✓ Connected to Neo4j")
            except Exception as e:
                print(f"⚠ Neo4j connection failed: {e}")
                self.neo4j_driver = None
        
        # Use lightweight embedding service instead of sentence-transformers
        self.embedding_service = get_embedding_service()
        
        # Initialize OpenAI client for answer generation
        self.llm = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.model_name = "gpt-4o-mini"  # Use mini for cost/speed optimization
        
        # MEMORY OPTIMIZATION: Don't load all persons into memory
        # Instead, query Neo4j on-demand with pagination
        self.persons_cache_enabled = False  # Disabled to save memory
        
        # Strict cache size limits
        self.query_cache = {}
        self.MAX_QUERY_CACHE_SIZE = 100  # Limit to 100 cached queries
        self.CACHE_TTL_SECONDS = 1800  # 30 minutes
        
        print("✓ Memory-Optimized HybridRAG Engine initialized")
        print(f"  Embedding: OpenAI API (no local models)")
        print(f"  LLM: {self.model_name}")
        print(f"  Cache limits: {self.MAX_QUERY_CACHE_SIZE} queries")
    
    def vector_search(self, question: str, top_k: int = 5, namespace: str = None) -> Dict[str, Any]:
        """
        Search Pinecone vector database
        
        Args:
            question: User query
            top_k: Number of results to return
            namespace: Optional namespace filter
        
        Returns:
            Dictionary with matches, metadatas, documents, distances
        """
        try:
            # Generate embedding using OpenAI API (no local model needed)
            query_embedding = self.embedding_service.encode([question])[0]
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=namespace
            )
            
            # Extract results
            matches = results.get('matches', [])
            metadatas = [m.get('metadata', {}) for m in matches]
            documents = [m.get('metadata', {}).get('text', '') for m in matches]
            distances = [m.get('score', 0.0) for m in matches]
            
            return {
                'matches': matches,
                'metadatas': metadatas,
                'documents': documents,
                'distances': distances
            }
            
        except Exception as e:
            print(f"Error in vector search: {e}")
            return {
                'matches': [],
                'metadatas': [],
                'documents': [],
                'distances': []
            }
    
    def graph_search_paginated(self, query_cypher: str, parameters: Dict = None, limit: int = 10) -> List[Dict]:
        """
        MEMORY OPTIMIZATION: Query Neo4j with pagination instead of loading all data
        
        Args:
            query_cypher: Cypher query string
            parameters: Query parameters
            limit: Maximum number of results
        
        Returns:
            List of result dictionaries
        """
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query_cypher, parameters or {})
                records = []
                for i, record in enumerate(result):
                    if i >= limit:
                        break
                    records.append(dict(record))
                return records
        except Exception as e:
            print(f"Error in graph search: {e}")
            return []
    
    def query(self, question: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Main query method - simplified and memory-optimized
        
        Args:
            question: User query
            session_id: Session identifier
        
        Returns:
            Dictionary with answer, sources, confidence, etc.
        """
        # Check cache first
        cache_key = self._get_cache_key(question)
        cached = self._get_cached_result(cache_key)
        if cached:
            return cached
        
        # 1. Vector search
        vector_results = self.vector_search(question, top_k=5)
        
        # 2. Build context from vector results
        context_parts = []
        if vector_results['documents']:
            context_parts.append("=== RELEVANT INFORMATION ===\n")
            for i, (meta, doc) in enumerate(zip(vector_results['metadatas'][:5], vector_results['documents'][:5])):
                entity_type = meta.get('entity_type', 'unknown')
                name = meta.get('name', 'unknown')
                context_parts.append(f"\n[Source {i+1}: {entity_type} - {name}]")
                context_parts.append(doc[:1500])  # Limit to 1500 chars per doc
        
        context = '\n'.join(context_parts)
        
        # 3. Generate answer using OpenAI
        answer = self._generate_answer(question, context)
        
        # 4. Build result
        result = {
            'answer': answer,
            'sources': self._build_sources(vector_results),
            'confidence': self._calculate_confidence(vector_results),
            'context': {
                'vector_count': len(vector_results['documents']),
                'graph_count': 0  # Not using graph search in optimized version
            }
        }
        
        # Cache result
        self._cache_result(cache_key, result)
        
        return result
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate answer using OpenAI (no LangChain needed)"""
        try:
            system_prompt = """You are the Mandate Wizard, an expert on Hollywood TV and film industry intelligence.
            
RULES:
1. Answer directly and concisely
2. Use information from the context provided
3. If context is insufficient, acknowledge limitations
4. Be conversational and helpful
5. Keep answers under 200 words unless more detail is requested"""
            
            response = self.llm.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating answer: {e}")
            return "I apologize, but I encountered an error generating an answer. Please try again."
    
    def _build_sources(self, vector_results: Dict) -> List[Dict]:
        """Build source citations from vector results"""
        sources = []
        for i, meta in enumerate(vector_results['metadatas'][:5]):
            sources.append({
                'id': i + 1,
                'type': meta.get('entity_type', 'unknown'),
                'title': meta.get('name', 'Unknown'),
                'platform': meta.get('platform', ''),
                'metadata': meta
            })
        return sources
    
    def _calculate_confidence(self, vector_results: Dict) -> float:
        """Calculate confidence score based on result quality"""
        if not vector_results['distances']:
            return 0.0
        
        # Average of top 3 scores
        top_scores = vector_results['distances'][:3]
        if top_scores:
            return sum(top_scores) / len(top_scores)
        return 0.0
    
    def _get_cache_key(self, question: str) -> str:
        """Generate cache key from question"""
        normalized = question.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached result if not expired"""
        if cache_key in self.query_cache:
            result, expiry = self.query_cache[cache_key]
            if datetime.now() < expiry:
                return result
            else:
                del self.query_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict):
        """Cache query result with TTL and size limit"""
        # Enforce cache size limit
        if len(self.query_cache) >= self.MAX_QUERY_CACHE_SIZE:
            # Remove oldest entry
            oldest_key = next(iter(self.query_cache))
            del self.query_cache[oldest_key]
        
        expiry = datetime.now() + timedelta(seconds=self.CACHE_TTL_SECONDS)
        self.query_cache[cache_key] = (result, expiry)
    
    def clear_caches(self):
        """Clear all caches to free memory"""
        self.query_cache.clear()
        self.embedding_service.clear_cache()
        print("✓ All caches cleared")
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
