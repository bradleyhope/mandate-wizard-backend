"""
Progressive Engine - Generates progressively better answers with semantic repetition avoidance
Phase 1: Gemini-optimized version
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time

from .conversation_manager import TurnContext, ResponseStrategy
from .conversation_store import ConversationStore


@dataclass
class ResponseQuality:
    """Quality metrics for a response"""
    overall_score: float
    specificity: float
    actionability: float
    strategic_value: float
    context_awareness: float
    novelty: float
    
    def to_dict(self) -> Dict:
        return {
            'overall': self.overall_score,
            'specificity': self.specificity,
            'actionability': self.actionability,
            'strategic_value': self.strategic_value,
            'context_awareness': self.context_awareness,
            'novelty': self.novelty
        }


class ProgressiveEngine:
    """Generates progressively improving answers"""
    
    def __init__(self, store: ConversationStore, rag_engine, llm_client, embedding_client):
        self.store = store
        self.rag = rag_engine
        self.llm = llm_client
        self.embeddings = embedding_client
        
        # Thresholds (from AI feedback)
        self.SEMANTIC_REPETITION_THRESHOLD = 0.85  # Gemini/Claude recommendation
        self.MAX_REGENERATION_ATTEMPTS = 2
    
    # ========================================================================
    # MAIN GENERATION FLOW
    # ========================================================================
    
    def generate_answer(self, context: TurnContext) -> Tuple[str, ResponseQuality, float]:
        """
        Generate progressively better answer
        Returns: (answer, quality, repetition_score)
        """
        start_time = time.time()
        
        # Retrieve relevant documents
        documents = self._retrieve_documents(context)
        
        # Generate answer
        answer = self._generate_with_strategy(context, documents)
        
        # Get embedding for semantic similarity using OpenAI embeddings API
        embedding_response = self.embeddings.embeddings.create(
            model="text-embedding-3-small",
            input=answer
        )
        answer_embedding = embedding_response.data[0].embedding
        
        # Check semantic repetition
        previous_embeddings = self.store.get_previous_answer_embeddings(
            context.conversation_id,
            limit=5
        )
        repetition_score = self.store.calculate_semantic_repetition(
            answer_embedding,
            previous_embeddings
        )
        
        # Regenerate if too repetitive
        regeneration_count = 0
        while (repetition_score > self.SEMANTIC_REPETITION_THRESHOLD and 
               regeneration_count < self.MAX_REGENERATION_ATTEMPTS):
            
            print(f"Repetition detected ({repetition_score:.2f}), regenerating...")
            
            # Regenerate with stronger novelty emphasis
            answer = self._generate_with_strategy(
                context,
                documents,
                emphasize_novelty=True,
                previous_answer=answer
            )
            
            embedding_response = self.embeddings.embeddings.create(
                model="text-embedding-3-small",
                input=answer
            )
            answer_embedding = embedding_response.data[0].embedding
            repetition_score = self.store.calculate_semantic_repetition(
                answer_embedding,
                previous_embeddings
            )
            
            regeneration_count += 1
        
        # Calculate quality
        quality = self._calculate_quality(answer, context, repetition_score)
        
        # Extract entities mentioned
        entities_mentioned = self._extract_entities(answer)
        
        # Save turn to database
        from .conversation_store import ConversationTurn
        turn = ConversationTurn(
            turn_number=context.turn_number,
            user_query=context.user_query,
            answer=answer,
            question_type=context.question_type.value,
            rewritten_query=context.rewritten_query,
            response_strategy=context.response_strategy.value,
            quality_score=quality.overall_score,
            repetition_score=repetition_score,
            entities_mentioned=entities_mentioned,
            new_entities_count=len([e for e in entities_mentioned if e not in context.state.covered_entities]),
            response_time_ms=int((time.time() - start_time) * 1000)
        )
        
        # Get query embedding
        embedding_response = self.embeddings.embeddings.create(
            model="text-embedding-3-small",
            input=context.rewritten_query
        )
        query_embedding = embedding_response.data[0].embedding
        
        self.store.add_turn(
            context.conversation_id,
            turn,
            query_embedding=query_embedding,
            answer_embedding=answer_embedding
        )
        
        # Update conversation state
        from .conversation_manager import ConversationManager
        manager = ConversationManager(self.store, self.llm)
        manager.update_state_after_turn(
            context,
            answer,
            entities_mentioned,
            quality.overall_score
        )
        
        # Track entity mentions
        for entity in entities_mentioned:
            self.store.track_entity_mention(
                context.conversation_id,
                entity_id=entity.lower().replace(' ', '_'),
                entity_name=entity,
                entity_type='person',  # TODO: Detect type
                turn_number=context.turn_number
            )
        
        return answer, quality, repetition_score
    
    # ========================================================================
    # DOCUMENT RETRIEVAL
    # ========================================================================
    
    def _retrieve_documents(self, context: TurnContext) -> List[Dict]:
        """Retrieve relevant documents with entity filtering"""
        
        # Use rewritten query for better retrieval
        query = context.rewritten_query
        
        # Build filter based on entities to exclude/include
        filter_criteria = {}
        
        if context.entities_to_include:
            # For comparative questions: only get docs about these entities
            filter_criteria['entity_names'] = context.entities_to_include
        elif context.entities_to_exclude:
            # For exploration: exclude docs primarily about these entities
            filter_criteria['exclude_entity_names'] = context.entities_to_exclude
        
        # Retrieve from RAG (Pinecone vector search)
        # Note: Engine.retrieve() only accepts 'question' parameter, not 'query', 'top_k', or 'filters'
        try:
            documents = self.rag.retrieve(query)
            print(f"✅ Retrieved {len(documents)} documents from Pinecone")
        except Exception as e:
            print(f"❌ Retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            documents = []  # Return empty list to allow graceful degradation
        
        # Enrich with Neo4j entity data (person profiles, relationships, etc.)
        try:
            entities = self.rag.enrich_entities(documents)
            if entities:
                print(f"✅ Enriched with {len(entities)} entities from Neo4j")
                for entity in entities:
                    # Convert Neo4j entity to document format
                    entity_doc = {
                        'metadata': {
                            'text': self._format_entity_as_text(entity),
                            'source': 'neo4j',
                            'entity_id': entity.get('entity_id'),
                            'entity_type': entity.get('type')
                        },
                        'score': 0.9  # High score for entity enrichment
                    }
                    documents.append(entity_doc)
            else:
                print("⚠️ Neo4j enrichment returned 0 entities")
        except Exception as e:
            print(f"⚠️ Neo4j enrichment failed: {e}")
        
        # Check if web search is needed
        if self._should_trigger_web_search(context, documents):
            web_results = self._web_search(query)
            documents.extend(web_results)
        
        return documents
    
    def _should_trigger_web_search(self, context: TurnContext, documents: List[Dict]) -> bool:
        """Determine if web search should be triggered"""
        
        # Only trigger for explicit recency queries to minimize latency
        query_lower = context.user_query.lower()
        recency_keywords = ['current', 'recent', 'latest', 'now', 'today', '2025', '2024', 'this year']
        
        # Must have recency keyword AND few documents
        has_recency = any(keyword in query_lower for keyword in recency_keywords)
        few_docs = len(documents) < 5
        
        # Only trigger if both conditions met (more restrictive)
        return has_recency and few_docs
    
    def _web_search(self, query: str) -> List[Dict]:
        """Perform web search using Perplexity API for fresh information"""
        import os
        import requests
        
        api_key = os.getenv('SONAR_API_KEY')
        if not api_key:
            print("⚠️ SONAR_API_KEY not found, skipping web search")
            return []
        
        try:
            print(f"🌐 Triggering web search for: {query}")
            
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'sonar-pro',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a research assistant. Provide factual, up-to-date information with sources.'
                        },
                        {
                            'role': 'user',
                            'content': query
                        }
                    ],
                    'max_tokens': 500,
                    'temperature': 0.2,
                    'return_citations': True
                },
                timeout=5  # Reduced from 10s for faster response
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                citations = data.get('citations', [])
                
                if content:
                    print(f"✅ Web search returned {len(content)} chars, {len(citations)} citations")
                    # Format as a document for the RAG system
                    return [{
                        'text': content,
                        'metadata': {
                            'source': 'web_search',
                            'citations': citations,
                            'query': query,
                            'timestamp': 'real-time'
                        }
                    }]
            else:
                print(f"⚠️ Web search failed: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Web search error: {e}")
        
        return []
    
    # ========================================================================
    # ANSWER GENERATION
    # ========================================================================
    
    def _generate_with_strategy(
        self,
        context: TurnContext,
        documents: List[Dict],
        emphasize_novelty: bool = False,
        previous_answer: Optional[str] = None
    ) -> str:
        """Generate answer using appropriate strategy"""
        
        # Build prompt based on strategy
        prompt = self._build_prompt(context, documents, emphasize_novelty, previous_answer)
        
        # Generate using OpenAI chat completions API
        response = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """You are a helpful assistant for entertainment industry professionals.

