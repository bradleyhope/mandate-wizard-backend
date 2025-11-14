# Conversational RAG Architecture for Mandate Wizard

**Date:** November 12, 2025  
**Based on:** Research of state-of-the-art conversational RAG systems  
**Goal:** Fix critical conversation quality issues with minimal complexity

---

## 🎯 Design Principles

Based on research, our design follows these principles:

1. **Simple over Complex** - Lightweight conversational RAG, not full agentic RAG
2. **Proven Patterns** - Use battle-tested approaches from Haystack, LangChain
3. **Incremental** - Build core features first, add advanced features later
4. **Persistent** - PostgreSQL for conversation storage, not in-memory
5. **Fast** - Query rewriting < 500ms, total response < 3s

---

## 📊 Research Summary

### What We Learned

**From Agentic RAG Research:**
- ✅ Agent layer adds query analysis, context management, adaptive learning
- ✅ Dynamic retrieval strategies based on query type
- ❌ Too complex for our needs (reinforcement learning, multiple agents)
- **Takeaway:** Cherry-pick query analysis and context management only

**From Haystack Conversational RAG:**
- ✅ Dedicated memory store for conversation history
- ✅ Memory retrieval before generation (inject into prompt)
- ✅ Store both user queries AND responses
- ✅ Pipeline architecture makes data flow explicit
- **Takeaway:** Adopt memory injection pattern

**From Query Rewriting Research:**
- ✅ 20% of queries are too short (< 5 words)
- ✅ Follow-ups need conversation context
- ✅ 5 rewriting transformations: context, keywords, abbreviations, entities, pre-built
- **Takeaway:** Focus on conversation context rewriting first

**From Repetition Avoidance Research:**
- ✅ 7 strategies: context tracking, penalties, rephrasing, deduplication, learning, feedback
- ✅ Track last N responses, compare entities
- ✅ Regenerate with exclusions if > 70% overlap
- **Takeaway:** Implement context tracking + explicit deduplication

---

## 🏗️ Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Conversational RAG Engine                    │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Load Conversation History (PostgreSQL)                       │
│     ↓                                                            │
│  2. Query Rewriting (with conversation context)                  │
│     ↓                                                            │
│  3. Retrieval (Pinecone + Neo4j)                                 │
│     ↓                                                            │
│  4. Web Search (if needed)                                       │
│     ↓                                                            │
│  5. Synthesis (with conversation context)                        │
│     ↓                                                            │
│  6. Repetition Detection                                         │
│     ↓ (if repetitive)                                            │
│  7. Regenerate with Exclusions                                   │
│     ↓                                                            │
│  8. Save to Conversation History                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

**1. Conversation Store (PostgreSQL)**
```python
class ConversationStore:
    """
    Manages conversation history in PostgreSQL.
    """
    def create_conversation(self, user_email: str) -> str:
        """Create new conversation, return conversation_id."""
        
    def get_recent_turns(self, conversation_id: str, limit: int = 5) -> List[Dict]:
        """Get last N turns from conversation."""
        
    def add_turn(self, conversation_id: str, question: str, response: Dict):
        """Add new turn to conversation."""
        
    def get_mentioned_entities(self, conversation_id: str, last_n: int = 3) -> Set[str]:
        """Get entities mentioned in last N turns."""
```

**2. Query Rewriter**
```python
class QueryRewriter:
    """
    Rewrites queries with conversation context.
    """
    def rewrite(self, question: str, conversation_history: List[Dict]) -> str:
        """
        Rewrite query with context if it's a follow-up.
        
        Examples:
        - "What other platforms?" → "What streaming platforms besides Netflix..."
        - "in travel" → "What work have we done in travel?"
        """
        if not self._is_follow_up(question):
            return question
        
        return self._rewrite_with_context(question, conversation_history)
    
    def _is_follow_up(self, question: str) -> bool:
        """Detect if question is a follow-up."""
        follow_up_indicators = [
            'other', 'more', 'also', 'what about', 'how about', 
            'else', 'additionally', 'and', 'or', 'besides'
        ]
        return any(indicator in question.lower() for indicator in follow_up_indicators)
    
    def _rewrite_with_context(self, question: str, history: List[Dict]) -> str:
        """Use LLM to rewrite with conversation context."""
        # Build context from last 2 turns
        context = "\n".join([
            f"Q: {turn['question']}\nA: {turn['answer'][:300]}"
            for turn in history[-2:]
        ])
        
        prompt = f"""Given this conversation:

{context}

The user now asks: "{question}"

Rewrite this as a standalone question that includes necessary context.
Output ONLY the rewritten question, nothing else.

Rewritten question:"""
        
        # Use fast model (GPT-4o-mini)
        rewritten = self.llm.generate(prompt, max_tokens=100, temperature=0)
        return rewritten.strip()
```

