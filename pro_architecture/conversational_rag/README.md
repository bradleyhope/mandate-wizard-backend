# Conversational RAG - Phase 1

**Gold-standard conversational RAG system** with semantic similarity, multi-layer memory, and progressive improvement.

## Features

✅ **Semantic Repetition Detection** - Uses embeddings (not entity overlap) to detect repetitive answers  
✅ **Multi-Layer Memory** - Working/short-term/long-term memory for context  
✅ **Comparative Question Handling** - Properly handles "compare X vs Y" questions  
✅ **Query Rewriting** - Rewrites vague follow-ups into self-contained queries  
✅ **Progressive Improvement** - Each answer aims to be better than the last  
✅ **Quality Scoring** - 5-dimensional quality metrics  
✅ **User Feedback Collection** - Tracks thumbs up/down, ratings, comments  
✅ **Auto-Regeneration** - Regenerates if answer is too repetitive (>0.85 similarity)

## Architecture

```
ConversationalRAG (main orchestrator)
├── ConversationStore (database access)
├── ConversationManager (strategy planning)
└── ProgressiveEngine (answer generation)
```

## API Endpoints

### Start Conversation
```bash
POST /api/conversational/start
{
  "session_id": "optional",
  "initial_goal": "optional"
}
```

### Process Query
```bash
POST /api/conversational/query
{
  "conversation_id": "uuid",
  "query": "Who should I pitch to at Netflix?"
}
```

### Add Feedback
```bash
POST /api/conversational/feedback
{
  "conversation_id": "uuid",
  "turn_number": 1,
  "feedback_type": "thumbs_up",
  "feedback_value": 1.0
}
```

### Get Conversation
```bash
GET /api/conversational/conversation/{conversation_id}
```

### Get Stats
```bash
GET /api/conversational/conversation/{conversation_id}/stats
```

## Database Schema

Requires PostgreSQL with `pgvector` extension for semantic similarity.

**Tables:**
- `conversations` - Conversation metadata
- `conversation_turns` - Individual turns with embeddings
- `conversation_state` - Multi-layer memory
- `entity_coverage` - Entity tracking
- `user_feedback` - Feedback collection

## Migration

```bash
cd pro_architecture/conversational_rag
export DATABASE_URL="postgresql://..."
./migrate_schema.sh
```

## Configuration

Requires:
- PostgreSQL with pgvector extension
- OpenAI API key (for embeddings)
- LLM client (for generation)
- RAG engine (for retrieval)

## Thresholds

- **Semantic Repetition**: 0.85 (regenerate if higher)
- **Max Regeneration Attempts**: 2
- **Recent Turns Context**: 5 turns
- **Entity Coverage Limit**: 20 entities per turn

## Quality Metrics

Each answer is scored on:
1. **Specificity** (0-1) - Names, numbers, concrete details
2. **Actionability** (0-1) - Action verbs, steps, recommendations
3. **Strategic Value** (0-1) - Insights, reasoning, "why"
4. **Context Awareness** (0-1) - References to conversation
5. **Novelty** (0-1) - Inverse of semantic repetition

**Overall Score** = weighted average of above

## Example Flow

```python
# Start conversation
conversation_id = rag.start_conversation("user123", "session456")

# Turn 1
result = rag.process_query(conversation_id, "Who should I pitch to at Netflix?")
# Answer: "Nuha El Tayeb, Director of MENA Content at Netflix..."
# Quality: 0.75, Repetition: 0.0

# Turn 2
result = rag.process_query(conversation_id, "What other platforms?")
# Rewritten: "What streaming platforms besides Netflix are interested in MENA content?"
# Answer: "Amazon Prime Video (Nadim Dada), Disney+ (Hend Baghdady)..."
# Quality: 0.82, Repetition: 0.12 (NEW entities, not Netflix again!)

# Turn 3
result = rag.process_query(conversation_id, "Tell me more about Nadim")
# Answer: "Nadim Dada is VP of Content at Amazon Prime Video MENA. Track record: 15+ titles..."
# Quality: 0.88, Repetition: 0.08 (deeper, more strategic)
```

## Phase 2 Roadmap

After collecting real user feedback, Phase 2 will add:
- **Mandate Graph** (structured domain model)
- **Reward Model** (learned quality scoring)
- **Candidate Generation** (generate K candidates, pick best)
- **Coverage Ledger** (fine-grained entity tracking)
- **Verifiability** (claims + evidence tracking)

## Testing

```bash
# Run unit tests
pytest conversational_rag/tests/

# Test API endpoints
curl -X POST http://localhost:5000/api/conversational/start \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123"}'
```

## Monitoring

Track these metrics:
- Average quality score per conversation
- Repetition rate (% of turns with >0.85 similarity)
- Positive feedback rate
- Unique entities covered per conversation
- Average conversation length

## Support

For issues or questions, see main project README.
