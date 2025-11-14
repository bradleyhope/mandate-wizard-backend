# Mandate Wizard: Comprehensive Testing Strategy

**Date:** November 12, 2025  
**Purpose:** Relentlessly test the system to identify strengths, weaknesses, and improvement opportunities  
**Approach:** Persona-based testing across all query types

---

## Testing Philosophy

**Goal:** Stress test the system like real users would, not just happy-path testing.

**Principles:**
1. **Relentless** - Test hundreds of queries, not dozens
2. **Realistic** - Use actual user personas and scenarios
3. **Adversarial** - Try to break it, find edge cases
4. **Comprehensive** - Cover all entity types and query patterns
5. **Measurable** - Track metrics for every response

---

## User Personas

### Persona 1: The Executive Assistant

**Name:** Sarah  
**Role:** Executive Assistant to a studio head  
**Goals:** Quick, accurate answers about people and their current roles  
**Pain Points:** Needs to know who's who RIGHT NOW, not 6 months ago

**Typical Queries:**
- "Who is the current CEO of Netflix?"
- "What is Chris Mansolillo working on now?"
- "Who reports to Ted Sarandos?"
- "Is Jane Doe still at HBO?"
- "What's the contact info for [person]?"

**Success Criteria:**
- ✅ Answers are current (< 30 days old)
- ✅ Contact info is accurate
- ✅ Relationships are up-to-date
- ✅ Response time < 3 seconds

---

### Persona 2: The Development Executive

**Name:** Marcus  
**Role:** Development Executive at a production company  
**Goals:** Research people for potential collaborations  
**Pain Points:** Needs deep context, not just surface info

**Typical Queries:**
- "Tell me about Chris Mansolillo's career background"
- "What type of projects does [person] typically work on?"
- "Who has [person] worked with in the past?"
- "What's [person]'s track record with streaming shows?"
- "Find me showrunners who've worked on procedural dramas"

**Success Criteria:**
- ✅ Comprehensive career history
- ✅ Project details and credits
- ✅ Collaboration patterns
- ✅ Genre/format preferences
- ✅ Track record analysis

---

### Persona 3: The Journalist

**Name:** Alex  
**Role:** Entertainment journalist  
**Goals:** Quick fact-checking and background research  
**Pain Points:** Needs to verify information quickly and accurately

**Typical Queries:**
- "Verify: Is [person] the CEO of [company]?"
- "When did [person] join [company]?"
- "What shows has [person] produced?"
- "Who are the key executives at [company]?"
- "What's the latest news about [person]?"

**Success Criteria:**
- ✅ Factually accurate
- ✅ Sources cited
- ✅ Dates and timelines correct
- ✅ No speculation, just facts
- ✅ Confidence indicators

---

### Persona 4: The Investor/Analyst

**Name:** David  
**Role:** Media industry analyst  
**Goals:** Understand company structures and leadership  
**Pain Points:** Needs org charts, reporting structures, strategic moves

**Typical Queries:**
- "Who are the top executives at Netflix?"
- "What's the org structure of [company]'s content division?"
- "Who reports to whom at [company]?"
- "What companies has [person] led?"
- "Track [person]'s career moves over the last 5 years"

**Success Criteria:**
- ✅ Org structure clarity
- ✅ Reporting relationships
- ✅ Career trajectory analysis
- ✅ Strategic context
- ✅ Timeline accuracy

---

### Persona 5: The Networker

**Name:** Lisa  
**Role:** Talent manager  
**Goals:** Find connections and warm introductions  
**Pain Points:** Needs to know who knows whom

**Typical Queries:**
- "Who can introduce me to [person]?"
- "What's the connection between [person A] and [person B]?"
- "Who has worked with both [person A] and [person B]?"
- "Find people in my network who know [person]"
- "What projects connect [person A] and [person B]?"

**Success Criteria:**
- ✅ Relationship mapping
- ✅ Mutual connections
- ✅ Collaboration history
- ✅ Network visualization
- ✅ Introduction paths

---

## Query Categories

### Category 1: Entity Lookup (Simple)

**Pattern:** "Who is [person]?" or "What is [company]?"

