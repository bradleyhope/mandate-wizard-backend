# Phase 2 Roadmap - Production-Grade Conversational RAG

**Timeline:** 6-8 weeks after Phase 1 deployment  
**Prerequisites:** 2-4 weeks of real user feedback from Phase 1

Based on ChatGPT 5 Pro recommendations and real user feedback.

---

## Overview

Phase 1 (Gemini-optimized) provides a **gold-standard conversational RAG** system. Phase 2 upgrades it to **production-grade** with learned intelligence, structured domain models, and verifiability.

**Key Upgrades:**
1. Mandate Graph (structured domain model)
2. Reward Model (learned quality scoring)
3. Candidate Generation (generate K, pick best)
4. Coverage Ledger (fine-grained entity tracking)
5. Verifiability (claims + evidence)

---

## Phase 2.1: Mandate Graph (Weeks 1-2)

### Goal
Replace free-text goals with structured domain model for better intent understanding.

### What to Build

**Mandate Graph Schema:**
```python
{
  "mandate": {
    "genre": "doc|scripted|unscripted",
    "region": "MENA|LatAm|Asia|Global",
    "format": "feature|series|short",
    "stage": "idea|treatment|deck|pilot|production"
  },
  "constraints": {
    "budget_band": "micro|low|mid|high",
    "timeline_quarter": "Q1|Q2|Q3|Q4",
    "rights_needed": ["theatrical", "streaming", "broadcast"]
  },
  "tactics": {
    "warm_intros": true|false,
    "festival_strategy": ["IDFA", "Sundance", "Cannes"],
    "pitch_materials": ["deck", "sizzle", "script"]
  },
  "success_metric": "meeting|LOI|deal|production"
}
```

**Implementation:**
1. Create `mandate_graph` table
2. Build intent parser (LLM-based)
3. Update goal inference to populate Mandate Graph
4. Use Mandate Graph for retrieval filtering

**Success Criteria:**
- 80%+ of conversations have complete Mandate Graph
- Retrieval precision improves by 15%+

---

## Phase 2.2: Reward Model (Weeks 3-4)

### Goal
Replace heuristic quality scoring with learned model trained on real user feedback.

### What to Build

**Data Collection (from Phase 1):**
- Collect 500+ conversation turns with user feedback
- Label high-quality vs. low-quality answers
- Extract features: specificity, actionability, etc.

**Model Training:**
```python
# Features
features = [
    'specificity_score',
    'actionability_score',
    'strategic_value_score',
    'context_awareness_score',
    'novelty_score',
    'turn_number',
    'entities_mentioned_count',
    'question_type',
    'response_strategy'
]

# Target
target = 'user_feedback_value'  # 0.0-1.0

# Train gradient boosting model
model = XGBRegressor()
model.fit(X_train, y_train)
```

**Integration:**
1. Replace `_calculate_quality()` with model inference
2. Use model to score candidate answers
3. Continuously retrain with new feedback

**Success Criteria:**
- Model R² > 0.70 on held-out data
- Positive feedback rate improves by 10%+

---

## Phase 2.3: Candidate Generation (Weeks 5-6)

### Goal
Generate multiple candidate answers and pick the best one (not just hope single generation is good).

### What to Build

**Candidate Generation:**
```python
def generate_candidates(context, k=4):
    candidates = []
    
    # Variant 1: Breadth-first
    candidates.append(generate(
        prompt_variant="breadth",
        retrieval_mix="diverse",
        temperature=0.8
    ))
    
    # Variant 2: Depth-first
    candidates.append(generate(
        prompt_variant="depth",
        retrieval_mix="focused",
        temperature=0.6
    ))
    
    # Variant 3: Strategic
    candidates.append(generate(
        prompt_variant="strategic",
        retrieval_mix="high_level",
        temperature=0.7
    ))
    
    # Variant 4: Actionable
    candidates.append(generate(
        prompt_variant="actionable",
        retrieval_mix="tactical",
        temperature=0.7
    ))
    
    return candidates
```

