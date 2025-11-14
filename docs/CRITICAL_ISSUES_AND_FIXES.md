# Mandate Wizard: Critical Issues & Improvement Plan

**Date:** November 12, 2025  
**Status:** 🚨 URGENT - Major Quality Issues Identified  
**Source:** Real user conversation analysis

---

## 🔴 Critical Issue: No Conversational Context

### The Problem

**User conversation shows:**
1. Initial question: "Who should I pitch a documentary about police investigating tramadol in Saudi Arabia?"
2. Follow-up: "Are there other platforms interested in MENA content?"
3. Follow-up: "What other platforms are currently investing in MENA content?"
4. Follow-up: "What trends are emerging in viewer preferences for MENA content?"
5. Follow-up: "What are the key challenges in producing content for the MENA market?"

**System behavior:**
- ❌ Every answer mentions the **same two executives** (Nuha El Tayeb, Larry Tanz)
- ❌ Answers are nearly identical despite different questions
- ❌ No awareness of previous answers
- ❌ No attempt to avoid repetition
- ❌ Generic, non-specific information

### Root Cause

Looking at `pro_architecture/rag/engine.py`:

```python
def answer(self, question: str, user_email: str = None) -> Dict[str, Any]:
    t0 = time.time()
    intent = classify(question)
    docs = self.retrieve(question)  # ❌ Only uses current question
    entities = self.enrich_entities(docs)
    out = self.synthesize(question, docs, entities)  # ❌ No conversation history
```

**The engine has NO conversation memory:**
- No conversation history parameter
- No context from previous Q&A
- No tracking of what was already mentioned
- Each query is treated as completely independent

---

## 🔴 Critical Issue: Stale Data

**Evidence:** "Last updated: 2023-10-25" (2 years old!)

### The Problem

- Data is outdated
- No indication of freshness in the answer
- Users can't trust the information
- Automated updates not yet implemented

### Impact

- Wrong job titles
- Outdated relationships
- Missing recent projects
- Inaccurate contact information

---

## 🔴 Critical Issue: Poor Answer Quality

### The Problem

**Answers are:**
- Generic and vague
- Repetitive across follow-ups
- Missing specific details
- Not answering the actual question

**Example:**
- Q: "What other platforms are currently investing in MENA content?"
- A: Talks about Netflix (again) and mentions "other platforms" vaguely without naming them

**Should mention:**
- Amazon Prime Video
- Disney+
- Shahid (MBC)
- OSN+
- Specific investment amounts
- Recent deals/announcements

---

## 🔴 Critical Issue: No Conversational Intelligence

### Missing Capabilities

1. **No conversation history tracking**
2. **No context awareness**
3. **No repetition avoidance**
4. **No follow-up understanding**
5. **No progressive disclosure** (building on previous answers)

---

## 💡 Solution: Implement Conversational RAG

### Phase 1: Add Conversation Context (Week 1)

**Goal:** Make the system aware of conversation history

#### Changes Needed

**1. Update Engine API**

```python
# Current (broken)
def answer(self, question: str, user_email: str = None) -> Dict[str, Any]:
    ...

# New (with context)
def answer(
    self, 
    question: str, 
    conversation_history: List[Dict] = None,
    user_email: str = None
) -> Dict[str, Any]:
    ...
```

**2. Add Conversation Context to Retrieval**

```python
def retrieve(self, question: str, conversation_history: List[Dict] = None) -> List[Dict[str, Any]]:
    # Rewrite query with conversation context
    contextualized_query = self._contextualize_query(question, conversation_history)
    
    # Retrieve with context
    qs = self._multi_query(contextualized_query)
    ...
```

**3. Add Context to Synthesis**

```python
def synthesize(
    self, 
    question: str, 
    docs: List[Dict[str, Any]], 
    entities: List[Dict[str, Any]],
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    # Build context-aware prompt
    context = self._build_conversation_context(conversation_history)
    prompt = USER_TEMPLATE.format(
        question=question, 
        snippets=...,
        conversation_context=context  # NEW
    )
    ...
```

**4. Update System Prompt**

```python
SYSTEM_WITH_CONTEXT = """You are Mandate Wizard, an AI assistant specializing in the film and television industry.

IMPORTANT CONVERSATION RULES:
1. You are in a multi-turn conversation with the user
2. Review the conversation history before answering
3. DO NOT repeat information you've already provided
4. Build on previous answers progressively
5. If asked a follow-up, focus on NEW information
6. Reference previous answers when relevant ("As I mentioned earlier...")
7. If you've already named specific people/companies, provide DIFFERENT examples in follow-ups

CONVERSATION HISTORY:
{conversation_history}

CURRENT QUESTION:
{question}

RETRIEVED INFORMATION:
{snippets}

Provide a comprehensive answer that:
- Acknowledges the conversation context
- Avoids repeating previous information
- Provides new, specific details
- References previous answers when relevant
"""
```

