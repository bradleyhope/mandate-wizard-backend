# Mandate Wizard - System Architecture

**Version:** 1.1 (Database-Only Architecture)  
**Date:** October 23, 2025  
**Status:** Production Ready ✓

---

## Overview

The Mandate Wizard web application uses a **database-only architecture** where all entity data is stored and queried from cloud databases at runtime. There are no local JSON files loaded into memory during query processing.

---

## Architecture Diagram

```
User Query
    ↓
Flask Web Server (app.py)
    ↓
HybridRAG Engine (hybridrag_engine_pinecone.py)
    ↓
┌─────────────────────────────────────────┐
│  1. Intent Classification               │
│     - ROUTING / STRATEGIC / COMPARATIVE │
│  2. Attribute Extraction                │
│     - Region, Format, Genre             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  3. Parallel Database Queries           │
│     ├─ Neo4j Graph Query                │
│     │  (Executives by region/genre)     │
│     └─ Pinecone Vector Query            │
│        (Semantic similarity search)     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  4. Context Fusion                      │
│     - Merge graph + vector results      │
│     - Deduplicate entities              │
│     - Rank by relevance                 │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  5. LLM Answer Generation               │
│     - GPT-4.1-mini                      │
│     - Context-aware prompting           │
│     - Structured answer format          │
└─────────────────────────────────────────┘
    ↓
Structured Answer (JSON)
    ↓
Web Interface / API Response
```

---

## Data Flow

### Storage Layer (Offline)

**Entity Extraction Pipeline:**
```
Source Research
    ↓
LLM Extraction (GPT-4.1-mini)
    ↓
JSON Entity Files (local, temporary)
    ↓
sync_all_entities.py
    ↓
┌─────────────────────────────────────────┐
│  Upload to Databases                    │
│  ├─ Pinecone: Vector embeddings         │
│  └─ Neo4j: Graph nodes & relationships  │
└─────────────────────────────────────────┘
```

**Key Point:** JSON files are only used during extraction/upload. Once uploaded to databases, they are no longer needed for query processing.

### Query Layer (Runtime)

**Query Processing:**
```
User Query
    ↓
HybridRAG Engine
    ↓
┌─────────────────────────────────────────┐
│  Direct Database Queries                │
│  ├─ Pinecone: Semantic search           │
│  └─ Neo4j: Structured queries           │
└─────────────────────────────────────────┘
    ↓
Context Assembly
    ↓
LLM Answer Generation
    ↓
Structured Answer
```

**Key Point:** No local JSON files are loaded or accessed during query processing. All data comes from Pinecone and Neo4j.

---

## Database Architecture

### Pinecone Vector Database

**Purpose:** Semantic similarity search across all entity content

**Structure:**
- **Index Name:** `netflix-mandate-wizard`
- **Dimensions:** 384 (all-MiniLM-L6-v2 embeddings)
- **Total Vectors:** 1,044+ vectors
- **Metadata:** entity_id, entity_type, name, text chunk

**Query Pattern:**
```python
# Generate query embedding
query_embedding = embedding_model.encode(question)

# Search Pinecone
results = index.query(
    vector=query_embedding,
    top_k=10,
    include_metadata=True
)
```

**Use Cases:**
- Semantic search for mandates and strategies
- Finding similar content priorities
- Contextual information retrieval
- Fallback when graph search returns no results

### Neo4j Graph Database

**Purpose:** Structured queries for executives by attributes

**Structure:**
- **Node Type:** Person (executives)
- **Properties:** name, current_title, region, bio, mandate, reports_to
- **Indexes:** region (27 regions), current_title
- **Total Nodes:** 165+ executives

**Query Pattern:**
```cypher
MATCH (p:Person)
WHERE p.region = 'mena'
RETURN p.entity_id, p.name, p.current_title, 
       p.region, p.bio, p.mandate, p.reports_to
```

**Use Cases:**
- Finding executives by region (MENA, Korea, UK, etc.)
- Routing queries to specific people
- Building organizational context (reports_to relationships)
- Regional-first pitch routing

---

## Key Architectural Decisions

### 1. Database-Only at Runtime

**Decision:** Query Pinecone and Neo4j directly, no local JSON files

**Rationale:**
- ✅ Scalability: Databases handle millions of entities
- ✅ Consistency: Single source of truth
- ✅ Performance: Optimized database queries
- ✅ Simplicity: No file system dependencies
- ✅ Deployment: Easier to deploy (no data files to sync)

**Trade-offs:**
- ⚠️ Network dependency: Requires database connectivity
- ⚠️ Latency: ~500ms for Pinecone queries (acceptable)

### 2. Hybrid Retrieval (Graph + Vector)

**Decision:** Combine Neo4j structured queries with Pinecone semantic search

**Rationale:**
- ✅ Precision: Neo4j for exact attribute matches (region, genre)
- ✅ Recall: Pinecone for semantic similarity and context
- ✅ Flexibility: Handles both structured and unstructured queries
- ✅ Redundancy: Fallback if one database fails

**Implementation:**
```python
# Parallel retrieval
graph_results = self.graph_search(question, attributes, intent)
vector_results = self.vector_search(question, top_k=10)

# Fusion
context = self.fuse_context(graph_results, vector_results, intent)
```

### 3. Regional-First Routing

**Decision:** Prioritize regional executives for regional projects

**Rationale:**
- ✅ Accuracy: Regional teams handle regional content
- ✅ Process: Aligns with Netflix's internal workflow
- ✅ User expectation: Industry professionals expect regional routing

**Implementation:**
- Detect region keywords in query
- Query Neo4j for executives in that region
- Prioritize regional director/manager in answer
- Mention US executives only as escalation path

### 4. Intent-Based Prompting