**Test Queries:**
1. "Who is Chris Mansolillo?"
2. "What is Netflix?"
3. "Tell me about HBO Max"
4. "Who is Ted Sarandos?"
5. "What is Succession?"

**Evaluation Criteria:**
- ✅ Correct entity identified
- ✅ Current information
- ✅ Key facts included (role, company, projects)
- ✅ Response completeness (1-5 scale)
- ✅ Response time < 2 seconds

---

### Category 2: Relationship Queries

**Pattern:** "Who does [person] work with?" or "What's the relationship between X and Y?"

**Test Queries:**
1. "Who does Chris Mansolillo work with?"
2. "What's the relationship between Ted Sarandos and Netflix?"
3. "Who reports to [person]?"
4. "What projects connect [person A] and [person B]?"
5. "Find people who've worked with both [person A] and [person B]"

**Evaluation Criteria:**
- ✅ Relationships correctly identified
- ✅ Relationship types accurate (boss, colleague, collaborator)
- ✅ Current vs. past relationships distinguished
- ✅ Strength/frequency of relationship
- ✅ Supporting evidence provided

---

### Category 3: Career/History Queries

**Pattern:** "What has [person] worked on?" or "Tell me about [person]'s career"

**Test Queries:**
1. "What projects has Chris Mansolillo worked on?"
2. "Tell me about [person]'s career history"
3. "What's [person]'s track record?"
4. "How long has [person] been at [company]?"
5. "What was [person]'s previous job?"

**Evaluation Criteria:**
- ✅ Comprehensive career timeline
- ✅ Projects listed with dates
- ✅ Career progression clear
- ✅ Major achievements highlighted
- ✅ Current status accurate

---

### Category 4: Search/Discovery Queries

**Pattern:** "Find me [type of person]" or "Who are the [role] at [company]?"

**Test Queries:**
1. "Find me showrunners who work on procedural dramas"
2. "Who are the top executives at Netflix?"
3. "Find development executives at streaming companies"
4. "Who are the producers of crime shows?"
5. "Find people who've worked on both film and TV"

**Evaluation Criteria:**
- ✅ Relevant results returned
- ✅ Results ranked by relevance
- ✅ Sufficient results (not too few, not too many)
- ✅ Filtering/faceting works
- ✅ Results diversity

---

### Category 5: Complex/Multi-Hop Queries

**Pattern:** Queries requiring multiple reasoning steps

**Test Queries:**
1. "Who are the people Chris Mansolillo has worked with who are now at Netflix?"
2. "Find executives who moved from traditional TV to streaming in the last 2 years"
3. "What do [person A] and [person B] have in common?"
4. "Who has worked on shows similar to [show]?"
5. "Find people who've transitioned from development to production"

**Evaluation Criteria:**
- ✅ Multi-step reasoning successful
- ✅ All constraints satisfied
- ✅ Logic transparent
- ✅ Results make sense
- ✅ No hallucinations

---

### Category 6: Edge Cases & Adversarial

**Pattern:** Queries designed to break the system

**Test Queries:**
1. "Who is [completely made-up person]?" (should say "not found")
2. "What is [person]'s phone number?" (should handle privacy)
3. "Tell me about [person] from 1985" (before their career)
4. "Who is the CEO of [defunct company]?"
5. "What is [ambiguous name]?" (multiple people with same name)
6. "[gibberish query]" (should handle gracefully)
7. "Tell me EVERYTHING about [person]" (should handle scope)
8. "[extremely long query with 200 words]" (should handle length)

**Evaluation Criteria:**
- ✅ Graceful failure handling
- ✅ Clear "not found" messages
- ✅ Privacy respected
- ✅ Ambiguity resolved
- ✅ No crashes or errors
- ✅ No hallucinations

---

## Testing Methodology

### Phase 1: Baseline Testing (100 queries)

**Goal:** Establish baseline performance across all categories

**Approach:**
1. 20 queries per category (Categories 1-5)
2. Mix of easy, medium, hard queries
3. Track all metrics
4. Identify patterns

**Metrics to Track:**
- Response time (seconds)
- Answer quality (1-5 scale)
- Factual accuracy (correct/incorrect)
- Completeness (1-5 scale)
- Relevance (1-5 scale)
- Confidence score (from system)
- Sources cited (count)
- Hallucinations (yes/no)