Formatting rules:
- Use **bold** for names, titles, and key terms
- Use bullet points (-) for lists
- Use numbered lists (1., 2., 3.) for steps or rankings
- Keep paragraphs concise (2-3 sentences max)
- Use clear section breaks
- Be direct and actionable

Provide detailed, accurate answers based on the provided context."""},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content
        return answer.strip()
    
    def _build_prompt(
        self,
        context: TurnContext,
        documents: List[Dict],
        emphasize_novelty: bool,
        previous_answer: Optional[str]
    ) -> str:
        """Build prompt based on response strategy"""
        
        # Format documents
        doc_context = "\n\n".join([
            f"[{i+1}] {doc.get('content', '')[:500]}..."
            for i, doc in enumerate(documents[:5])
        ])
        
        # Build conversation history
        history = ""
        if context.recent_turns:
            history = "\n".join([
                f"User: {turn.user_query}\nAssistant: {turn.answer[:200]}..."
                for turn in context.recent_turns[-2:]
            ])
        
        # Strategy-specific instructions
        strategy_instructions = self._get_strategy_instructions(context.response_strategy)
        
        # Novelty instructions
        novelty_instructions = ""
        if emphasize_novelty and previous_answer:
            novelty_instructions = f"""
IMPORTANT: Your previous answer was too similar to earlier responses. 
Previous answer: {previous_answer[:300]}...

