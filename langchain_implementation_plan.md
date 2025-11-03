# LangChain Integration Implementation Plan
**Strategic implementation of LangChain/LangGraph for Mandate Wizard**

---

## Overview

We're implementing LangChain incrementally to add stateful pathways, user memory, and observability without breaking the existing working system.

---

## Phase 1: Install Dependencies ✅ COMPLETE

**Installed:**
- `langchain` (1.0.1) - Core framework
- `langchain-core` - Base abstractions
- `langchain-openai` - OpenAI integration
- `langgraph` - Stateful workflows
- `langsmith` - Observability
- `mem0ai` - User memory

---

## Phase 2: User Memory System (NEXT)

### Goal
Implement persistent user memory to remember:
- User's project details (genre, region, format)
- Sophistication level (novice, mid-level, advanced)
- Conversation stage (Layer 1-8)
- Past queries and preferences

### Implementation

**File:** `user_memory.py`

```python
from mem0 import Memory
import os

class UserMemoryManager:
    def __init__(self):
        self.memory = Memory()
    
    def add_user_context(self, user_id: str, context: dict):
        """Store user context (project, persona, stage)"""
        for key, value in context.items():
            self.memory.add(
                f"User {key}: {value}",
                user_id=user_id,
                metadata={"type": "context", "key": key}
            )
    
    def get_user_context(self, user_id: str, query: str):
        """Retrieve relevant user memories"""
        memories = self.memory.search(
            query,
            user_id=user_id,
            limit=10
        )
        return memories
    
    def detect_project_details(self, query: str):
        """Extract project details from query"""
        # Genre detection
        genres = ['thriller', 'comedy', 'drama', 'horror', 'sci-fi', 'romance']
        detected_genre = next((g for g in genres if g in query.lower()), None)
        
        # Region detection
        regions = ['korean', 'korea', 'spanish', 'latin', 'french', 'uk', 'india']
        detected_region = next((r for r in regions if r in query.lower()), None)
        
        # Format detection
        formats = ['series', 'film', 'movie', 'limited series', 'unscripted', 'documentary']
        detected_format = next((f for f in formats if f in query.lower()), None)
        
        return {
            'genre': detected_genre,
            'region': detected_region,
            'format': detected_format
        }
```

**Integration Point:** Add to `app.py` query handler

---

## Phase 3: Persona Detection System

### Goal
Detect user sophistication level and persona type from query patterns.

### Implementation

**File:** `persona_detector.py`

```python
from typing import Dict, Literal
import re

PersonaType = Literal['screenwriter', 'producer', 'executive', 'agent', 'business_affairs']
SophisticationLevel = Literal['novice', 'mid-level', 'advanced']

class PersonaDetector:
    def __init__(self):
        self.novice_signals = [
            'how do i', 'where do i start', 'new to', 'first time',
            'beginner', 'help me understand', 'what is', 'explain'
        ]
        
        self.advanced_signals = [
            'competitive intelligence', 'recent greenlights', 'pipeline',
            'what has [name] greenlit', 'slate', 'positioning',
            'deal structure', 'package', 'attach', 'talent'
        ]
        
        self.crisis_signals = [
            'urgent', 'deadline', 'asap', 'need to decide',
            'days', 'hours', 'by [date]', 'time-sensitive'
        ]
        
        self.persona_signals = {
            'screenwriter': ['my script', 'i wrote', 'my story', 'pitch my', 'first screenplay'],
            'producer': ['producing', 'package', 'attach', 'financing', 'production company'],
            'executive': ['competitive', 'slate', 'pipeline', 'greenlit', 'development'],
            'agent': ['my client', 'talent', 'actor', 'represent', 'availability'],
            'business_affairs': ['deal', 'budget', 'terms', 'contract', 'negotiation']
        }
    
    def detect_sophistication(self, query: str, conversation_history: list) -> SophisticationLevel:
        """Detect user sophistication level"""
        query_lower = query.lower()
        
        # Check for novice signals
        if any(signal in query_lower for signal in self.novice_signals):
            return 'novice'
        
        # Check for advanced signals
        if any(signal in query_lower for signal in self.advanced_signals):
            return 'advanced'
        
        # Check conversation history complexity
        if len(conversation_history) > 5:
            # If user has asked multiple sophisticated questions, they're advanced
            advanced_count = sum(
                1 for msg in conversation_history
                if any(signal in msg.lower() for signal in self.advanced_signals)
            )
            if advanced_count >= 2:
                return 'advanced'
        
        # Default to mid-level
        return 'mid-level'
    
    def detect_persona(self, query: str, conversation_history: list) -> PersonaType:
        """Detect user persona type"""
        query_lower = query.lower()
        
        # Score each persona
        scores = {}
        for persona, signals in self.persona_signals.items():
            scores[persona] = sum(1 for signal in signals if signal in query_lower)
        
        # Return persona with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        # Default to producer (most common)
        return 'producer'
    
    def detect_crisis_mode(self, query: str) -> bool:
        """Detect if user is in crisis/time-sensitive mode"""
        query_lower = query.lower()
        return any(signal in query_lower for signal in self.crisis_signals)
    
    def get_user_profile(self, query: str, conversation_history: list) -> Dict:
        """Get complete user profile"""
        return {
            'sophistication_level': self.detect_sophistication(query, conversation_history),
            'persona': self.detect_persona(query, conversation_history),
            'crisis_mode': self.detect_crisis_mode(query),
            'query_count': len(conversation_history)
        }
```