---

### Phase 2: Query Rewriting with Context (Week 1)

**Goal:** Transform follow-up questions into standalone queries

#### Implementation

```python
def _contextualize_query(self, question: str, conversation_history: List[Dict]) -> str:
    """
    Rewrite follow-up questions to include conversation context.
    
    Example:
    History: "Who should I pitch a documentary about MENA content?"
    Follow-up: "What other platforms are interested?"
    Rewritten: "What streaming platforms besides Netflix are interested in MENA content?"
    """
    if not conversation_history or len(conversation_history) == 0:
        return question
    
    # Use LLM to rewrite query with context
    from openai import OpenAI
    client = OpenAI()
    
    history_text = "\n".join([
        f"Q: {turn['question']}\nA: {turn['answer'][:500]}"
        for turn in conversation_history[-3:]  # Last 3 turns
    ])
    
    prompt = f"""Given this conversation history:

{history_text}

The user now asks: "{question}"

Rewrite this question as a standalone query that includes necessary context from the conversation history.
Only output the rewritten question, nothing else.

Rewritten question:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Fast and cheap
        temperature=0,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )
    
    rewritten = response.choices[0].message.content.strip()
    return rewritten
```

---

### Phase 3: Repetition Detection & Avoidance (Week 2)

**Goal:** Detect when we're about to repeat information

#### Implementation

```python
def _check_repetition(self, answer: str, conversation_history: List[Dict]) -> Dict[str, Any]:
    """
    Check if the answer repeats information from previous turns.
    
    Returns:
    {
        "is_repetitive": bool,
        "repeated_entities": List[str],
        "repeated_facts": List[str]
    }
    """
    if not conversation_history:
        return {"is_repetitive": False, "repeated_entities": [], "repeated_facts": []}
    
    # Extract entities from current answer
    current_entities = self._extract_entities(answer)
    
    # Extract entities from previous answers
    previous_entities = set()
    for turn in conversation_history:
        previous_entities.update(self._extract_entities(turn.get("answer", "")))
    
    # Check overlap
    repeated = current_entities & previous_entities
    
    return {
        "is_repetitive": len(repeated) / max(len(current_entities), 1) > 0.7,  # 70% overlap
        "repeated_entities": list(repeated),
        "repeated_facts": []
    }

def _regenerate_with_exclusions(
    self, 
    question: str, 
    docs: List[Dict], 
    entities: List[Dict],
    exclude_entities: List[str]
) -> Dict[str, Any]:
    """
    Regenerate answer excluding already-mentioned entities.
    """
    exclusion_note = f"\n\nIMPORTANT: You have already mentioned these people/companies in previous answers: {', '.join(exclude_entities)}. DO NOT mention them again. Focus on providing NEW examples and information."
    
    # Add exclusion to prompt
    prompt = USER_TEMPLATE.format(question=question, snippets=...) + exclusion_note
    
    # Generate new answer
    ...
```

---

### Phase 4: Progressive Disclosure (Week 2)

**Goal:** Build answers progressively across conversation

#### Implementation

```python
def _determine_answer_strategy(self, question: str, conversation_history: List[Dict]) -> str:
    """
    Determine how to structure the answer based on conversation depth.
    
    Strategies:
    - "overview": First question, provide broad overview
    - "deep_dive": Follow-up, go deeper on specific aspect
    - "expand": Follow-up, provide additional examples
    - "clarify": Follow-up asking for clarification
    """
    if not conversation_history:
        return "overview"
    
    # Analyze question type
    if any(word in question.lower() for word in ["other", "more", "additional", "else"]):
        return "expand"
    elif any(word in question.lower() for word in ["how", "why", "explain"]):
        return "deep_dive"
    elif any(word in question.lower() for word in ["what do you mean", "clarify", "explain"]):
        return "clarify"
    else:
        return "overview"

def synthesize(
    self, 
    question: str, 
    docs: List[Dict], 
    entities: List[Dict],
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    
    # Determine strategy
    strategy = self._determine_answer_strategy(question, conversation_history)
    
    # Adjust prompt based on strategy
    if strategy == "expand":
        instruction = "Provide NEW examples and information that you haven't mentioned before."
    elif strategy == "deep_dive":
        instruction = "Go deeper into the details, providing more context and explanation."
    elif strategy == "clarify":
        instruction = "Clarify your previous answer, providing more specific details."
    else:
        instruction = "Provide a comprehensive overview."
    
    # Add to prompt
    ...
```

---

### Phase 5: Conversation State Management (Week 3)

**Goal:** Track conversation state in database

#### Database Schema

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255),
    started_at TIMESTAMP DEFAULT NOW(),
    last_activity_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    turn_number INTEGER,
    question TEXT,
    answer TEXT,
    entities_mentioned TEXT[],
    context JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_turns_conversation ON conversation_turns(conversation_id, turn_number);