You MUST provide NEW information. Focus on:
- NEW entities not mentioned before
- NEW facts and insights
- NEW perspectives or angles
"""
        elif context.entities_to_exclude:
            novelty_instructions = f"""
IMPORTANT: Avoid repeating information about these entities (already covered):
{', '.join(context.entities_to_exclude[:10])}

Focus on NEW entities and information.
"""
        
        # Comparative question handling
        comparative_instructions = ""
        if context.entities_to_include:
            comparative_instructions = f"""
This is a COMPARATIVE question. Focus specifically on these entities:
{', '.join(context.entities_to_include)}

Provide a side-by-side comparison highlighting key differences.
"""
        
        # Build full prompt
        prompt = f"""You are an expert assistant helping users with strategic decision-making.

CONVERSATION HISTORY:
{history}

CURRENT QUESTION: {context.user_query}

RELEVANT INFORMATION:
{doc_context}

{strategy_instructions}

{comparative_instructions}

{novelty_instructions}

QUALITY REQUIREMENTS:
- Be SPECIFIC: Include names, numbers, concrete details
- Be ACTIONABLE: Provide clear next steps when relevant
- Be STRATEGIC: Explain WHY, not just WHAT
- Be CONTEXTUAL: Build on the conversation naturally
- Be NOVEL: Add NEW value compared to previous answers

Answer:"""
        
        return prompt
    
    def _get_strategy_instructions(self, strategy: ResponseStrategy) -> str:
        """Get strategy-specific instructions"""
        
        if strategy == ResponseStrategy.BREADTH:
            return """RESPONSE STRATEGY: BREADTH
Provide a wide overview covering multiple options/entities.
Aim for 3-5 different entities or options with brief descriptions of each."""
        
        elif strategy == ResponseStrategy.DEPTH:
            return """RESPONSE STRATEGY: DEPTH
Provide deep, detailed information about the specific topic/entity.
Include background, track record, specific examples, and nuanced insights."""
        
        elif strategy == ResponseStrategy.COMPARE:
            return """RESPONSE STRATEGY: COMPARE
Provide a clear side-by-side comparison.
Highlight key similarities and differences across relevant dimensions."""
        
        elif strategy == ResponseStrategy.STRATEGIC_ADVICE:
            return """RESPONSE STRATEGY: STRATEGIC ADVICE
Provide high-level strategic guidance.
Focus on the big picture, key considerations, and recommended approach."""
        
        elif strategy == ResponseStrategy.ACTIONABLE_STEPS:
            return """RESPONSE STRATEGY: ACTIONABLE STEPS