**Decision:** Different system prompts for ROUTING vs STRATEGIC queries

**Rationale:**
- ✅ Answer quality: Different intents need different answer formats
- ✅ Accuracy: Prevents routing when user wants strategy
- ✅ Consistency: Ensures predictable answer structure

**Implementation:**
```python
if intent == 'STRATEGIC':
    system_prompt = """Provide strategic information, list mandates..."""
else:  # ROUTING
    system_prompt = """Recommend specific person to pitch to..."""
```

---

## Performance Characteristics

### Query Latency Breakdown

| Component | Latency | Notes |
|-----------|---------|-------|
| Intent Classification | <1ms | Keyword matching |
| Attribute Extraction | <1ms | Regex patterns |
| Neo4j Graph Query | <100ms | Indexed queries |
| Pinecone Vector Query | ~500ms | Semantic search |
| Context Fusion | <10ms | In-memory operations |
| LLM Generation | ~3.5s | GPT-4.1-mini |
| **Total** | **~4.2s** | End-to-end |

### Scalability

**Current Scale:**
- 769 entities extracted
- 1,044 vectors in Pinecone
- 165 executives in Neo4j
- 27 regions indexed

**Target Scale (Multi-Streamer):**
- 5,000-8,000 entities
- 10,000+ vectors in Pinecone
- 1,000+ executives in Neo4j
- 50+ regions

**Scalability Assessment:**
- ✅ Pinecone: Scales to millions of vectors
- ✅ Neo4j: Scales to millions of nodes
- ✅ LLM: Stateless, horizontally scalable
- ⚠️ Cost: LLM API costs scale with query volume

---

## Deployment Architecture

### Current Deployment (Development)

```
Manus Sandbox
    ├─ Flask Development Server (port 5000)
    ├─ Python 3.11 runtime
    └─ Environment variables (OPENAI_API_KEY)
        ↓
External Services
    ├─ Pinecone (cloud)
    ├─ Neo4j (cloud)
    └─ OpenAI API (cloud)
```

### Recommended Production Deployment

```
Load Balancer
    ↓
Gunicorn (4 workers)
    ↓
Flask Application
    ├─ Redis Cache (optional, for common queries)
    └─ Environment variables
        ↓
External Services
    ├─ Pinecone (cloud)
    ├─ Neo4j (cloud)
    └─ OpenAI API (cloud)
```

**Production Recommendations:**
1. Use Gunicorn instead of Flask dev server
2. Add Redis caching for common queries
3. Move credentials to environment variables
4. Add monitoring and logging
5. Set up health check endpoints

---

## Security Considerations

### Current State

**Credentials:** Hardcoded in `app.py` (development only)

**Risks:**
- ⚠️ Exposed in code repository
- ⚠️ No rotation mechanism
- ⚠️ No access control

### Production Recommendations

**1. Environment Variables:**
```bash
export PINECONE_API_KEY="..."
export NEO4J_URI="..."
export NEO4J_USER="..."
export NEO4J_PASSWORD="..."
export OPENAI_API_KEY="..."
```

**2. Secrets Management:**
- Use AWS Secrets Manager, Azure Key Vault, or similar
- Rotate credentials regularly
- Audit access logs

**3. API Security:**
- Add authentication (API keys, OAuth)
- Rate limiting per user/IP
- Input validation and sanitization

---

## Monitoring & Observability

### Recommended Metrics

**Application Metrics:**
- Query latency (p50, p95, p99)
- Query success rate
- Intent classification accuracy
- Database query latency

**Database Metrics:**
- Pinecone query latency
- Neo4j query latency
- Database connection pool usage
- Error rates

**Business Metrics:**
- Queries per day
- Top query types (ROUTING vs STRATEGIC)
- Most queried regions
- Most queried executives

### Logging Strategy

**Current:** Basic stdout logging to `/tmp/mandate_wizard.log`

**Recommended:**
- Structured JSON logging
- Log aggregation (ELK, Datadog, etc.)
- Query analytics (question, intent, latency, success)
- Error tracking (Sentry, Rollbar, etc.)

---

## Future Architecture Enhancements

### 1. Multi-Streamer Support

**Current:** Netflix only  
**Target:** Netflix, Amazon, Apple, Max, Disney+

**Changes Needed:**
- Add `streamer` field to Neo4j nodes
- Add streamer detection to attribute extraction
- Filter queries by streamer
- Update UI with streamer selector

### 2. Response Caching

**Current:** No caching  
**Target:** Redis cache for common queries

**Benefits:**
- Reduce LLM API costs
- Improve response time for common queries
- Reduce database load

**Implementation:**
```python
# Check cache first
cache_key = f"query:{hash(question)}"
cached_answer = redis.get(cache_key)
if cached_answer:
    return cached_answer

# Generate answer
answer = engine.query(question)

# Cache for 1 hour
redis.setex(cache_key, 3600, answer)
```

### 3. Query Analytics Dashboard

**Current:** No analytics  
**Target:** Real-time dashboard

**Metrics:**
- Query volume over time
- Top executives queried
- Regional distribution
- Intent classification breakdown
- Average latency

---

## Conclusion

The Mandate Wizard uses a **database-only architecture** that queries Pinecone and Neo4j directly at runtime, with no local JSON files. This design provides scalability, consistency, and simplicity, while maintaining excellent query performance (~4 seconds end-to-end).

The hybrid retrieval approach (graph + vector) ensures both precision and recall, while intent-based prompting delivers high-quality, context-appropriate answers for routing and strategic queries.

---

**For deployment instructions, see:** `DEPLOYMENT_GUIDE.md`  
**For API documentation, see:** `README.md`  
**For issue fixes, see:** `FIX_SUMMARY.md`