```

#### API Changes

```python
# New endpoint: Start conversation
POST /api/conversations
Response: {"conversation_id": "uuid"}

# Modified endpoint: Ask question
POST /api/answer
Body: {
    "question": "...",
    "conversation_id": "uuid"  # Optional, creates new if not provided
}

# New endpoint: Get conversation history
GET /api/conversations/{conversation_id}
Response: {
    "conversation_id": "uuid",
    "turns": [
        {"question": "...", "answer": "...", "timestamp": "..."},
        ...
    ]
}
```

---

## 📊 Implementation Plan

### Week 1: Core Conversational RAG

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Add conversation_history parameter | P0 | 4h | Backend |
| Implement query rewriting | P0 | 6h | Backend |
| Update system prompt | P0 | 2h | Backend |
| Add context to synthesis | P0 | 4h | Backend |
| Test with sample conversations | P0 | 4h | QA |

**Deliverable:** System can handle conversation context

### Week 2: Repetition Avoidance

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Implement repetition detection | P0 | 6h | Backend |
| Add entity extraction | P0 | 4h | Backend |
| Implement regeneration with exclusions | P0 | 6h | Backend |
| Add progressive disclosure | P1 | 6h | Backend |
| Test repetition avoidance | P0 | 4h | QA |

**Deliverable:** System avoids repeating information

### Week 3: Conversation State

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Create database schema | P0 | 2h | Backend |
| Implement conversation tracking | P0 | 8h | Backend |
| Add conversation API endpoints | P0 | 6h | Backend |
| Update frontend to use conversations | P1 | 8h | Frontend |
| Test end-to-end | P0 | 4h | QA |

**Deliverable:** Conversations persisted and tracked

### Week 4: Testing & Optimization

| Task | Priority | Effort | Owner |
|------|----------|--------|-------|
| Comprehensive conversation testing | P0 | 8h | QA |
| Performance optimization | P1 | 6h | Backend |
| Edge case handling | P1 | 6h | Backend |
| Documentation | P0 | 4h | Tech Writer |
| Production deployment | P0 | 4h | DevOps |

**Deliverable:** Production-ready conversational system

---

## 🎯 Success Metrics

### Before (Current State)

- ❌ 0% conversation context awareness
- ❌ High repetition rate (80%+ in follow-ups)
- ❌ Generic answers
- ❌ Low user satisfaction

### After (Target State)

- ✅ 100% conversation context awareness
- ✅ < 10% repetition rate
- ✅ Specific, contextual answers
- ✅ > 4.0/5.0 user satisfaction
- ✅ > 90% follow-up quality

---

## 💰 Cost Estimate

### Additional API Costs

| Component | Usage | Cost/Month |
|-----------|-------|------------|
| Query rewriting (GPT-4o-mini) | ~5,000 rewrites/month @ $0.0001 | $0.50 |
| Conversation context (tokens) | +200 tokens/query @ $0.01/1k | $10 |
| **TOTAL** | | **~$10/month** |

**Note:** Minimal cost increase, huge quality improvement.

---

## 🚀 Quick Win: Immediate Improvements

### Can Deploy Today (No Code Changes)

**1. Update System Prompt**
Add instructions to avoid repetition:
```
"If this is a follow-up question, review previous answers and provide NEW information."
```

**2. Increase Retrieval Diversity**
Adjust config to retrieve more diverse results:
```python
S.USE_MMR = True  # Maximum Marginal Relevance
S.MMR_LAMBDA = 0.7  # Balance relevance vs. diversity
```

**3. Add Freshness Warnings**
Update prompt to explicitly mention data age:
```
"Always mention when data was last updated, especially if > 6 months old."
```

---

## 📋 Next Steps

1. **Review this plan** - Get stakeholder approval
2. **Prioritize fixes** - Which to implement first?
3. **Allocate resources** - Assign engineers
4. **Start Week 1** - Core conversational RAG
5. **Test relentlessly** - Use real conversations

---

## 🔗 Related Documents

- `docs/testing_strategy.md` - Comprehensive testing plan
- `docs/option_c_automated_updates_plan.md` - Data freshness solution
- `pro_architecture/rag/engine.py` - Current RAG implementation

---

## ⚠️ Recommendation

**URGENT: Implement conversational RAG (Weeks 1-2) before launching to more users.**

The current system's lack of conversation awareness is a **critical quality issue** that will:
- Frustrate users
- Damage credibility
- Reduce adoption
- Generate negative feedback

**ROI:** 
- Effort: 40 hours (2 weeks)
- Cost: +$10/month
- Impact: Transforms user experience from "broken" to "intelligent"

**Let's fix this!** 🛠️