Provide concrete, tactical next steps.
Be specific about WHO to contact, WHAT to prepare, WHEN to act, HOW to approach."""
        
        return ""
    
    # ========================================================================
    # QUALITY CALCULATION
    # ========================================================================
    
    def _calculate_quality(
        self,
        answer: str,
        context: TurnContext,
        repetition_score: float
    ) -> ResponseQuality:
        """Calculate quality metrics"""
        
        # Specificity: presence of names, numbers, concrete details
        specificity = self._score_specificity(answer)
        
        # Actionability: presence of action verbs, steps, recommendations
        actionability = self._score_actionability(answer)
        
        # Strategic value: presence of insights, reasoning, "why"
        strategic_value = self._score_strategic_value(answer)
        
        # Context awareness: references to previous conversation
        context_awareness = self._score_context_awareness(answer, context)
        
        # Novelty: inverse of repetition
        novelty = 1.0 - repetition_score
        
        # Overall score (weighted average)
        overall = (
            specificity * 0.25 +
            actionability * 0.20 +
            strategic_value * 0.20 +
            context_awareness * 0.15 +
            novelty * 0.20
        )
        
        return ResponseQuality(
            overall_score=overall,
            specificity=specificity,
            actionability=actionability,
            strategic_value=strategic_value,
            context_awareness=context_awareness,
            novelty=novelty
        )
    
    def _score_specificity(self, answer: str) -> float:
        """Score based on specific details"""
        score = 0.5  # Base score
        
        # Check for proper nouns (capitalized words)
        import re
        proper_nouns = len(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', answer))
        score += min(proper_nouns * 0.05, 0.3)
        
        # Check for numbers
        numbers = len(re.findall(r'\b\d+\b', answer))
        score += min(numbers * 0.05, 0.2)
        
        return min(score, 1.0)
    
    def _score_actionability(self, answer: str) -> float:
        """Score based on actionable content"""
        score = 0.3  # Base score
        
        action_keywords = [
            'contact', 'reach out', 'prepare', 'submit', 'send',
            'schedule', 'follow up', 'research', 'consider', 'focus on'
        ]
        
        answer_lower = answer.lower()
        action_count = sum(1 for keyword in action_keywords if keyword in answer_lower)
        score += min(action_count * 0.1, 0.5)
        
        # Check for numbered lists or bullet points
        if any(marker in answer for marker in ['1.', '2.', '•', '-']):
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_strategic_value(self, answer: str) -> float:
        """Score based on strategic insights"""
        score = 0.4  # Base score
        
        strategic_keywords = [
            'because', 'therefore', 'however', 'consider', 'important',
            'key', 'critical', 'advantage', 'opportunity', 'risk'
        ]
        
        answer_lower = answer.lower()
        strategic_count = sum(1 for keyword in strategic_keywords if keyword in answer_lower)
        score += min(strategic_count * 0.08, 0.4)
        
        # Check for reasoning patterns
        if 'this is important because' in answer_lower or 'the reason' in answer_lower:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_context_awareness(self, answer: str, context: TurnContext) -> float:
        """Score based on conversation context"""
        score = 0.5  # Base score
        
        # Check if answer references previous conversation
        context_phrases = [
            'as mentioned', 'as discussed', 'building on', 'in addition to',
            'compared to', 'unlike', 'similar to', 'previously'
        ]
        
        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in context_phrases):
            score += 0.3
        
        # Check if answer mentions entities from conversation
        if context.state.covered_entities:
            mentioned_count = sum(
                1 for entity in context.state.covered_entities[:5]
                if entity.lower() in answer_lower
            )
            # Moderate bonus (we want NEW entities, but some reference is good)
            score += min(mentioned_count * 0.05, 0.2)
        
        return min(score, 1.0)
    
    # ========================================================================
    # ENTITY EXTRACTION
    # ========================================================================
    
    def _extract_entities(self, answer: str) -> List[str]:
        """Extract entity names from answer"""
        import re
        
        # Simple extraction: find capitalized phrases (2-3 words)
        # This is a placeholder - in production, use NER
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
        matches = re.findall(pattern, answer)
        
        # Filter out common words
        stopwords = {'The', 'This', 'That', 'These', 'Those', 'When', 'Where', 'Why', 'How'}
        entities = [m for m in matches if m not in stopwords]
        
        # Deduplicate
        unique_entities = list(dict.fromkeys(entities))
        
        return unique_entities[:20]  # Limit to top 20

    def _format_entity_as_text(self, entity: Dict) -> str:
        """Format Neo4j entity data as readable text for LLM context"""
        entity_type = entity.get('type', 'unknown')
        data = entity.get('data', {})
        
        if entity_type == 'person':
            # Format person entity
            name = data.get('name', 'Unknown')
            title = data.get('title', '')
            company = data.get('company', '')
            bio = data.get('bio', '')
            
            text_parts = [f"{name}"]
            if title:
                text_parts.append(f"Title: {title}")
            if company:
                text_parts.append(f"Company: {company}")
            if bio:
                text_parts.append(f"Bio: {bio}")
            
            return " | ".join(text_parts)
            
        elif entity_type == 'company':
            # Format company entity
            name = data.get('name', 'Unknown')
            description = data.get('description', '')
            
            text_parts = [f"{name}"]
            if description:
                text_parts.append(f"Description: {description}")
            
            return " | ".join(text_parts)
            
        else:
            # Generic format
            return json.dumps(data)
