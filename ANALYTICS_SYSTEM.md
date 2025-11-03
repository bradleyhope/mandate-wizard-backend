# Deep Chat Analytics System - Mandate Wizard

**Date:** October 28, 2025  
**Status:** IMPLEMENTED

---

## Overview

Comprehensive analytics system that tracks every user interaction, analyzes patterns, and provides deep insights into what's working and what's not.

---

## Features

### 1. Query Tracking
**Every query is logged with:**
- Timestamp
- User email
- Question and answer
- Response time
- Success/failure status
- Intent classification
- Session ID
- Subscription status
- Estimated tokens and cost

### 2. User Journey Analysis
**Per-user tracking:**
- First and last query dates
- Total queries across all sessions
- Success/failure rates
- Average response time
- Total tokens and costs
- Favorite topics
- Session details

### 3. Pattern Extraction
**Automatic detection of:**
- **Topics:** greenlights, executives, deals, mandates, talent, production, genre, strategy
- **Intents:** Classified by query type
- **Keywords:** Frequency analysis of significant words
- **Entities:** People, companies, projects mentioned

### 4. Performance Metrics
**System health monitoring:**
- Response time tracking (last 1000 queries)
- Success rate over time
- Error type classification
- Performance trends

### 5. Engagement Analysis
**User behavior insights:**
- Session lengths
- Queries per session
- Drop-off rates
- Follow-up patterns
- Single vs multi-query sessions

---

## API Endpoints

### Get Summary Statistics
```http
GET /api/analytics/summary?days=7
```

**Response:**
```json
{
  "summary": {
    "period": "Last 7 days",
    "total_queries": 150,
    "successful_queries": 145,
    "failed_queries": 5,
    "success_rate": "96.7%",
    "unique_users": 25,
    "avg_queries_per_user": 6.0,
    "avg_response_time": "2.34s",
    "total_cost": "$3.00",
    "avg_cost_per_query": "$0.0200",
    "top_topics": [
      ["greenlights", 45],
      ["executives", 32],
      ["deals", 28]
    ],
    "top_keywords": [
      ["netflix", 67],
      ["greenlight", 45],
      ["executive", 32]
    ]
  },
  "success": true
}
```

### Get User Journey
```http
GET /api/analytics/user/user@example.com
```

**Response:**
```json
{
  "journey": {
    "email": "user@example.com",
    "first_query_date": "2025-10-21T10:00:00",
    "last_query_date": "2025-10-28T15:30:00",
    "total_queries": 42,
    "total_sessions": 8,
    "avg_queries_per_session": 5.25,
    "session_details": [
      {
        "session_id": "session_1",
        "query_count": 7,
        "duration": 1200,
        "topics": {
          "greenlights": 4,
          "executives": 3
        }
      }
    ],
    "query_timeline": [...]
  },
  "success": true
}
```

### Get Pattern Analysis
```http
GET /api/analytics/patterns
```

**Response:**
```json
{
  "patterns": {
    "topics": {
      "greenlights": 145,
      "executives": 98,
      "deals": 76,
      "mandates": 65
    },
    "intents": {
      "HYBRID": 120,
      "PINECONE": 45,
      "NEO4J": 30
    },
    "keywords": {
      "netflix": 234,
      "greenlight": 145,
      "executive": 98
    }
  },
  "success": true
}
```

---

## Data Structure

### Query Record
```json
{
  "timestamp": "2025-10-28T15:30:00",
  "email": "user@example.com",
  "question": "What greenlights happened this week?",
  "answer": "This week Netflix greenlighted...",
  "question_length": 35,
  "answer_length": 450,
  "response_time": 2.34,
  "success": true,
  "error": null,
  "intent": "PINECONE",
  "session_id": "session_123",
  "subscription_status": "paid",
  "tokens_used": 2000,
  "cost": 0.02
}
```

### User Statistics
```json
{
  "first_query": "2025-10-21T10:00:00",
  "last_query": "2025-10-28T15:30:00",
  "total_queries": 42,
  "successful_queries": 40,
  "failed_queries": 2,
  "total_tokens": 84000,
  "total_cost": 0.84,
  "avg_response_time": 2.15,
  "favorite_topics": {
    "greenlights": 15,
    "executives": 12,
    "deals": 8
  },
  "sessions": {
    "session_1": 7,
    "session_2": 5
  }
}
```

---

## Insights Available

### 1. What's Working
- **Most popular topics** - What users ask about most
- **High success rate queries** - What the system answers well
- **Engaged users** - Who uses the system most
- **Valuable sessions** - Multi-query sessions indicate engagement

### 2. What's Not Working
- **Failed queries** - What questions the system can't answer
- **Drop-off points** - Where users abandon sessions
- **Slow responses** - Queries with high response times
- **Error patterns** - Common failure modes

### 3. User Behavior
- **Query patterns** - When users ask questions
- **Topic preferences** - What different users care about
- **Session length** - How long users engage
- **Follow-up rate** - How often users ask multiple questions

### 4. Cost Analysis
- **Cost per user** - Who's expensive to serve
- **Cost per topic** - What queries cost most
- **Cost trends** - Is spending increasing?
- **ROI metrics** - Value per dollar spent

---

## Use Cases

### Product Development
- **Feature prioritization** - Build what users ask for most
- **Quality improvement** - Fix what fails most often
- **UX optimization** - Reduce drop-off, increase engagement

### Business Intelligence
- **User segmentation** - Identify power users vs casual users
- **Pricing strategy** - Understand value delivered
- **Growth metrics** - Track engagement over time

### Content Strategy
- **Topic coverage** - What's missing from the database
- **Content quality** - What answers work best
- **Update priorities** - What needs refreshing

### Support & Operations
- **Error monitoring** - Catch issues early
- **Performance tracking** - Maintain SLAs
- **Capacity planning** - Predict resource needs

---

## Privacy & Compliance

### Data Retention
- Queries stored for 90 days by default
- User can request data deletion (GDPR)
- Aggregated stats retained indefinitely

### Data Protection
- Email addresses hashed for privacy
- Queries not shared with third parties
- Secure storage with access controls

### Transparency
- Users can view their own analytics
- Clear data usage policy
- Opt-out available

---

## Monitoring Dashboard (Future)

**Planned features:**
- Real-time query stream
- Live success rate graph
- Cost tracking dashboard
- User engagement heatmap
- Topic trend visualization
- Error alert system

---

## Files

- `chat_analytics.py` - Analytics engine
- `analytics_endpoints.py` - API endpoints (integrated into app.py)
- `chat_analytics.json` - Data storage
- `ANALYTICS_SYSTEM.md` - This documentation

---

## Next Steps

1. **Build visualization dashboard** - Web UI for analytics
2. **Add alerting** - Email notifications for issues
3. **Implement A/B testing** - Test improvements
4. **Add recommendations** - Suggest related queries
5. **Export reports** - Weekly/monthly summaries

---

## Conclusion

The Deep Chat Analytics System provides comprehensive visibility into user behavior, system performance, and business metrics. It enables data-driven decisions about product development, content strategy, and resource allocation.

**Key Benefits:**
- ✅ Understand what users want
- ✅ Identify and fix problems quickly
- ✅ Optimize costs and performance
- ✅ Measure engagement and value
- ✅ Make data-driven decisions