**Selection:**
```python
# Score all candidates with reward model
scores = [reward_model.score(c, context) for c in candidates]

# Select Pareto-best (highest score, lowest repetition)
best = select_pareto_best(candidates, scores, repetition_scores)
```

**Success Criteria:**
- Best-of-4 beats single generation 70%+ of the time
- Average quality score improves by 0.05+

---

## Phase 2.4: Coverage Ledger (Week 7)

### Goal
Track fine-grained coverage of each entity (not just presence/absence).

### What to Build

**Coverage Ledger Schema:**
```python
coverage_ledger = {
    "Nuha El Tayeb": {
        "facts_covered": [
            "Director of MENA Content at Netflix",
            "Based in Dubai",
            "Joined Netflix in 2020"
        ],
        "attributes_covered": {
            "role": True,
            "company": True,
            "location": True,
            "tenure": True,
            "slate_examples": False,  # Not yet covered
            "taste_profile": False,
            "contact_vector": False
        },
        "evidence": ["doc_123", "doc_456"],
        "depth_score": 0.43  # 3/7 attributes covered
    }
}
```

**Schema Slots (per entity type):**
- **Person**: role, company, tenure, slate_examples, taste_profile, timing, contact_vector
- **Company**: focus_areas, budget_range, recent_deals, decision_makers, submission_process
- **Platform**: content_strategy, target_audience, commissioning_process, key_contacts

**Repetition Cost Function:**
```python
def repetition_cost(curr, prev, coverage_ledger):
    overlap = set(curr_entities) & set(prev_entities)
    
    # Allow purposeful repetition for comparisons
    purposeful = {e for e in overlap if reuse_map.get(e) == "compare"}
    
    # Penalize redundant repetition (same facts)
    redundant = []
    for entity in (overlap - purposeful):
        curr_facts = extract_facts(curr, entity)
        prev_facts = coverage_ledger[entity]['facts_covered']
        if len(set(curr_facts) & set(prev_facts)) > 0.7 * len(curr_facts):
            redundant.append(entity)
    
    return len(redundant) / len(curr_entities)
```

**Success Criteria:**
- Repetition detection precision improves by 25%+
- False positives (penalizing valid comparisons) < 5%

---

## Phase 2.5: Verifiability (Week 8)

### Goal
Track which claims are backed by evidence and which are hallucinated.

### What to Build

**Claim Extraction:**
```python
def extract_claims(answer):
    # Use LLM to extract factual claims
    prompt = f"""Extract all factual claims from this answer:

{answer}

List each claim as a separate bullet point."""
    
    claims = llm.generate(prompt).split('\n')
    return [c.strip('- ') for c in claims if c.strip()]
```

**Evidence Linking:**
```python
def link_evidence(claim, retrieved_docs):
    # Find which documents support this claim
    evidence = []
    for doc in retrieved_docs:
        if semantic_similarity(claim, doc['content']) > 0.75:
            evidence.append({
                'doc_id': doc['id'],
                'snippet': doc['content'][:200],
                'confidence': similarity_score
            })
    return evidence
```

**Verifiability Score:**
```python
verifiability = len(claims_with_evidence) / len(total_claims)
```

**Delta Renderer:**
```markdown
## What's New This Turn
- Nadim Dada at Amazon Prime Video (new executive)
- Track record: 15+ MENA titles, 8 documentaries

## Action You Can Take Now
1. Prepare 10-page deck + 3-min sizzle
2. Lead with compelling protagonist
3. Reach out via warm intro (MBC alumni)

## Evidence Used
- [Amazon MENA Strategy, 2024] (doc_789)
- [Interview with Nadim, Variety, March 2024] (doc_456)
```

**Success Criteria:**
- Verifiability score > 0.80 (80%+ of claims backed by evidence)
- User trust rating improves by 15%+

---