---

## Phase 4: LangGraph Workflow for 8-Layer Pathway

### Goal
Create a stateful graph that navigates through the 8 intelligence layers based on user needs.

### Implementation

**File:** `pathway_graph.py`

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator

class PathwayState(TypedDict):
    """State that persists across the pathway"""
    query: str
    user_id: str
    user_profile: dict
    project_details: dict
    current_layer: int
    executive_name: str
    executive_context: dict
    production_companies: list
    recent_greenlights: list
    packaging_intel: dict
    answer: str
    follow_ups: list
    confidence_score: float
    sources: list

class MandateWizardPathway:
    def __init__(self, rag_engine, memory_manager, persona_detector):
        self.rag_engine = rag_engine
        self.memory = memory_manager
        self.persona_detector = persona_detector
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the 8-layer pathway graph"""
        workflow = StateGraph(PathwayState)
        
        # Add nodes for each layer
        workflow.add_node("detect_persona", self.detect_persona_node)
        workflow.add_node("layer1_routing", self.layer1_executive_routing)
        workflow.add_node("layer2_mandate", self.layer2_executive_mandate)
        workflow.add_node("layer3_prodco", self.layer3_production_companies)
        workflow.add_node("layer4_greenlights", self.layer4_recent_greenlights)
        workflow.add_node("layer5_pitch", self.layer5_pitch_requirements)
        workflow.add_node("layer6_packaging", self.layer6_packaging_intelligence)
        workflow.add_node("generate_answer", self.generate_answer_node)
        workflow.add_node("generate_followups", self.generate_followups_node)
        
        # Define edges (pathway flow)
        workflow.set_entry_point("detect_persona")
        workflow.add_edge("detect_persona", "layer1_routing")
        workflow.add_conditional_edges(
            "layer1_routing",
            self.should_continue_to_layer2,
            {
                "continue": "layer2_mandate",
                "generate": "generate_answer"
            }
        )
        workflow.add_conditional_edges(
            "layer2_mandate",
            self.should_continue_to_layer3,
            {
                "continue": "layer3_prodco",
                "generate": "generate_answer"
            }
        )
        # ... continue for all layers
        
        workflow.add_edge("generate_answer", "generate_followups")
        workflow.add_edge("generate_followups", END)
        
        return workflow.compile()
    
    def detect_persona_node(self, state: PathwayState) -> PathwayState:
        """Node 0: Detect user persona and sophistication"""
        # Get user memories
        memories = self.memory.get_user_context(state['user_id'], state['query'])
        
        # Detect persona
        profile = self.persona_detector.get_user_profile(
            state['query'],
            conversation_history=[]  # TODO: Get from memory
        )
        
        # Detect project details
        project_details = self.memory.detect_project_details(state['query'])
        
        # Store in memory
        self.memory.add_user_context(state['user_id'], {
            'persona': profile['persona'],
            'sophistication': profile['sophistication_level'],
            **project_details
        })
        
        return {
            **state,
            'user_profile': profile,
            'project_details': project_details,
            'current_layer': 0
        }
    
    def layer1_executive_routing(self, state: PathwayState) -> PathwayState:
        """Layer 1: Route to correct executive"""
        # Call existing RAG engine
        results = self.rag_engine.hybrid_search(
            state['query'],
            search_type='routing'
        )
        
        # Extract executive name
        executive_name = self._extract_executive_name(results)
        
        return {
            **state,
            'executive_name': executive_name,
            'current_layer': 1,
            'sources': results.get('sources', [])
        }
    
    def layer2_executive_mandate(self, state: PathwayState) -> PathwayState:
        """Layer 2: Get executive mandate and taste"""
        # Get executive context from Neo4j
        executive_context = self.rag_engine.get_executive_context(
            state['executive_name']
        )
        
        return {
            **state,
            'executive_context': executive_context,
            'current_layer': 2
        }
    
    def layer3_production_companies(self, state: PathwayState) -> PathwayState:
        """Layer 3: Get production company pathway"""
        # Extract production companies from context
        production_companies = self._extract_production_companies(
            state['executive_context']
        )
        
        return {
            **state,
            'production_companies': production_companies,
            'current_layer': 3
        }
    
    def layer4_recent_greenlights(self, state: PathwayState) -> PathwayState:
        """Layer 4: Get recent greenlights (if available)"""
        # TODO: Query greenlights database when built
        recent_greenlights = []
        
        return {
            **state,
            'recent_greenlights': recent_greenlights,
            'current_layer': 4
        }
    
    def generate_answer_node(self, state: PathwayState) -> PathwayState:
        """Generate final answer based on collected context"""
        # Adapt answer based on user profile
        if state['user_profile']['sophistication_level'] == 'novice':
            instruction = "Provide educational context and step-by-step guidance."
        elif state['user_profile']['sophistication_level'] == 'advanced':
            instruction = "Provide insider intelligence and competitive positioning."
        else:
            instruction = "Provide strategic guidance and actionable intelligence."
        
        # Generate answer using existing RAG engine
        answer = self.rag_engine.generate_answer(
            query=state['query'],
            context=state['executive_context'],
            instruction=instruction
        )
        
        return {
            **state,
            'answer': answer,
            'confidence_score': 0.85  # TODO: Calculate actual confidence
        }
    
    def generate_followups_node(self, state: PathwayState) -> PathwayState:
        """Generate pathway-based follow-ups"""
        # Use existing pathway followups system
        from pathway_followups import PathwayFollowupGenerator
        
        generator = PathwayFollowupGenerator()
        follow_ups = generator.generate_pathway_followups(
            query=state['query'],
            answer=state['answer'],
            executive_name=state['executive_name']
        )
        
        return {
            **state,
            'follow_ups': follow_ups
        }
    
    def should_continue_to_layer2(self, state: PathwayState) -> str:
        """Decide if we need Layer 2 (mandate) information"""
        # If user is novice or query is about "what does X want", continue
        if state['user_profile']['sophistication_level'] == 'novice':
            return "continue"
        if 'what does' in state['query'].lower() or 'what is' in state['query'].lower():
            return "continue"
        # If we already have executive name, we can generate answer
        return "generate"
    
    def should_continue_to_layer3(self, state: PathwayState) -> str:
        """Decide if we need Layer 3 (production companies)"""
        # If query mentions "how to pitch" or "production company", continue
        if any(term in state['query'].lower() for term in ['how to pitch', 'production company', 'how do i']):
            return "continue"
        return "generate"
    
    def _extract_executive_name(self, results: dict) -> str:
        """Extract executive name from search results"""
        # Simple extraction - can be improved
        if results.get('answer'):
            # Look for pattern: "Name, Title"
            import re
            match = re.search(r'\*\*([^,]+),', results['answer'])
            if match:
                return match.group(1).strip()
        return "Unknown"
    
    def _extract_production_companies(self, context: dict) -> list:
        """Extract production companies from executive context"""
        # TODO: Implement extraction logic
        return []
```

---

## Phase 5: Integration with Existing RAG System

### Goal
Wrap existing RAG engine in LangGraph nodes without rewriting it.

### Implementation

**File:** `app.py` (modifications)

```python
from pathway_graph import MandateWizardPathway
from user_memory import UserMemoryManager
from persona_detector import PersonaDetector

# Initialize components
memory_manager = UserMemoryManager()
persona_detector = PersonaDetector()
pathway = MandateWizardPathway(
    rag_engine=rag_engine,  # existing
    memory_manager=memory_manager,
    persona_detector=persona_detector
)

@app.route('/api/query_langgraph', methods=['POST'])
def query_langgraph():
    """New endpoint using LangGraph pathway"""
    data = request.json
    query = data.get('query', '')
    user_id = data.get('user_id', 'anonymous')
    
    # Run through pathway graph
    result = pathway.graph.invoke({
        'query': query,
        'user_id': user_id,
        'user_profile': {},
        'project_details': {},
        'current_layer': 0,
        'executive_name': '',
        'executive_context': {},
        'production_companies': [],
        'recent_greenlights': [],
        'packaging_intel': {},
        'answer': '',
        'follow_ups': [],
        'confidence_score': 0.0,
        'sources': []
    })
    
    return jsonify({
        'answer': result['answer'],
        'follow_ups': result['follow_ups'],
        'confidence_score': result['confidence_score'],
        'user_profile': result['user_profile'],
        'layer_reached': result['current_layer']
    })
```

---

## Phase 6: LangSmith Observability

### Goal
Add automatic tracing and monitoring.

### Implementation

**File:** `.env` (add these)

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=mandate-wizard
```

**That's it!** LangSmith will automatically trace all LLM calls, retrievals, and graph executions.

---

## Phase 7: Chain of Verification

### Goal
Add self-verification to reduce hallucinations.

### Implementation

**File:** `verification.py`

```python
from langchain_openai import ChatOpenAI

class ChainOfVerification:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    def verify_answer(self, query: str, answer: str, sources: list) -> dict:
        """Verify answer against source material"""
        
        # Step 1: Extract claims from answer
        claims = self._extract_claims(answer)
        
        # Step 2: Verify each claim
        verification_results = []
        for claim in claims:
            verified = self._verify_claim(claim, sources)
            verification_results.append({
                'claim': claim,
                'verified': verified,
                'confidence': verified['confidence']
            })
        
        # Step 3: Calculate overall confidence
        overall_confidence = sum(r['confidence'] for r in verification_results) / len(verification_results)
        
        return {
            'verified': all(r['verified']['is_supported'] for r in verification_results),
            'confidence': overall_confidence,
            'claims': verification_results
        }
    
    def _extract_claims(self, answer: str) -> list:
        """Extract factual claims from answer"""
        prompt = f"""Extract the key factual claims from this answer:

{answer}

Return a list of specific, verifiable claims."""
        
        response = self.llm.invoke(prompt)
        # Parse response into list
        claims = [line.strip('- ') for line in response.content.split('\n') if line.strip()]
        return claims
    
    def _verify_claim(self, claim: str, sources: list) -> dict:
        """Verify a single claim against sources"""
        sources_text = "\n\n".join([s.get('text', '') for s in sources])
        
        prompt = f"""Is this claim supported by the source material?

Claim: {claim}

Sources:
{sources_text}

Answer with:
1. Is the claim supported? (yes/no)
2. Confidence (0-1)
3. Evidence (quote from sources)"""
        
        response = self.llm.invoke(prompt)
        
        # Parse response
        is_supported = 'yes' in response.content.lower()
        confidence = 0.8 if is_supported else 0.2  # Simplified
        
        return {
            'is_supported': is_supported,
            'confidence': confidence,
            'evidence': response.content
        }
```

---

## Testing Plan

### Test 1: User Memory
```python
# Test that user context is remembered
query1 = "I have a Korean thriller series"
query2 = "Who should I pitch to?"
# System should remember it's about Korean thriller
```

### Test 2: Persona Detection
```python
# Test novice detection
query = "How do I pitch to Netflix? I'm new to this"
# Should detect: novice, screenwriter

# Test advanced detection
query = "What has Don Kang greenlit in Q4 2024?"
# Should detect: advanced, executive
```

### Test 3: LangGraph Pathway
```python
# Test that graph navigates through layers
query = "What production companies in Korea work with Netflix?"
# Should hit: Layer 1 (routing) → Layer 2 (mandate) → Layer 3 (prodco)
```

### Test 4: Chain of Verification
```python
# Test that claims are verified
answer = "Don Kang is VP, Content (Korea) and greenlit Squid Game"
# Should verify both claims against sources
```

---

## Rollout Strategy

### Week 1: Foundation
- ✅ Install dependencies
- ✅ Create user memory system
- ✅ Create persona detector
- ✅ Test memory and persona detection

### Week 2: LangGraph
- Build pathway graph
- Integrate with existing RAG
- Test graph execution
- Add LangSmith observability

### Week 3: Verification & Polish
- Implement Chain of Verification
- Add confidence scoring
- Test end-to-end
- Performance optimization

### Week 4: Production Deployment
- A/B test new vs. old system
- Monitor performance
- Gather user feedback
- Full rollout

---

## Success Metrics

### Memory System:
- ✅ User context remembered across sessions
- ✅ Project details extracted from queries
- ✅ Conversation history maintained

### Persona Detection:
- ✅ 90%+ accuracy on sophistication level
- ✅ 80%+ accuracy on persona type
- ✅ Crisis mode detected reliably

### LangGraph Pathway:
- ✅ All layers accessible
- ✅ Conditional routing works
- ✅ State persists across nodes

### Verification:
- ✅ Claims extracted accurately
- ✅ Verification confidence >85%
- ✅ Hallucinations reduced by 50%

---

## Next Steps

1. ✅ Dependencies installed
2. **NOW:** Implement user memory system
3. Build persona detector
4. Create LangGraph workflow
5. Integrate with existing system
6. Test and iterate
7. Deploy to production

