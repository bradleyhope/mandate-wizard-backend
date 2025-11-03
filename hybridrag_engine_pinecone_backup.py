"""
HybridRAG Query Engine V3 for Netflix Mandate Wizard (Pinecone + Neo4j)
Queries entities directly from Pinecone vector database and Neo4j graph database
"""

import json
import os
from typing import List, Dict, Any
from openai import OpenAI
from pinecone import Pinecone
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

class HybridRAGEnginePinecone:
    """Hybrid RAG engine using Pinecone vector database and Neo4j graph database"""
    
    def __init__(self, pinecone_api_key: str, pinecone_index_name: str = "netflix-mandate-wizard",
                 neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        """Initialize the hybrid RAG engine with Pinecone and Neo4j"""
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(pinecone_index_name)
        
        # Initialize Neo4j (optional)
        self.neo4j_driver = None
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                print("✓ Connected to Neo4j")
            except Exception as e:
                print(f"⚠ Neo4j connection failed: {e}")
                print("  Continuing with Pinecone only...")
        
        # Initialize embedding model (same as used for Pinecone)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize OpenAI
        self.llm = OpenAI()
        
        # Get Pinecone stats
        stats = self.index.describe_index_stats()
        
        print(f"✓ HybridRAG V3 (Pinecone + Neo4j) initialized")
        print(f"✓ Vector DB: {stats['total_vector_count']} vectors in Pinecone")
        
        # Cache for person entities from Neo4j
        self.persons_cache = []
        self.persons_by_region = {}
        self.persons_by_genre = {}
        self.persons_by_format = {}
        
        # Load persons from Neo4j if available
        if self.neo4j_driver:
            self._load_persons_from_neo4j()
    
    def _load_persons_from_neo4j(self):
        """Load all person entities from Neo4j and build indexes"""
        try:
            with self.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (p:Person)
                    RETURN p.entity_id as entity_id,
                           p.name as name,
                           p.current_title as current_title,
                           p.region as region,
                           p.bio as bio,
                           p.mandate as mandate,
                           p.recent_projects as recent_projects,
                           p.reports_to as reports_to
                """)
                
                for record in result:
                    person = {
                        'entity_id': record['entity_id'],
                        'entity_type': 'person',
                        'name': record['name'],
                        'current_title': record['current_title'],
                        'region': record['region'],
                        'bio': record['bio'],
                        'mandate': record['mandate'],
                        'recent_projects': record['recent_projects'],
                        'reports_to': record['reports_to'],
                        'genres': [],  # Will be populated from vector search if needed
                        'formats': []
                    }
                    self.persons_cache.append(person)
                    
                    # Index by region
                    region = person.get('region', 'global')
                    if region:
                        region = region.lower()
                        if region not in self.persons_by_region:
                            self.persons_by_region[region] = []
                        self.persons_by_region[region].append(person)
                
                print(f"✓ Loaded {len(self.persons_cache)} persons from Neo4j")
                print(f"✓ Indexed: {len(self.persons_by_region)} regions")
                
        except Exception as e:
            print(f"⚠ Failed to load persons from Neo4j: {e}")
    
    def classify_intent(self, question: str) -> str:
        """Classify the user's intent"""
        question_lower = question.lower()
        
        # ROUTING: Who to pitch to (must check FIRST before STRATEGIC)
        if any(word in question_lower for word in ['who do i pitch', 'who should i pitch', 'who handles', 'who to contact', 'who to pitch', 'who is on', 'who are on']):
            return 'ROUTING'
        
        # STRATEGIC: What they want (including mandate queries)
        if any(word in question_lower for word in ['what kind', 'what does', 'what is', 'looking for', 'want', 'strategy', 'mandate', 'recent mandate', 'priority', 'priorities']):
            # But if it's asking "what should i do" with a project description, it's ROUTING
            if 'what should i do' in question_lower or 'what should id o' in question_lower:
                return 'ROUTING'
            return 'STRATEGIC'
        
        # COMPARATIVE: Comps and examples
        if any(word in question_lower for word in ['comp', 'similar', 'like', 'example', 'greenlit']):
            return 'COMPARATIVE'
        
        # Default to ROUTING if it describes a project
        if any(word in question_lower for word in ['i have a', 'my project', 'my show', 'my film', 'my series']):
            return 'ROUTING'
        
        # Default to HYBRID
        return 'HYBRID'
    
    def extract_attributes(self, question: str) -> Dict[str, Any]:
        """Extract attributes from question"""
        question_lower = question.lower()
        
        # Extract region
        regions = {
            'korea': ['korea', 'korean'],
            'japan': ['japan', 'japanese', 'anime'],
            'india': ['india', 'indian', 'bollywood'],
            'mexico': ['mexico', 'mexican'],
            'brazil': ['brazil', 'brazilian'],
            'uk': ['uk', 'british', 'england'],
            'france': ['france', 'french'],
            'germany': ['germany', 'german'],
            'italy': ['italy', 'italian'],
            'spain': ['spain', 'spanish'],
            'africa': ['africa', 'african'],
            'mena': ['mena', 'middle east', 'arabic', 'saudi', 'saudi arabia', 'dubai', 'uae', 'egypt', 'lebanon', 'jordan', 'morocco', 'tunisia', 'algeria'],
            'us': ['us', 'american', 'usa']
        }
        
        detected_region = None
        for region, keywords in regions.items():
            if any(kw in question_lower for kw in keywords):
                detected_region = region
                break
        
        # Extract format
        formats = {
            'film': ['film', 'movie'],
            'series': ['series', 'show', 'tv'],
            'documentary': ['documentary', 'doc', 'docuseries'],
            'unscripted': ['unscripted', 'reality', 'dating', 'competition']
        }
        
        detected_format = None
        for fmt, keywords in formats.items():
            if any(kw in question_lower for kw in keywords):
                detected_format = fmt
                break
        
        # Extract genre
        genres = {
            'dating': ['dating', 'romance', 'love'],
            'comedy': ['comedy', 'sitcom', 'funny'],
            'drama': ['drama', 'dramatic'],
            'crime': ['crime', 'true crime', 'murder', 'detective'],
            'thriller': ['thriller', 'suspense'],
            'horror': ['horror', 'scary'],
            'sci-fi': ['sci-fi', 'science fiction', 'scifi'],
            'fantasy': ['fantasy'],
            'action': ['action'],
            'sports': ['sports', 'athlete', 'formula 1', 'f1', 'basketball', 'football']
        }
        
        detected_genre = None
        for genre, keywords in genres.items():
            if any(kw in question_lower for kw in keywords):
                detected_genre = genre
                break
        
        return {
            'region': detected_region,
            'format': detected_format,
            'genre': detected_genre
        }
    
    def graph_search(self, question: str, attributes: Dict[str, Any], intent: str = 'ROUTING') -> List[Dict]:
        """Search Neo4j graph database by attributes"""
        if not self.neo4j_driver:
            return []
        
        region = attributes.get('region')
        genre = attributes.get('genre')
        fmt = attributes.get('format')
        
        # Find matching persons from cache
        matches = []
        
        # Match by region (highest priority)
        if region and region in self.persons_by_region:
            matches = self.persons_by_region[region].copy()
        else:
            # Default to US if no region specified
            if 'us' in self.persons_by_region:
                matches = self.persons_by_region['us'].copy()
            else:
                matches = self.persons_cache.copy()
        
        # Sort by seniority level
        def get_seniority_score(person):
            title = person.get('current_title', '').lower()
            
            # Base score by seniority
            if intent == 'STRATEGIC':
                # For strategic queries, prioritize VPs who set mandates
                if 'vp' in title or 'vice president' in title or 'head' in title:
                    base_score = 10
                elif 'director' in title or 'manager' in title:
                    base_score = 20
                else:
                    base_score = 30
            else:
                # For routing queries, prioritize Directors/Managers who take pitches
                if 'director' in title or 'manager' in title:
                    base_score = 10
                elif 'vp' in title or 'vice president' in title or 'head' in title:
                    base_score = 20
                else:
                    base_score = 30
            
            return base_score
        
        matches.sort(key=get_seniority_score)
        
        # For top matches, include their boss for context
        enriched_matches = []
        for person in matches[:5]:
            enriched_matches.append(person)
            
            # If they report to someone, include their boss too
            if person.get('reports_to'):
                boss_name = person['reports_to']
                boss = next((p for p in self.persons_cache if p.get('name') == boss_name), None)
                if boss and boss not in enriched_matches:
                    enriched_matches.append(boss)
        
        return enriched_matches[:7]
    
    def vector_search(self, question: str, top_k: int = 10) -> Dict:
        """Search Pinecone vector database"""
        # Generate embedding for the question
        query_embedding = self.embedding_model.encode(question).tolist()
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Format results
        formatted_results = {
            'ids': [match['id'] for match in results['matches']],
            'distances': [1 - match['score'] for match in results['matches']],
            'metadatas': [match['metadata'] for match in results['matches']],
            'documents': [match['metadata'].get('text', '') for match in results['matches']]
        }
        
        return formatted_results
    
    def fuse_context(self, graph_results: List[Dict], vector_results: Dict, intent: str) -> str:
        """Fuse graph and vector results into context for LLM"""
        context_parts = []
        
        # Include graph results (executives) if available
        if graph_results:
            context_parts.append("=== RELEVANT NETFLIX EXECUTIVES ===\n")
            for person in graph_results:
                context_parts.append(f"\n**{person.get('name')}**")
                if person.get('current_title'):
                    context_parts.append(f"Title: {person['current_title']}")
                if person.get('region'):
                    context_parts.append(f"Region: {person['region']}")
                if person.get('bio'):
                    context_parts.append(f"Bio: {person['bio'][:500]}")
                if person.get('reports_to'):
                    context_parts.append(f"Reports to: {person['reports_to']}")
                if person.get('mandate'):
                    context_parts.append(f"Mandate: {person['mandate'][:500]}")
                context_parts.append("")
        
        # Always include vector results for rich context
        if vector_results['documents']:
            context_parts.append("\n=== RELEVANT INFORMATION FROM KNOWLEDGE BASE ===\n")
            for i, (meta, doc) in enumerate(zip(vector_results['metadatas'][:5], vector_results['documents'][:5])):
                entity_type = meta.get('entity_type', 'unknown')
                name = meta.get('name', 'unknown')
                context_parts.append(f"\n[Source {i+1}: {entity_type} - {name}]")
                context_parts.append(doc[:1500])
                context_parts.append("")
        
        return '\n'.join(context_parts)
    
    def generate_answer(self, question: str, context: str, intent: str) -> str:
        """Generate answer using LLM"""
        
        # Adjust system prompt based on intent
        if intent == 'STRATEGIC':
            system_prompt = """You are the Netflix Mandate Wizard, an expert system that provides strategic intelligence about what Netflix wants.

CRITICAL RULES:
1. For STRATEGIC queries about "what Netflix wants" or "recent mandates", provide STRATEGIC INFORMATION, not routing
2. If asked "what are recent mandates", list 3-5 key strategic priorities from the knowledge base
3. DO NOT route to a specific person unless the query explicitly asks "who" to pitch to
4. Focus on VP-level mandates, strategic priorities, and what content Netflix is seeking
5. Use information from the KNOWLEDGE BASE section to identify recent strategic shifts
6. NO asterisks or bold formatting - use plain text only
7. Keep answers 200-300 words maximum
8. Only use information from the provided context - do NOT make up details

ANSWER FORMAT FOR "WHAT ARE RECENT MANDATES":
- List 3-5 key strategic mandates or priorities
- For each: Who set it (VP name), what they want, why it matters
- Keep it conversational and informative

ANSWER FORMAT FOR "WHAT DOES NETFLIX WANT IN [GENRE]":
- Start with the strategic mandate from the most relevant VP
- Explain what they're looking for and why
- Provide specific examples or recent priorities
- Keep it conversational and direct
"""
        else:
            system_prompt = """You are the Netflix Mandate Wizard, an expert system that helps people figure out who to pitch their projects to at Netflix.

CRITICAL RULES:
1. REGIONAL-FIRST APPROACH: If the project is set in or targets a specific region (MENA, Korea, Mexico, UK, etc.), ALWAYS recommend the regional content director FIRST
2. PRIORITIZE executives from the EXECUTIVES section - they are the most relevant
3. For regional projects: Recommend the regional Director/Manager as the primary contact
4. For US/global projects: Recommend the US-based Director/Manager as the primary contact
5. VPs (Vice Presidents) should only be mentioned as context (e.g., "reports to Brandon Riegg who oversees...")
6. NO asterisks or bold formatting - use plain text only
7. Keep answers 200-300 words maximum
8. Only use information from the provided context - do NOT make up executives or details
9. Focus on ACTIONABLE intelligence: who to contact, what they want, how to position

REGIONAL PROJECT EXAMPLES:
- "True crime in Saudi Arabia" → Pitch to MENA regional director (e.g., Nuha El Tayeb)
- "Korean drama" → Pitch to Korea regional director
- "Mexican comedy" → Pitch to Mexico regional director
- "UK thriller" → Pitch to UK regional director

ANSWER FORMAT:
- First sentence: "Pitch to [Director/Manager Name], [Title]."
- First paragraph: Why this person, their role, mention who they report to for context
- Second paragraph: What they're looking for (mandate details from their boss or the division)
- Third paragraph (optional): How to position your pitch, recent examples
- Keep it conversational and direct

EXAMPLE:
"Pitch to Molly Ebinger, Director of Unscripted Series. She handles dating show development and reports to Brandon Riegg, VP of Nonfiction Series & Sports, who has made dating shows Netflix's highest priority for unscripted content..."
"""
        
        response = self.llm.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}\n\nProvide a clear, actionable answer."}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    
    def query(self, question: str) -> str:
        """Main query method - returns answer string"""
        # Step 1: Classify intent
        intent = self.classify_intent(question)
        
        # Step 2: Extract attributes
        attributes = self.extract_attributes(question)
        
        # Step 3: Graph search (Neo4j)
        graph_results = self.graph_search(question, attributes, intent=intent)
        
        # Step 4: Vector search (Pinecone)
        vector_results = self.vector_search(question, top_k=10)
        
        # Step 5: Fuse context
        context = self.fuse_context(graph_results, vector_results, intent)
        
        # Step 6: Generate answer
        answer = self.generate_answer(question, context, intent)
        
        return answer

    @property
    def persons(self):
        """Return persons for stats endpoint"""
        return self.persons_cache
    
    @property
    def mandates(self):
        """Return empty list for stats endpoint (loaded from vector DB)"""
        return []
    
    @property
    def projects(self):
        """Return empty list for stats endpoint (loaded from vector DB)"""
        return []