## Implementation Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Mandate Graph schema | Database tables, intent parser |
| 2 | Mandate Graph integration | Updated goal inference, retrieval filtering |
| 3 | Reward model data prep | Labeled dataset (500+ examples) |
| 4 | Reward model training | Trained model, API integration |
| 5 | Candidate generation | 4-variant generation, Pareto selection |
| 6 | Candidate integration | A/B testing, performance validation |
| 7 | Coverage Ledger | Schema completion tracking, repetition v2 |
| 8 | Verifiability | Claim extraction, evidence linking, delta renderer |

---

## Success Metrics

### Phase 1 Baseline (from real data)
- Average quality score: 0.75
- Repetition rate: 12%
- Positive feedback rate: 72%
- Verifiability: Not tracked

### Phase 2 Targets
- Average quality score: **0.85** (+0.10)
- Repetition rate: **< 5%** (-7%)
- Positive feedback rate: **85%** (+13%)
- Verifiability: **> 80%** (new metric)
- Intent understanding: **90%** (Mandate Graph completion)

---

## Cost Analysis

### Phase 1 Costs
- Database: $7/mo (Render PostgreSQL)
- LLM calls: ~$10/mo (embeddings + generation)
- **Total: ~$17/mo**

### Phase 2 Additional Costs
- Reward model inference: +$3/mo (XGBoost, fast)
- Candidate generation: +$20/mo (4x LLM calls)
- Claim extraction: +$5/mo (additional LLM calls)
- **Total: ~$45/mo** (+$28/mo)

**ROI:** If Phase 2 improves conversion by 15%, the $28/mo is negligible.

---

## Risks & Mitigations

### Risk 1: Candidate generation too slow
**Mitigation:** 
- Run candidates in parallel
- Cache common patterns
- Use faster model for candidates, best model for final

### Risk 2: Reward model overfits to early feedback
**Mitigation:**
- Continuous retraining with new data
- Regularization (L2, dropout)
- A/B test model vs. heuristics

### Risk 3: Coverage Ledger too complex
**Mitigation:**
- Start with simple schema (5-7 slots per entity type)
- Expand based on real usage patterns
- Use LLM to auto-populate schema

### Risk 4: Verifiability slows down responses
**Mitigation:**
- Run claim extraction async (after response sent)
- Use for analytics, not blocking
- Cache evidence links

---

## Decision Points

### After Week 2 (Mandate Graph)
**Go/No-Go:** Does Mandate Graph improve retrieval precision by 15%+?
- **Go:** Continue to reward model
- **No-Go:** Simplify Mandate Graph or revert to free-text

### After Week 4 (Reward Model)
**Go/No-Go:** Does reward model beat heuristics on held-out data?
- **Go:** Continue to candidate generation
- **No-Go:** Improve feature engineering or collect more data

### After Week 6 (Candidate Generation)
**Go/No-Go:** Does best-of-4 beat single generation 70%+ of time?
- **Go:** Continue to coverage ledger
- **No-Go:** Reduce to best-of-2 or optimize prompt variants

---

## Phase 3 (Future)

After Phase 2, consider:
- **Multi-turn planning** (plan entire conversation upfront)
- **Proactive suggestions** (anticipate next question)
- **Personalization** (adapt to user preferences)
- **Multi-modal** (images, videos in answers)
- **Real-time updates** (trigger updates when new data available)

---

## Getting Started

### Prerequisites
1. **Phase 1 deployed and running**
2. **2-4 weeks of user feedback collected**
3. **500+ conversation turns with ratings**

### First Steps
1. Analyze Phase 1 feedback data
2. Identify top pain points
3. Prioritize Phase 2 features based on impact
4. Start with Mandate Graph (highest ROI)

### Resources Needed
- 1 ML engineer (reward model training)
- 1 backend engineer (integration)
- 2 weeks of user feedback data
- $500 budget for LLM API calls (testing)

---

## Questions?

See main project README or contact the team.
