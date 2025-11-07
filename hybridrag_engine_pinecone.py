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
from intelligent_search import IntelligentSearch, score_database_confidence
from answer_enhancer import enhance_answer_with_search_guidance
from smart_followups import SmartFollowupGenerator
from comparison_engine import ComparisonEngine
from data_integration import get_data_integration
from answer_templates import (ROUTING_TEMPLATE_CONVERSATIONAL, STRATEGIC_TEMPLATE_NARRATIVE, 
                               FACTUAL_TEMPLATE_PROFILE, COMPARISON_TEMPLATE_ANALYSIS,
                               PROCEDURAL_TEMPLATE_GUIDE, TEMPLATE_TEMPERATURES, REASONING_EFFORTS)
from local_reranker import get_reranker
from cache_manager import get_cache, RESPONSE_TTL, VECTOR_TTL

class HybridRAGEnginePinecone:
    """Hybrid RAG engine using Pinecone vector database and Neo4j graph database"""
    
    def __init__(self, pinecone_api_key: str, pinecone_index_name: str = "netflix-mandate-wizard",
                 neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
        """Initialize the hybrid RAG engine with Pinecone and Neo4j"""
        
        # Initialize Pinecone with timeout
        import socket
        socket.setdefaulttimeout(10)  # 10 second timeout for all socket operations
        
        try:
            self.pc = Pinecone(api_key=pinecone_api_key)
            self.index = self.pc.Index(pinecone_index_name)
            print("✓ Connected to Pinecone")
        except Exception as e:
            print(f"⚠ Pinecone connection failed: {e}")
            raise RuntimeError(f"Failed to connect to Pinecone: {e}")
        
        # Initialize Neo4j (optional) with timeout
        self.neo4j_driver = None
        if neo4j_uri and neo4j_user and neo4j_password:
            try:
                self.neo4j_driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    connection_timeout=10,  # 10 second connection timeout
                    max_connection_lifetime=30  # 30 second max lifetime
                )
                # Test connection
                with self.neo4j_driver.session() as session:
                    session.run("RETURN 1")
                print("✓ Connected to Neo4j")
            except Exception as e:
                print(f"⚠ Neo4j connection failed: {e}")
                print("  Continuing with Pinecone only...")
                self.neo4j_driver = None
        
        # Initialize embedding model (lazy loading to save memory)
        self._embedding_model = None  # Will be loaded on first use
        
        # Initialize GPT-5 Responses API client
        # Using GPT-5 for maximum capability
        self.model_name = "gpt-5"
        
        # Import GPT-5 client
        from gpt5_client import GPT5Client
        
        # Initialize GPT-5 client
        # Environment variables set in start_app.sh:
        # - OPENAI_API_KEY from manus-secrets
        # - OPENAI_BASE_URL unset (use real OpenAI API)
        self.llm = GPT5Client()
        
        # Initialize intelligent search system
        self.intelligent_search = IntelligentSearch()
        
        # Initialize smart follow-up generator
        self.followup_generator = SmartFollowupGenerator()
        
        # Initialize comparison engine
        self.comparison_engine = ComparisonEngine(neo4j_uri, neo4j_user, neo4j_password)
        
        # Initialize data integration (Task 1A/1B data)
        self.data_integration = get_data_integration()
        data_stats = self.data_integration.get_stats()
        print(f"✅ Loaded Task 1A/1B data: {data_stats['executives']} executives, {data_stats['total_quotes']} quotes, {data_stats['total_projects']} projects")
        
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
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model only when first needed"""
        if self._embedding_model is None:
            print("Loading sentence-transformers model (first use)...")
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("✓ Embedding model loaded")
        return self._embedding_model
    
    def query_greenlights_from_neo4j(self, genre: str = None, limit: int = 10) -> List[Dict]:
        """Query recent greenlights directly from Neo4j"""
        if not self.neo4j_driver:
            return []
        
        try:
            with self.neo4j_driver.session() as session:
                if genre:
                    # Query with genre filter
                    query = """
                        MATCH (g:Greenlight)
                        WHERE g.genre IS NOT NULL AND toLower(g.genre) CONTAINS toLower($genre)
                        RETURN g.title as title, g.genre as genre, g.format as format,
                               g.year as year, g.executive as executive,
                               g.talent_attached as talent, g.description as description,
                               g.greenlight_date as date
                        ORDER BY g.greenlight_date DESC
                        LIMIT $limit
                    """
                    result = session.run(query, genre=genre, limit=limit)
                else:
                    # Query all recent greenlights
                    query = """
                        MATCH (g:Greenlight)
                        WHERE g.greenlight_date IS NOT NULL
                        RETURN g.title as title, g.genre as genre, g.format as format,
                               g.year as year, g.executive as executive,
                               g.talent_attached as talent, g.description as description,
                               g.greenlight_date as date
                        ORDER BY g.greenlight_date DESC
                        LIMIT $limit
                    """
                    result = session.run(query, limit=limit)
                
                greenlights = []
                for record in result:
                    greenlights.append({
                        'title': record['title'],
                        'genre': record['genre'],
                        'format': record['format'],
                        'year': record['year'],
                        'executive': record['executive'],
                        'talent': record['talent'],
                        'description': record['description'],
                        'date': record['date']
                    })
                
                return greenlights
        except Exception as e:
            print(f"Error querying greenlights from Neo4j: {e}")
            return []
    
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
                    if region and region is not None:
                        region = str(region).lower()
                        if region not in self.persons_by_region:
                            self.persons_by_region[region] = []
                        self.persons_by_region[region].append(person)
                
                print(f"✓ Loaded {len(self.persons_cache)} persons from Neo4j")
                print(f"✓ Indexed: {len(self.persons_by_region)} regions")
                
        except Exception as e:
            print(f"⚠ Failed to load persons from Neo4j: {e}")
    
    def classify_intent(self, question: str) -> str:
        """Classify the user's intent using first principles"""
        import re
        question_lower = question.lower().strip()
        
        # PERSON_FINDING: User wants to know WHO to contact
        person_patterns = [
            r'\bwho (do i|should i|to) (pitch|contact|talk to|approach)',
            r'\bwho handles\b',
            r'\bwho is (on|in charge of|responsible for)',
            r'\bwho are (on|in charge of)',
            r'\bwho to (pitch|contact|talk to)',
            r'\bwhere (do i go|to go)\b',
            r'\bwhat (do i|should i) do\b',
        ]
        if any(re.search(pattern, question_lower) for pattern in person_patterns):
            return 'ROUTING'
        
        # MARKET_INFO: User wants to know WHICH countries/markets/regions
        market_patterns = [
            r'\bwhat (countries|markets|regions)',
            r'\bwhich (countries|markets|regions)',
            r'\bi mean what (countries|markets)',
        ]
        if any(re.search(pattern, question_lower) for pattern in market_patterns):
            return 'MARKET_INFO'
        
        # STRATEGIC: User wants to know WHAT Netflix wants
        strategic_patterns = [
            r'\bwhat (kind of|type of|does .* want)',
            r'\bwhat are .* mandates?\b',  # Matches "what are recent mandates", "what are some recent mandates", etc.
            r'\bwhat are .* (priorities|looking for)',
            r'\bwhat is .* (strategy|mandate|priority)',
            r'\bdoes .* want\b',
            r'\bis .* looking for\b',
            r'\bwhat matters to\b',
            r'\brecent mandates?\b',  # Also catch "recent mandates" directly
        ]
        if any(re.search(pattern, question_lower) for pattern in strategic_patterns):
            return 'STRATEGIC'
        
        # CLARIFICATION: Single word or short correction
        if len(question_lower.split()) <= 2:
            return 'CLARIFICATION'
        
        # FACTUAL_QUERY: User wants specific facts (recent greenlights, budgets, timelines)
        factual_patterns = [
            r'\bwhat are (the )?(latest|recent) (documentaries|films|shows|series|projects)',
            r'\bwhat (documentaries|films|shows) (were|are) greenlit',
            r'\bwhat got (greenlit|made|cancelled)',
            r'\bwhat.*(budget|timeline|process|deal)',
            r'\bhow (long|much)',
        ]
        if any(re.search(pattern, question_lower) for pattern in factual_patterns):
            return 'FACTUAL_QUERY'
        
        # EXAMPLE_QUERY: User wants specific examples
        example_patterns = [
            r'\bi need examples',
            r'\bshow me examples',
            r'\bgive me examples',
            r'\bwhat are some examples',
            r'\bthat\'s not very detailed',
        ]
        if any(re.search(pattern, question_lower) for pattern in example_patterns):
            return 'EXAMPLE_QUERY'
        
        # PROCESS_QUERY: User wants to know HOW to do something
        process_patterns = [
            r'\bhow do i',
            r'\bhow to',
            r'\bwhat\'s the (best way|process)',
            r'\bshould i',
            r'\bdo i need',
        ]
        if any(re.search(pattern, question_lower) for pattern in process_patterns):
            return 'PROCESS_QUERY'
        
        # COMPARATIVE: Comps and similar projects
        if any(word in question_lower for word in ['comp', 'similar', 'like']):
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
            'uk': ['uk', 'british', 'england', 'scotland', 'scottish', 'wales', 'welsh'],
            'france': ['france', 'french'],
            'germany': ['germany', 'german'],
            'italy': ['italy', 'italian'],
            'spain': ['spain', 'spanish'],
            'nordics': ['nordic', 'nordics', 'norway', 'norwegian', 'sweden', 'swedish', 'denmark', 'danish', 'finland', 'finnish', 'iceland', 'icelandic'],
            'africa': ['africa', 'african'],
            'mena': ['mena', 'middle east', 'arabic', 'saudi', 'saudi arabia', 'dubai', 'uae', 'egypt', 'egyptian', 'lebanon', 'lebanese', 'jordan', 'moroccan', 'morocco', 'tunisia', 'tunisian', 'algeria', 'algerian'],
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
        """Search Neo4j graph database for matching persons"""
        if not self.neo4j_driver:
            return []
        
        # For MARKET_INFO queries, return representatives from each region
        if intent == 'MARKET_INFO':
            # Get one executive from each region to show which regions have teams
            region_representatives = []
            seen_regions = set()
            for person in self.persons_cache:
                region = person.get('region', 'US')
                if region and region not in seen_regions:
                    region_representatives.append(person)
                    seen_regions.add(region)
            return region_representatives
        
        region = attributes.get('region')
        genre = attributes.get('genre')
        fmt = attributes.get('format')
        referenced_person = attributes.get('referenced_person')
        
        # If we have a referenced person, filter to just that person
        if referenced_person:
            matches = [p for p in self.persons_cache if referenced_person.lower() in p.get('name', '').lower()]
            if matches:
                return matches[:1]  # Return just the referenced person
        
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
            title = (person.get('current_title') or '').lower()
            
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
    
    def vector_search(self, question: str, top_k: int = 10, use_reranking: bool = False) -> Dict:
        """Search Pinecone vector database with optional reranking"""
        # Fetch more results initially for reranking (50 instead of 10)
        initial_top_k = 50 if use_reranking else top_k
        
        # Generate embedding for the question
        query_embedding = self.embedding_model.encode(question).tolist()
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=initial_top_k,
            include_metadata=True
        )
        
        # Extract documents and metadata
        documents = [match['metadata'].get('text', '') for match in results['matches']]
        metadatas = [match['metadata'] for match in results['matches']]
        ids = [match['id'] for match in results['matches']]
        distances = [1 - match['score'] for match in results['matches']]
        
        # Apply reranking if enabled
        if use_reranking and documents:
            try:
                reranker = get_reranker()
                if reranker:
                    # Rerank documents
                    reranked = reranker.rerank(question, documents, top_n=top_k)
                    
                    # Reorder results based on reranking
                    reranked_indices = [r['index'] for r in reranked]
                    documents = [documents[i] for i in reranked_indices]
                    metadatas = [metadatas[i] for i in reranked_indices]
                    ids = [ids[i] for i in reranked_indices]
                    distances = [distances[i] for i in reranked_indices]
                    
                    # Add reranking scores to metadata
                    for i, result in enumerate(reranked):
                        metadatas[i]['rerank_score'] = result['relevance_score']
            except Exception as e:
                print(f"⚠️ Reranking failed: {e}, using original order")
        
        # Format results
        formatted_results = {
            'ids': ids[:top_k],
            'distances': distances[:top_k],
            'metadatas': metadatas[:top_k],
            'documents': documents[:top_k]
        }
        
        # Debug logging
        print(f"[DEBUG] Vector search for '{question[:50]}': found {len(documents)} results")
        if documents:
            print(f"[DEBUG] First result: {documents[0][:200] if documents[0] else 'EMPTY'}")
            print(f"[DEBUG] First metadata: {metadatas[0] if metadatas else 'EMPTY'}")
        
        return formatted_results
    
    def fuse_context(self, graph_results: List[Dict], vector_results: Dict, intent: str, neo4j_greenlights: List[Dict] = None, source_tracker=None) -> str:
        """Fuse graph, vector, and Neo4j greenlight results into context for LLM"""
        context_parts = []
        
        # Track sources if tracker is provided
        if source_tracker:
            source_tracker.reset()
        
        # Include Neo4j greenlights first (highest priority for factual queries)
        if neo4j_greenlights:
            context_parts.append("=== RECENT NETFLIX GREENLIGHTS ===")
            for gl in neo4j_greenlights:
                # Track source
                if source_tracker:
                    citation_num = source_tracker.add_greenlight_source(gl)
                    context_parts.append(f"\n**{gl.get('title', 'Untitled')}** [Source {citation_num}]")
                else:
                    context_parts.append(f"\n**{gl.get('title', 'Untitled')}**")
                if gl.get('genre'):
                    context_parts.append(f"Genre: {gl['genre']}")
                if gl.get('format'):
                    context_parts.append(f"Format: {gl['format']}")
                if gl.get('year'):
                    context_parts.append(f"Year: {gl['year']}")
                if gl.get('executive'):
                    context_parts.append(f"Executive: {gl['executive']}")
                if gl.get('talent'):
                    context_parts.append(f"Talent: {gl['talent']}")
                if gl.get('description'):
                    context_parts.append(f"Description: {gl['description']}")
                if gl.get('date'):
                    context_parts.append(f"Date: {gl['date']}")
                context_parts.append("")
            context_parts.append("\n")
        
        # Include graph results (executives) if available
        if graph_results:
            context_parts.append("=== RELEVANT NETFLIX EXECUTIVES ===\n")
            for person in graph_results:
                # Track source
                if source_tracker:
                    citation_num = source_tracker.add_graph_source(person)
                    context_parts.append(f"\n**{person.get('name')}** [Source {citation_num}]")
                else:
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
            for i, (meta, doc, distance) in enumerate(zip(vector_results['metadatas'][:5], vector_results['documents'][:5], vector_results['distances'][:5])):
                entity_type = meta.get('entity_type', 'unknown')
                name = meta.get('name', 'unknown')
                
                # Track source
                if source_tracker:
                    score = 1 - distance  # Convert distance to similarity score
                    citation_num = source_tracker.add_vector_source(meta, doc, score)
                    context_parts.append(f"\n[Source {citation_num}: {entity_type} - {name}]")
                else:
                    context_parts.append(f"\n[Source {i+1}: {entity_type} - {name}]")
                
                context_parts.append(doc[:1500])
                context_parts.append("")
        
        return '\n'.join(context_parts)
    
    def generate_answer(self, question: str, context: str, intent: str, session_id: str = "default") -> str:
        """Generate answer using LangChain hybrid system"""
        from langchain_hybrid import get_langchain_hybrid
        
        # Use LangChain for answer generation
        lc_hybrid = get_langchain_hybrid()
        result = lc_hybrid.generate_answer(
            question=question,
            context=context,
            intent=intent,
            session_id=session_id,
            include_history=True
        )
        
        # Return full result including follow-ups
        return result
    
    def generate_answer_old(self, question: str, context: str, intent: str) -> str:
        """OLD: Generate answer using direct GPT-4 (kept as fallback)"""
        
        # Adjust system prompt based on intent
        if intent == 'MARKET_INFO':
            system_prompt = """You are the Netflix Mandate Wizard, an expert on Netflix's global operations.

CRITICAL RULES:
1. Lead with the DIRECT ANSWER in the first sentence
2. Use BULLET POINTS for lists of countries/regions
3. Keep total answer under 150 words
4. Write conversationally (use "you", active voice)
5. DO NOT route to specific people unless explicitly asked
6. Use **bold** for region names only

ANSWER FORMAT:

First sentence: Direct answer (e.g., "Netflix has dedicated teams in 7 European regions:")

Bullet list:
• **Region** - Brief context (1-3 words)
• **Region** - Brief context

Final sentence: One sentence about strategic importance

EXAMPLE:
"Netflix has dedicated teams in these European regions:

• **UK/Ireland** - Largest market
• **France** - Strong local production
• **Germany** - Growing subscriber base
• **Spain** - Strategic hub
• **Nordics** - Norway, Sweden, Denmark, Finland, Iceland
• **Italy** - Premium content focus
• **Central/Eastern Europe** - Emerging markets

The biggest investments go to UK, France, and Germany."

Keep it scannable and concise."""
        elif intent == 'FACTUAL_QUERY':
            system_prompt = FACTUAL_TEMPLATE_PROFILE
        elif intent == 'EXAMPLE_QUERY':
            system_prompt = """You are the Netflix Mandate Wizard. The user wants SPECIFIC EXAMPLES.

IMPORTANT: You currently don't have access to a comprehensive project database with specific examples.

When asked for examples:
1. Acknowledge you don't have a complete project catalog
2. Provide any examples mentioned in the context
3. Explain what type of information you DO have (mandates, executive preferences)
4. Suggest where to find examples (Netflix blog, trade publications)

FORMAT:

First sentence: Acknowledge the request

What you can provide: Any examples from context (if available)

Alternative: Where to find comprehensive examples

EXAMPLE:
"I don't have a comprehensive catalog of recent Netflix projects with detailed examples.

What I can tell you: Based on the mandates, Netflix recently prioritized shows like *Love Is Blind* (dating), *The Diplomat* (political thriller), and *Beef* (character-driven drama). These reflect the types of projects executives are seeking.

For detailed examples and case studies, check Variety, Deadline, or Netflix's official blog for recent announcements."

Be helpful while acknowledging limitations."""
        elif intent == 'PROCESS_QUERY':
            system_prompt = PROCEDURAL_TEMPLATE_GUIDE
        elif intent == 'STRATEGIC':
            system_prompt = STRATEGIC_TEMPLATE_NARRATIVE
        elif intent == 'HYBRID':
            # Check if context has greenlight data
            if '=== RECENT NETFLIX GREENLIGHTS ===' in context:
                system_prompt = """You are the Netflix Mandate Wizard. The user is asking about recent greenlights.

CRITICAL RULES:
1. Lead with a DIRECT LIST of the actual greenlights from the context
2. Use the EXACT titles, genres, and details provided in the context
3. DO NOT make up or invent projects - only use what's in the context
4. DO NOT recommend executives unless specifically asked
5. Format as a scannable list with key details

ANSWER FORMAT:

First sentence: Direct answer (e.g., "Netflix has greenlit 3 crime thrillers recently:")

List of projects:
• **Title** - Genre, Format, Year (Executive: Name)
• **Title** - Genre, Format, Year (Executive: Name)

Final sentence: One sentence about the trend or pattern

EXAMPLE:
"Netflix has greenlit 3 crime thrillers recently:

• **Untitled Charlie Brooker Project** - Crime Thriller/Detective, Limited Series (4 episodes), 2025 (Executive: Charlie Brooker, Jessica Rhoades)
• **Bad Influencer** - Crime drama, Series, 2025 (Executive: TBD)
• **A Man on the Inside** - Crime comedy, Series, 2024 (Executive: TBD)

Netflix is clearly investing in diverse crime content, from dark thrillers to lighter crime comedies."

Keep it factual and scannable."""
            else:
                system_prompt = ROUTING_TEMPLATE_CONVERSATIONAL
        else:  # ROUTING - default
            system_prompt = ROUTING_TEMPLATE_CONVERSATIONAL
        
        # Use GPT-5 Responses API with chat completion compatibility
        response = self.llm.chat_completion_compatible(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context}\n\nProvide a clear, actionable answer."}
            ],
            model="gpt-5",
            max_tokens=2000
        )
        
        return response['choices'][0]['message']['content']
    
    def search_resources(self, question: str, intent: str, attributes: dict, answer: str) -> list:
        """Search for relevant external resources (Phase 2: Option A)"""
        try:
            from resource_search import search_resources as do_search
            return do_search(question, intent, attributes, answer)
        except Exception as e:
            print(f"Resource search error: {e}")
            return []
    
    def generate_followups(self, question: str, intent: str, attributes: dict, answer: str = "", conversation_history: list = None) -> list:
        """Generate smart, context-aware follow-up questions using the new generator"""
        # Use the smart follow-up generator for better suggestions
        return self.followup_generator.generate_smart_followups(
            question=question,
            answer=answer,
            intent=intent,
            attributes=attributes,
            conversation_history=conversation_history
        )
    
    def query(self, question: str, conversation_history: list = None) -> dict:
        """Main query method - returns dict with answer and follow-ups"""
        import time
        start_time = time.time()
        query_timeout = 45  # 45 second timeout for entire query
        
        # Check cache first (only for questions without conversation history)
        if not conversation_history:
            from query_cache import query_cache
            cache_key = query_cache._generate_key('query', question)
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                print(f"[CACHE HIT] Returning cached result for: {question[:50]}...")
                return cached_result
        
        # Import source tracker
        from source_tracker import SourceTracker
        from parallel_query import parallelize_hybrid_query, merge_parallel_results
        source_tracker = get_source_tracker()
        
        # Step 0: Resolve references using conversation history
        resolved_question = question
        context_from_history = {}
        
        if conversation_history:
            # Check if question contains pronouns or references
            question_lower = question.lower().strip()
            has_reference = any(word in question_lower for word in ['she', 'he', 'her', 'him', 'they', 'them', 'that person', 'this person', 'more about'])
            is_vague_followup = question_lower in ['more', 'tell me more', 'what else', 'continue', 'go on']
            
            if (has_reference or is_vague_followup) and len(conversation_history) > 0:
                # Search last 3 exchanges for person mentions
                import re
                person_name = None
                
                for exchange in reversed(conversation_history[-3:]):
                    last_answer = exchange.get('answer', '')
                    
                    # Try multiple patterns to extract person name
                    patterns = [
                        r'\*\*([^,]+),\s*([^\*]+)\*\*',  # **Name, Title**
                        r'\*\*([^,]+),',  # **Name,
                        r'^([A-Z][a-z]+\s+[A-Z][a-z]+),',  # Name at start
                    ]
                    
                    for pattern in patterns:
                        name_match = re.search(pattern, last_answer)
                        if name_match:
                            person_name = name_match.group(1)
                            break
                    
                    if person_name:
                        break
                
                if person_name:
                    context_from_history['referenced_person'] = person_name
                    # Append context to question for better intent classification
                    if is_vague_followup:
                        resolved_question = f"Tell me more about {person_name}'s mandates and recent projects"
                    else:
                        resolved_question = f"{question} (referring to {person_name})"
        
        # Step 0.5: Check if this is a comparison query
        comparison_intent = self.comparison_engine.detect_comparison_intent(resolved_question)
        
        if comparison_intent and comparison_intent.get('is_comparison'):
            # Handle comparison query separately
            comp_type = comparison_intent['comparison_type']
            entity1 = comparison_intent['entity1']
            entity2 = comparison_intent['entity2']
            
            if comp_type == 'executives':
                comparison_result = self.comparison_engine.compare_executives(entity1, entity2)
            elif comp_type == 'regions':
                comparison_result = self.comparison_engine.compare_regions(entity1, entity2)
            elif comp_type == 'genres':
                comparison_result = self.comparison_engine.compare_genres(entity1, entity2)
            else:
                # Fallback to normal query
                comparison_result = None
            
            if comparison_result and 'error' not in comparison_result:
                # Return comparison result
                return {
                    'answer': comparison_result['comparison'],
                    'followups': [
                        f"Tell me more about {entity1}",
                        f"Tell me more about {entity2}",
                        "What are other similar options?"
                    ],
                    'resources': [],
                    'confidence': 0.9,
                    'question_analysis': {'is_comparison': True},
                    'intent': 'COMPARATIVE',
                    'context': {
                        'comparison_type': comp_type,
                        'entity1': entity1,
                        'entity2': entity2
                    }
                }
        
        # Step 1: Classify intent (normal query)
        intent = self.classify_intent(resolved_question)
        
        # Step 2: Extract attributes
        attributes = self.extract_attributes(question)
        
        # Step 3: Graph search (Neo4j)
        # If we have a referenced person from context, filter graph results
        if context_from_history.get('referenced_person'):
            attributes['referenced_person'] = context_from_history['referenced_person']
        
        # Check timeout before expensive operation
        if time.time() - start_time > query_timeout:
            raise TimeoutError("Query exceeded time limit before graph search")
        
        graph_results = self.graph_search(resolved_question, attributes, intent=intent)
        
        # Step 4: Vector search (Pinecone)
        vector_results = self.vector_search(question, top_k=10)
        
        # Step 4.5: For factual queries about greenlights, add Neo4j greenlight data
        neo4j_greenlights = []
        if intent in ['FACTUAL_QUERY', 'STRATEGIC', 'HYBRID']:
            # Check if question is about greenlights
            question_lower = question.lower()
            if any(word in question_lower for word in ['greenlight', 'greenlights', 'greenlit', 'recent', 'latest']):
                genre = attributes.get('genre')
                neo4j_greenlights = self.query_greenlights_from_neo4j(genre=genre, limit=10)
                import sys
                print(f"[DEBUG] Found {len(neo4j_greenlights)} greenlights from Neo4j for genre={genre}")
                sys.stdout.flush()
        
        # Step 5: Fuse context with source tracking
        context = self.fuse_context(graph_results, vector_results, intent, neo4j_greenlights=neo4j_greenlights, source_tracker=source_tracker)
        
        # Step 6: Analyze question deeply
        question_analysis = self.intelligent_search.analyze_question(question)
        
        # Check timeout before answer generation
        if time.time() - start_time > query_timeout:
            raise TimeoutError("Query exceeded time limit before answer generation")
        
        # Step 7: Generate answer using LangChain
        session_id = "default"  # Will be passed from app.py
        langchain_result = self.generate_answer(question, context, intent, session_id=session_id)
        
        # Extract answer and follow-ups from LangChain result
        answer = langchain_result['answer']
        langchain_followups = langchain_result.get('follow_up_questions', [])
        
        # Step 7.5: Enhance answer with quotes and projects (Task 1A/1B data)
        # Extract executive name from answer or context
        exec_name = None
        if context_from_history.get('referenced_person'):
            exec_name = context_from_history['referenced_person']
        elif intent == 'ROUTING' and graph_results:
            # Try to extract executive name from graph results
            for result in graph_results[:1]:  # Just check first result
                if 'full_name' in result:
                    exec_name = result['full_name']
                    break
                elif 'name' in result:
                    exec_name = result['name']
                    break
        
        # Enhance answer if we have an executive name
        if exec_name and intent in ['ROUTING', 'STRATEGIC', 'FACTUAL_QUERY']:
            answer = self.data_integration.enhance_answer_with_data(
                answer, 
                exec_name, 
                include_quotes=True, 
                include_projects=True
            )
        
        # Step 8: Score confidence in our answer
        confidence = score_database_confidence(answer, intent, graph_results, vector_results)
        
        # Step 9: If confidence is low, enhance answer with search guidance
        # TEMPORARILY DISABLED - too aggressive, re-enable after data expansion
        # if confidence < 0.6 or not question_analysis.get('can_answer_from_database', True):
        #     search_tactics = self.intelligent_search.determine_search_tactics(question_analysis)
        #     answer = enhance_answer_with_search_guidance(answer, question_analysis, search_tactics)
        
        # Step 10: Use follow-up suggestions from LangChain (GPT-5 generated)
        # Use langchain_followups if available, otherwise generate using old method
        followups = langchain_followups if langchain_followups else self.generate_followups(question, intent, attributes, answer, conversation_history)
        
        # Step 11: Search for relevant resources (Phase 2)
        resources = self.search_resources(question, intent, attributes, answer)
        
        result = {
            'answer': answer,
            'followups': followups,
            'resources': resources,
            'sources': source_tracker.format_for_frontend(),  # Add sources
            'confidence': confidence,
            'question_analysis': question_analysis,
            'intent': intent,
            'context': {
                'referenced_person': context_from_history.get('referenced_person'),
                'attributes': attributes,
                'graph_results_count': len(graph_results) if graph_results else 0,
                'vector_count': len(vector_results.get('documents', [])),
                'graph_count': len(graph_results) if graph_results else 0
            }
        }
        
        # Cache result (only for questions without conversation history)
        if not conversation_history:
            from query_cache import query_cache
            cache_key = query_cache._generate_key('query', question)
            query_cache.set(cache_key, result, ttl=1800)  # Cache for 30 minutes
            print(f"[CACHE SET] Cached result for: {question[:50]}...")
        
        return result

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



    def query_with_streaming(self, question: str, conversation_history: list = None):
        """
        Generator method that yields streaming responses for long-running queries.
        Yields status updates and answer chunks as they arrive from GPT-5.
        """
        # Step 0: Check cache first
        cache = get_cache()
        cached_response = cache.get('response', question)
        
        if cached_response:
            # Return cached response immediately
            yield {'type': 'status', 'message': '✨ Retrieved from cache'}
            yield {'type': 'answer', 'content': cached_response['answer']}
            
            if cached_response.get('followups'):
                yield {'type': 'followups', 'followups': cached_response['followups']}
            
            if cached_response.get('resources'):
                yield {'type': 'resources', 'resources': cached_response['resources']}
            
            if cached_response.get('cards'):
                yield {'type': 'cards', 'cards': cached_response['cards']}
            
            return
        
        # Step 0.5: Resolve references using conversation history
        yield {'type': 'status', 'message': 'Analyzing your question...'}
        
        resolved_question = question
        context_from_history = {}
        
        if conversation_history:
            # Check if question contains pronouns or references
            question_lower = question.lower().strip()
            has_reference = any(word in question_lower for word in ['she', 'he', 'her', 'him', 'they', 'them', 'that person', 'this person', 'more about'])
            is_vague_followup = question_lower in ['more', 'tell me more', 'what else', 'continue', 'go on']
            
            if (has_reference or is_vague_followup) and len(conversation_history) > 0:
                # Search last 3 exchanges for person mentions
                import re
                person_name = None
                
                for exchange in reversed(conversation_history[-3:]):
                    last_answer = exchange.get('answer', '')
                    
                    # Try multiple patterns to extract person name
                    patterns = [
                        r'\*\*([^,]+),\s*([^\*]+)\*\*',  # **Name, Title**
                        r'\*\*([^,]+),',  # **Name,
                        r'^([A-Z][a-z]+\s+[A-Z][a-z]+),',  # Name at start
                    ]
                    
                    for pattern in patterns:
                        name_match = re.search(pattern, last_answer)
                        if name_match:
                            person_name = name_match.group(1)
                            break
                    
                    if person_name:
                        break
                
                if person_name:
                    context_from_history['referenced_person'] = person_name
                    # Append context to question for better intent classification
                    if is_vague_followup:
                        resolved_question = f"Tell me more about {person_name}'s mandates and recent projects"
                    else:
                        resolved_question = f"{question} (referring to {person_name})"
        
        # Step 0.5: Check if this is a comparison query
        yield {'type': 'status', 'message': 'Checking query type...'}
        comparison_intent = self.comparison_engine.detect_comparison_intent(resolved_question)
        
        if comparison_intent and comparison_intent.get('is_comparison'):
            # Handle comparison query separately (non-streaming for now)
            comp_type = comparison_intent['comparison_type']
            entity1 = comparison_intent['entity1']
            entity2 = comparison_intent['entity2']
            
            if comp_type == 'executives':
                comparison_result = self.comparison_engine.compare_executives(entity1, entity2)
            elif comp_type == 'regions':
                comparison_result = self.comparison_engine.compare_regions(entity1, entity2)
            elif comp_type == 'genres':
                comparison_result = self.comparison_engine.compare_genres(entity1, entity2)
            else:
                comparison_result = None
            
            if comparison_result and 'error' not in comparison_result:
                # Yield the complete comparison answer
                yield {'type': 'chunk', 'content': comparison_result['comparison']}
                yield {'type': 'followups', 'data': [
                    f"Tell me more about {entity1}",
                    f"Tell me more about {entity2}",
                    "What are other similar options?"
                ]}
                yield {'type': 'done'}
                return
        
        # Step 1: Classify intent
        yield {'type': 'status', 'message': 'Analyzing query type...'}
        intent = self.classify_intent(resolved_question)
        yield {'type': 'status', 'message': f'Query classified as: {intent}'}
        
        # Step 2: Extract attributes
        attributes = self.extract_attributes(question)
        
        # Step 3: Graph search (Neo4j)
        yield {'type': 'status', 'message': 'Searching executive database...'}
        if context_from_history.get('referenced_person'):
            attributes['referenced_person'] = context_from_history['referenced_person']
        graph_results = self.graph_search(resolved_question, attributes, intent=intent)
        yield {'type': 'status', 'message': f'Found {len(graph_results)} relevant executives'}
        
        # Step 4: Vector search (Pinecone)
        yield {'type': 'status', 'message': 'Retrieving mandate documents...'}
        vector_results = self.vector_search(question, top_k=10)
        yield {'type': 'status', 'message': f'Retrieved {len(vector_results.get("documents", []))} relevant documents'}
        
        # Step 5: Fuse context
        context = self.fuse_context(graph_results, vector_results, intent)
        
        # Step 6: Analyze question deeply
        question_analysis = self.intelligent_search.analyze_question(question)
        
        # Step 7: Generate answer with streaming
        yield {'type': 'status', 'message': 'Generating answer...'}
        
        # Build system prompt using new personalized templates
        if intent == 'FACTUAL_QUERY':
            system_prompt = FACTUAL_TEMPLATE_PROFILE
        elif intent == 'PROCESS_QUERY':
            system_prompt = PROCEDURAL_TEMPLATE_GUIDE
        elif intent == 'STRATEGIC':
            system_prompt = STRATEGIC_TEMPLATE_NARRATIVE
        elif intent == 'HYBRID':
            # Check if context has greenlight data
            if '=== RECENT NETFLIX GREENLIGHTS ===' in context:
                system_prompt = """You are the Netflix Mandate Wizard. The user is asking about recent greenlights.

CRITICAL RULES:
1. Lead with a DIRECT LIST of the actual greenlights from the context
2. Use the EXACT titles, genres, and details provided in the context
3. DO NOT make up or invent projects - only use what's in the context
4. DO NOT recommend executives unless specifically asked
5. Format as a scannable list with key details

ANSWER FORMAT:

First sentence: Direct answer (e.g., "Netflix has greenlit 3 crime thrillers recently:")

List of projects:
• **Title** - Genre, Format, Year (Executive: Name)
• **Title** - Genre, Format, Year (Executive: Name)

Final sentence: One sentence about the trend or pattern

EXAMPLE:
"Netflix has greenlit 3 crime thrillers recently:

• **Untitled Charlie Brooker Project** - Crime Thriller/Detective, Limited Series (4 episodes), 2025 (Executive: Charlie Brooker, Jessica Rhoades)
• **Bad Influencer** - Crime drama, Series, 2025 (Executive: TBD)
• **A Man on the Inside** - Crime comedy, Series, 2024 (Executive: TBD)

Netflix is clearly investing in diverse crime content, from dark thrillers to lighter crime comedies."

Keep it factual and scannable."""
            else:
                system_prompt = ROUTING_TEMPLATE_CONVERSATIONAL
        else:  # ROUTING - default
            system_prompt = ROUTING_TEMPLATE_CONVERSATIONAL
        
        # Generate response using GPT-5 Responses API
        yield {'type': 'status', 'message': 'Generating answer with GPT-5...'}
        
        # Determine reasoning effort based on intent
        reasoning_effort_map = {
            'ROUTING': 'medium',
            'STRATEGIC': 'medium',
            'FACTUAL_QUERY': 'low',
            'COMPARISON': 'high',
            'PROCEDURAL': 'low'
        }
        reasoning_effort = reasoning_effort_map.get(intent, 'medium')
        
        # Build the input for GPT-5
        gpt5_input = f"{system_prompt}\n\nQuestion: {question}\n\nContext:\n{context}\n\nProvide a clear, actionable answer."
        
        # Call GPT-5 Responses API using GPT5Client
        try:
            full_answer = self.llm.create(
                prompt=gpt5_input,
                effort=reasoning_effort,
                verbosity='medium',
                format_type='text',
                timeout=90
            )
            
            if not full_answer:
                error_msg = "GPT-5 returned empty response"
                print(error_msg)
                yield {'type': 'error', 'message': error_msg}
                return
            
        except Exception as e:
            error_msg = f"Error calling GPT-5: {str(e)}"
            print(error_msg)
            yield {'type': 'error', 'message': error_msg}
            return
        
        # Simulate streaming by sending answer in chunks (word by word for smooth effect)
        words = full_answer.split(' ')
        for i, word in enumerate(words):
            # Add space before word (except first word)
            content = (' ' if i > 0 else '') + word
            yield {'type': 'chunk', 'content': content}
        
        # Step 7.5: Enhance answer with quotes and projects (Task 1A/1B data)
        exec_name = None
        if context_from_history.get('referenced_person'):
            exec_name = context_from_history['referenced_person']
        elif intent in ['ROUTING', 'STRATEGIC', 'FACTUAL_QUERY'] and graph_results:
            # Extract executive name from graph results
            for result in graph_results[:1]:
                if 'full_name' in result:
                    exec_name = result['full_name']
                    break
                elif 'name' in result:
                    exec_name = result['name']
                    break
        
        # If we enhanced the answer, send the additional content
        if exec_name and intent in ['ROUTING', 'STRATEGIC', 'FACTUAL_QUERY']:
            enhanced_answer = self.data_integration.enhance_answer_with_data(
                full_answer, 
                exec_name, 
                include_quotes=True, 
                include_projects=True
            )
            
        # Skip embedding quotes in answer - we have beautiful quote cards instead!
        # (Quotes will be sent as separate 'cards' events)
        
        # Step 8: Generate dynamic cards (quotes, etc.)
        if exec_name and intent in ['ROUTING', 'STRATEGIC', 'FACTUAL_QUERY']:
            # Get quote cards for the executive
            quote_cards = self.data_integration.get_quote_cards(exec_name, limit=2, question=question)
            if quote_cards:
                yield {'type': 'cards', 'data': quote_cards}
        
        # Step 9: Generate follow-up suggestions
        followups = self.generate_followups(question, intent, attributes, full_answer, conversation_history)
        if followups:
            yield {'type': 'followups', 'data': followups}
        
        # Step 10: Search for relevant resources
        resources = self.search_resources(question, intent, attributes, full_answer)
        if resources:
            yield {'type': 'resources', 'data': resources}
        
        # Step 11: Cache the complete response for future queries
        try:
            cache_data = {
                'answer': full_answer,
                'followups': followups if followups else [],
                'resources': resources if resources else [],
                'cards': quote_cards if quote_cards else []
            }
            cache.set('response', question, cache_data, ttl=RESPONSE_TTL)
        except Exception as e:
            print(f"⚠️ Failed to cache response: {e}")
        
        # Final signal
        yield {'type': 'done'}