**3. Repetition Detector**
```python
class RepetitionDetector:
    """
    Detects repetitive responses.
    """
    def detect(
        self, 
        current_response: Dict, 
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Check if current response repeats previous information.
        
        Returns:
        {
            "is_repetitive": bool,
            "repeated_entities": List[str],
            "overlap_ratio": float
        }
        """
        # Extract entities from current response
        current_entities = set(current_response.get('entities', []))
        
        # Extract entities from last 3 responses
        previous_entities = set()
        for turn in conversation_history[-3:]:
            previous_entities.update(turn.get('entities', []))
        
        # Calculate overlap
        if len(current_entities) == 0:
            return {
                "is_repetitive": False,
                "repeated_entities": [],
                "overlap_ratio": 0.0
            }
        
        overlap = current_entities & previous_entities
        overlap_ratio = len(overlap) / len(current_entities)
        
        return {
            "is_repetitive": overlap_ratio > 0.7,  # 70% threshold
            "repeated_entities": list(overlap),
            "overlap_ratio": overlap_ratio
        }
```

**4. Conversational Engine (Main)**
```python
class ConversationalEngine:
    """
    Main conversational RAG engine.
    """
    def __init__(self):
        self.retriever = PineconeRetriever()
        self.graph = Neo4jDAO()
        self.embedder = get_embedder()
        self.reranker = get_reranker()
        self.conversation_store = ConversationStore()
        self.query_rewriter = QueryRewriter()
        self.repetition_detector = RepetitionDetector()
        self.web_search = WebSearch()
    
    def answer(
        self, 
        question: str, 
        conversation_id: str = None,
        user_email: str = None
    ) -> Dict[str, Any]:
        """
        Generate answer with conversation context.
        """
        # 1. Load conversation history
        history = []
        if conversation_id:
            history = self.conversation_store.get_recent_turns(conversation_id, limit=5)
        
        # 2. Rewrite query with context (if follow-up)
        contextualized_query = self.query_rewriter.rewrite(question, history)
        
        # 3. Retrieve from database
        docs = self.retrieve(contextualized_query)
        entities = self.enrich_entities(docs)
        
        # 4. Check if we need web search
        web_results = []
        if self._should_use_web_search(docs, entities, question):
            web_results = self.web_search.search(contextualized_query)
        
        # 5. Synthesize answer with conversation context
        response = self.synthesize(
            question=question,
            docs=docs,
            entities=entities,
            web_results=web_results,
            conversation_history=history
        )
        
        # 6. Check for repetition
        repetition_check = self.repetition_detector.detect(response, history)
        
        # 7. Regenerate if repetitive
        if repetition_check['is_repetitive']:
            excluded_entities = repetition_check['repeated_entities']
            response = self.synthesize_with_exclusions(
                question, docs, entities, web_results, history, excluded_entities
            )
        
        # 8. Save to conversation history
        if conversation_id:
            self.conversation_store.add_turn(conversation_id, question, response)
        
        return response
    
    def synthesize(
        self,
        question: str,
        docs: List[Dict],
        entities: List[Dict],
        web_results: List[Dict],
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Synthesize answer with conversation context.
        """
        # Build conversation context
        conversation_context = ""
        if conversation_history:
            conversation_context = "\n\n".join([
                f"Previous Q: {turn['question']}\nPrevious A: {turn['answer'][:200]}"
                for turn in conversation_history[-2:]  # Last 2 turns
            ])
        
        # Build prompt with conversation context
        prompt = f"""You are Mandate Wizard, an AI assistant specializing in entertainment industry intelligence.

CONVERSATION CONTEXT:
{conversation_context if conversation_context else "This is the start of a new conversation."}

IMPORTANT CONVERSATION RULES:
1. Review the conversation context above before answering
2. DO NOT repeat information you've already provided
3. Build on previous answers progressively
4. If asked a follow-up, focus on NEW information
5. If you've already named specific people/companies, provide DIFFERENT examples
6. Reference previous answers when relevant ("As I mentioned earlier...")

CURRENT QUESTION:
{question}

RETRIEVED INFORMATION:
{self._format_docs(docs)}

{self._format_web_results(web_results) if web_results else ""}

Provide a comprehensive answer that:
- Acknowledges the conversation context
- Avoids repeating previous information
- Provides new, specific details
- References previous answers when relevant
"""
        
        # Generate response
        response = self.llm.generate(prompt)
        
        return response
    
    def synthesize_with_exclusions(
        self,
        question: str,
        docs: List[Dict],
        entities: List[Dict],
        web_results: List[Dict],
        conversation_history: List[Dict],
        excluded_entities: List[str]
    ) -> Dict[str, Any]:
        """
        Regenerate answer excluding already-mentioned entities.
        """
        exclusion_instruction = f"""

CRITICAL: You have already mentioned these people/companies in previous answers:
{', '.join(excluded_entities)}

DO NOT mention them again. Provide completely NEW examples and information.
Focus on different executives, companies, or projects that you haven't discussed yet.
"""
        
        # Add exclusion to prompt (reuse synthesize logic)
        response = self.synthesize(
            question, docs, entities, web_results, conversation_history
        )
        
        # Append exclusion instruction to system prompt
        # (Implementation detail: modify prompt in synthesize)
        
        return response
```

