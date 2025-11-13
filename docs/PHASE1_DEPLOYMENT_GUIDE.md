# Phase 1 Conversational RAG - Deployment Guide

## Prerequisites

1. **PostgreSQL with pgvector extension**
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Environment Variables**
   ```bash
   DATABASE_URL=postgresql://user:pass@host:port/db
   OPENAI_API_KEY=sk-...
   ```

3. **Python Dependencies**
   ```bash
   pip install pgvector psycopg2-binary openai numpy
   ```

## Deployment Steps

### Step 1: Database Migration

```bash
cd pro_architecture/conversational_rag
export DATABASE_URL="your_database_url"
./migrate_schema.sh
```

This will create:
- `conversations` table
- `conversation_turns` table (with vector columns)
- `conversation_state` table
- `entity_coverage` table
- `user_feedback` table
- Helper functions and triggers
- Analytics views

### Step 2: Verify Installation

```bash
# Check if pgvector extension is installed
psql "$DATABASE_URL" -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check if tables were created
psql "$DATABASE_URL" -c "\dt" | grep conversation
```

### Step 3: Deploy to Render

The code is already integrated into `app.py`. When you push to GitHub, Render will auto-deploy.

```bash
git push origin master
```

### Step 4: Verify Deployment

```bash
# Check health
curl https://mandate-wizard-backend.onrender.com/api/conversational/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "conversational_rag",
#   "version": "1.0.0-phase1"
# }
```

## Testing

### Test 1: Start Conversation

```bash
curl -X POST https://mandate-wizard-backend.onrender.com/api/conversational/start \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{
    "session_id": "test_session_123",
    "initial_goal": "Find the right person to pitch my MENA documentary"
  }'
```

Expected response:
```json
{
  "conversation_id": "uuid-here",
  "message": "Conversation started successfully"
}
```

### Test 2: Process Query

```bash
CONV_ID="uuid-from-step-1"

curl -X POST https://mandate-wizard-backend.onrender.com/api/conversational/query \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d "{
    \"conversation_id\": \"$CONV_ID\",
    \"query\": \"Who should I pitch to at Netflix?\"
  }"
```

Expected response:
```json
{
  "answer": "Nuha El Tayeb is the Director of MENA Content at Netflix...",
  "turn_number": 1,
  "quality": {
    "overall": 0.78,
    "specificity": 0.85,
    "actionability": 0.70,
    "strategic_value": 0.75,
    "context_awareness": 0.60,
    "novelty": 1.0
  },
  "repetition_score": 0.0,
  "metadata": {
    "question_type": "initial",
    "response_strategy": "strategic_advice",
    "rewritten_query": "Who should I pitch to at Netflix?",
    "entities_excluded": [],
    "entities_included": []
  }
}
```

### Test 3: Follow-up Query

```bash
curl -X POST https://mandate-wizard-backend.onrender.com/api/conversational/query \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d "{
    \"conversation_id\": \"$CONV_ID\",
    \"query\": \"What other platforms?\"
  }"
```

Expected:
- Answer mentions NEW platforms (Amazon, Disney+, etc.)
- Does NOT repeat Netflix/Nuha El Tayeb
- Higher quality score (progressive improvement)
- Low repetition score (<0.3)

### Test 4: Comparative Query

```bash
curl -X POST https://mandate-wizard-backend.onrender.com/api/conversational/query \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d "{
    \"conversation_id\": \"$CONV_ID\",
    \"query\": \"How does Netflix compare to Amazon for MENA content?\"
  }"
```

Expected:
- Answer compares BOTH Netflix AND Amazon
- Side-by-side comparison
- question_type: "compare"
- response_strategy: "compare"

### Test 5: Add Feedback

```bash
curl -X POST https://mandate-wizard-backend.onrender.com/api/conversational/feedback \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d "{
    \"conversation_id\": \"$CONV_ID\",
    \"turn_number\": 1,
    \"feedback_type\": \"thumbs_up\",
    \"feedback_value\": 1.0,
    \"comment\": \"Very helpful!\"
  }"
```

### Test 6: Get Stats

```bash
curl https://mandate-wizard-backend.onrender.com/api/conversational/conversation/$CONV_ID/stats \
  -H "X-User-ID: test_user"
```

Expected:
```json
{
  "total_turns": 3,
  "avg_quality_score": 0.82,
  "goal_achieved": false,
  "feedback": {
    "total_feedback": 1,
    "positive_rate": 1.0,
    "avg_rating": 1.0
  },
  "unique_entities_covered": 5,
  "top_entities": [
    {"name": "Nuha El Tayeb", "mentions": 1},
    {"name": "Nadim Dada", "mentions": 1},
    ...
  ]
}
```

## Monitoring

### Key Metrics to Track

1. **Quality Progression**
   ```sql
   SELECT conversation_id, turn_number, quality_score
   FROM conversation_turns
   ORDER BY conversation_id, turn_number;
   ```

2. **Repetition Rate**
   ```sql
   SELECT 
     AVG(CASE WHEN repetition_score > 0.85 THEN 1.0 ELSE 0.0 END) AS repetition_rate
   FROM conversation_turns
   WHERE turn_number > 1;
   ```

3. **Positive Feedback Rate**
   ```sql
   SELECT 
     COUNT(CASE WHEN feedback_value > 0.5 THEN 1 END)::FLOAT / COUNT(*) AS positive_rate
   FROM user_feedback;
   ```

4. **Average Conversation Length**
   ```sql
   SELECT AVG(total_turns) FROM conversations WHERE status = 'completed';
   ```

### Alerts

Set up alerts for:
- Repetition rate > 20% (should be < 10%)
- Average quality score < 0.70 (should be > 0.75)
- Positive feedback rate < 60% (should be > 75%)

## Troubleshooting

### Issue: "pgvector extension not found"

```bash
# Install pgvector on your PostgreSQL instance
# For Render PostgreSQL, contact support to enable pgvector
# For local development:
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

### Issue: "Embeddings taking too long"

- Check OpenAI API rate limits
- Consider caching embeddings
- Batch embedding requests

### Issue: "High repetition scores"

- Check if entities_to_exclude is working
- Verify semantic similarity threshold (should be 0.85)
- Check if regeneration is triggering

### Issue: "Low quality scores"

- Review prompt templates in `progressive_engine.py`
- Check if RAG retrieval is returning relevant documents
- Verify LLM temperature (should be 0.7)

## Rollback Plan

If issues arise:

1. **Disable conversational endpoints**
   ```python
   # In app.py, set:
   CONVERSATIONAL_RAG_AVAILABLE = False
   ```

2. **Revert to previous version**
   ```bash
   git revert HEAD
   git push origin master
   ```

3. **Keep database tables** (for future retry)
   - Tables won't interfere with existing functionality
   - Can retry deployment later

## Next Steps

After successful deployment:

1. **Collect user feedback** (2-4 weeks)
2. **Analyze conversation patterns**
3. **Identify improvement areas**
4. **Plan Phase 2 upgrades** (Mandate Graph, reward model, etc.)

## Support

For issues:
- Check logs: `https://dashboard.render.com/`
- Review database: `psql $DATABASE_URL`
- Test locally: `python app.py`

## Success Criteria

Phase 1 is successful if:
- ✅ Repetition rate < 15%
- ✅ Average quality score > 0.75
- ✅ Positive feedback rate > 70%
- ✅ No production errors
- ✅ Response time < 5s per query