---

### Phase 2: Persona Testing (50 queries per persona)

**Goal:** Test like real users would

**Approach:**
1. 50 queries per persona (250 total)
2. Realistic scenarios
3. Follow-up questions
4. Track persona-specific success criteria

**Metrics to Track:**
- Persona satisfaction (1-5 scale)
- Task completion (yes/no)
- Time to answer
- Number of follow-ups needed
- Frustration points

---

### Phase 3: Adversarial Testing (100 queries)

**Goal:** Break the system, find edge cases

**Approach:**
1. Intentionally difficult queries
2. Ambiguous queries
3. Out-of-scope queries
4. Malformed queries
5. Privacy-sensitive queries

**Metrics to Track:**
- Error handling quality
- Graceful degradation
- Security issues
- Privacy leaks
- System crashes

---

### Phase 4: Load Testing (1000 queries)

**Goal:** Test performance at scale

**Approach:**
1. Automated query generation
2. Parallel requests
3. Sustained load
4. Peak load

**Metrics to Track:**
- Response time under load
- Error rate
- Throughput (queries/second)
- Resource usage
- Cache hit rate

---

## Evaluation Rubric

### Answer Quality (1-5 scale)

**5 - Excellent**
- Comprehensive and accurate
- All key information included
- Well-structured and clear
- Sources cited
- No errors or hallucinations

**4 - Good**
- Accurate and mostly complete
- Minor information gaps
- Clear and understandable
- Some sources cited
- No significant errors

**3 - Acceptable**
- Basically accurate
- Some important information missing
- Could be clearer
- Few sources cited
- Minor errors possible

**2 - Poor**
- Partially accurate
- Significant information gaps
- Unclear or confusing
- No sources cited
- Some errors

**1 - Unacceptable**
- Inaccurate or wrong
- Missing critical information
- Confusing or misleading
- No sources
- Major errors or hallucinations

---

## Test Execution Plan

### Setup

1. **Authentication:** Get API key for testing
2. **Environment:** Use production backend
3. **Tools:** 
   - Python test script
   - Results tracking spreadsheet
   - Screen recording for complex scenarios
4. **Team:** Assign testers to personas

### Execution Schedule

**Week 1:**
- Day 1-2: Baseline testing (100 queries)
- Day 3-4: Persona testing (250 queries)
- Day 5: Analysis and initial findings

**Week 2:**
- Day 1-2: Adversarial testing (100 queries)
- Day 3: Load testing (1000 queries)
- Day 4-5: Analysis and recommendations

### Deliverables

1. **Test Results Database** - All queries, responses, and scores
2. **Analysis Report** - Strengths, weaknesses, patterns
3. **Improvement Plan** - Prioritized recommendations
4. **Demo Video** - Key findings and examples

---

## Success Metrics

### Targets

| Metric | Target | Baseline | Goal |
|--------|--------|----------|------|
| Average Quality Score | > 4.0 | TBD | 4.5 |
| Factual Accuracy | > 95% | TBD | 98% |
| Response Time | < 3s | TBD | < 2s |
| Task Completion | > 90% | TBD | 95% |
| Hallucination Rate | < 2% | TBD | < 1% |
| User Satisfaction | > 4.0 | TBD | 4.5 |

---

## Known Areas to Investigate

### 1. Data Freshness
- How old is the data?
- Are recent job changes reflected?
- Are new projects included?

### 2. Relationship Accuracy
- Are org charts correct?
- Are collaborations accurate?
- Are relationships current?

### 3. Search Quality
- Are search results relevant?
- Is ranking good?
- Are filters working?

### 4. Answer Completeness
- Is enough context provided?
- Are sources cited?
- Is confidence indicated?

### 5. Edge Case Handling
- How are "not found" cases handled?
- How is ambiguity resolved?
- How are privacy concerns addressed?

---

## Next Steps

1. **Get authentication credentials** for testing
2. **Set up test environment** and tools
3. **Recruit testers** (or use automated testing)
4. **Execute Phase 1** (baseline testing)
5. **Analyze results** and iterate

**Ready to start testing!** 🧪