---

## 💾 Database Schema

### Conversations Table

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255),
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    INDEX idx_conversations_user (user_email),
    INDEX idx_conversations_activity (last_activity_at DESC)
);
```

### Conversation Turns Table

```sql
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    contextualized_query TEXT,  -- Rewritten query
    entities_mentioned TEXT[] DEFAULT '{}',
    intent VARCHAR(50),
    confidence FLOAT,
    sources JSONB DEFAULT '[]'::jsonb,
    web_search_triggered BOOLEAN DEFAULT FALSE,
    repetition_detected BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_turns_conversation (conversation_id, turn_number),
    INDEX idx_turns_created (created_at DESC)
);
```

---

## 🔌 API Changes

### New Endpoints

**1. Create Conversation**
```
POST /api/conversations
Response: {"conversation_id": "uuid"}
```

**2. Get Conversation History**
```
GET /api/conversations/{conversation_id}
Response: {
    "conversation_id": "uuid",
    "turns": [
        {
            "turn_number": 1,
            "question": "...",
            "answer": "...",
            "timestamp": "..."
        },
        ...
    ]
}
```

**3. Modified Answer Endpoint**
```
POST /api/answer
Body: {
    "question": "...",
    "conversation_id": "uuid"  # Optional, creates new if not provided
}
Response: {
    "final_answer": "...",
    "conversation_id": "uuid",  # NEW
    "turn_number": 3,  # NEW
    "contextualized_query": "...",  # NEW (for debugging)
    "repetition_detected": false,  # NEW
    ...
}
```

---

## 📈 Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Query Rewriting | < 500ms | GPT-4o-mini is fast |
| Total Response Time | < 3s | Including all steps |
| Repetition Detection | < 50ms | Simple entity comparison |
| Conversation History Load | < 100ms | PostgreSQL query |
| Memory Overhead | Minimal | Only last 5 turns loaded |

---

## 💰 Cost Estimate

| Component | Usage | Cost/Month |
|-----------|-------|------------|
| Query Rewriting | ~5,000 rewrites @ $0.0001 | $0.50 |
| Conversation Context | +200 tokens/query @ $0.01/1k | $10 |
| PostgreSQL Storage | ~1GB conversations | $0 (within limits) |
| **TOTAL** | | **~$10.50/month** |

---

## 🎯 Success Metrics

### Before (Current State)

- ❌ 0% conversation context awareness
- ❌ ~80% repetition rate in follow-ups
- ❌ Generic, non-specific answers
- ❌ Low user satisfaction

### After (Target State)

- ✅ 100% conversation context awareness
- ✅ < 10% repetition rate
- ✅ Specific, contextual answers
- ✅ > 4.0/5.0 user satisfaction
- ✅ > 90% follow-up quality

---

## 🚀 Implementation Phases

### Phase 1: Core Conversation Features (Week 1)

**Days 1-2: Database & Storage**
- [ ] Create PostgreSQL schema
- [ ] Implement ConversationStore class
- [ ] Add conversation_id to /api/answer
- [ ] Test conversation persistence

**Days 3-4: Query Rewriting**
- [ ] Implement QueryRewriter class
- [ ] Test follow-up detection
- [ ] Test context-aware rewriting
- [ ] Optimize for speed (< 500ms)

**Day 5: Integration & Testing**
- [ ] Integrate into main engine
- [ ] Test end-to-end conversation flow
- [ ] Test with sample conversations

### Phase 2: Repetition Avoidance (Week 2)

**Days 1-2: Detection**
- [ ] Implement RepetitionDetector class
- [ ] Test entity extraction
- [ ] Test overlap calculation
- [ ] Tune threshold (70%?)

**Days 3-4: Regeneration**
- [ ] Implement synthesize_with_exclusions
- [ ] Test exclusion instructions
- [ ] Test regenerated responses
- [ ] Verify no repetition

**Day 5: Testing**
- [ ] Test with repetitive conversations
- [ ] Test edge cases
- [ ] Performance testing

### Phase 3: Web Search Integration (Week 3)

**Days 1-2: Web Search**
- [ ] Implement WebSearch class
- [ ] Integrate search API
- [ ] Test search quality
- [ ] Test result formatting

**Days 3-4: Smart Triggering**
- [ ] Implement should_use_web_search logic
- [ ] Test triggering conditions
- [ ] Test hybrid (DB + web) responses
- [ ] Add source attribution

**Day 5: Testing**
- [ ] Test web search supplementation
- [ ] Test freshness improvements
- [ ] Performance testing

### Phase 4: Production Deployment (Week 4)

**Days 1-2: Testing**
- [ ] Comprehensive conversation testing
- [ ] Performance testing
- [ ] Load testing
- [ ] Bug fixes

**Days 3-4: Deployment**
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Monitor errors
- [ ] Gather user feedback

**Day 5: Documentation**
- [ ] Update API docs
- [ ] Create user guide
- [ ] Create troubleshooting guide

---

## 🔍 Testing Strategy

### Unit Tests

- ConversationStore CRUD operations
- QueryRewriter follow-up detection
- QueryRewriter context rewriting
- RepetitionDetector entity extraction
- RepetitionDetector overlap calculation

### Integration Tests

- End-to-end conversation flow
- Query rewriting → retrieval → synthesis
- Repetition detection → regeneration
- Web search triggering → supplementation

### Conversation Tests

Test with real conversation scenarios:

1. **Simple Follow-up**
   - Q1: "Who should I pitch a documentary about MENA content to?"
   - Q2: "What other platforms are interested?"
   - Expected: Q2 rewritten with context, no repetition

2. **Multiple Follow-ups**
   - Q1: "Tell me about Chris Mansolillo"
   - Q2: "What projects has he worked on?"
   - Q3: "Who has he worked with?"
   - Expected: All rewritten with context, progressive disclosure

3. **Repetitive Pattern**
   - Q1: "Who are the top Netflix executives?"
   - Q2: "Who are the top Amazon executives?"
   - Q3: "Who are the top HBO executives?"
   - Expected: Different executives each time, no repetition

---

## 📋 Next Steps

1. **Review architecture** - Get stakeholder approval
2. **Start Phase 1** - Database & query rewriting
3. **Test relentlessly** - Use real conversations
4. **Deploy incrementally** - Phase by phase
5. **Monitor & iterate** - Gather feedback, improve

---

**Ready to build!** 🚀
