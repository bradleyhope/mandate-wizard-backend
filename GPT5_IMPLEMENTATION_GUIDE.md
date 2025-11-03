# GPT-5 Implementation Guide for Mandate Wizard

**Date**: October 25, 2025  
**Purpose**: Proper implementation of GPT-5 Responses API for Mandate Wizard V5

---

## Executive Summary

GPT-5 uses a **different API** than GPT-4. The key differences:

| Feature | GPT-4 (Chat Completions) | GPT-5 (Responses API) |
|:--------|:------------------------|:---------------------|
| Endpoint | `/v1/chat/completions` | `/v1/responses` |
| Streaming | ✅ Supported | ❌ Not supported |
| Reasoning | Manual (prompting) | Built-in (`reasoning.effort`) |
| Web Search | Manual | Built-in (`tools: [{ type: "web_search" }]`) |
| Multi-turn | Manual context | `previous_response_id` |

---

## Current Implementation Issues

### ❌ What We're Doing Wrong

```python
# WRONG: Using Chat Completions API for GPT-5
response = self.llm.chat.completions.create(
    model="gpt-5",  # GPT-5 model
    messages=[...],  # Chat Completions format
    stream=True  # Streaming not supported!
)
```

**Problems**:
1. GPT-5 doesn't support Chat Completions API properly
2. Streaming doesn't work (returns error or hangs)
3. Missing GPT-5's built-in reasoning and web search features

---

## ✅ Correct GPT-5 Implementation

### 1. Using the Responses API

```python
import requests
import os

def query_gpt5(prompt, context, reasoning_effort="medium", use_web_search=False):
    """
    Proper GPT-5 Responses API implementation
    
    Args:
        prompt: User's question
        context: Retrieved context from RAG
        reasoning_effort: "low", "medium", or "high"
        use_web_search: Enable real-time web search
    
    Returns:
        Complete response text
    """
    
    # Build the request
    payload = {
        "model": "gpt-5",
        "input": f"{prompt}\\n\\nContext:\\n{context}",
        "reasoning": {
            "effort": reasoning_effort
        }
    }
    
    # Add web search if needed
    if use_web_search:
        payload["tools"] = [{"type": "web_search"}]
    
    # Make the API call
    response = requests.post(
        'https://api.openai.com/v1/responses',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}'
        },
        json=payload,
        timeout=60  # GPT-5 can take longer with high reasoning
    )
    
    if response.status_code != 200:
        raise Exception(f"GPT-5 API error: {response.status_code} - {response.text}")
    
    result = response.json()
    return result['output_text']
```

### 2. Simulating Streaming for UX

Since GPT-5 doesn't support streaming, we simulate it client-side:

```python
def query_with_simulated_streaming(prompt, context):
    """
    Query GPT-5 and simulate streaming by chunking the response
    """
    # Step 1: Show status
    yield {'type': 'status', 'message': 'Generating answer with GPT-5...'}
    
    # Step 2: Get complete response from GPT-5
    full_answer = query_gpt5(prompt, context, reasoning_effort="medium")
    
    # Step 3: Simulate streaming by sending word-by-word
    words = full_answer.split(' ')
    for i, word in enumerate(words):
        content = (' ' if i > 0 else '') + word
        yield {'type': 'chunk', 'content': content}
        # Optional: Add small delay for smoother effect
        # time.sleep(0.01)
    
    # Step 4: Send completion signal
    yield {'type': 'done'}
```

### 3. Reasoning Effort Guidelines

For Mandate Wizard, choose reasoning effort based on query type:

| Query Type | Reasoning Effort | Rationale |
|:-----------|:----------------|:----------|
| ROUTING | `medium` | Need to analyze context and provide detailed recommendations |
| STRATEGIC | `medium` | Synthesizing multiple mandates requires moderate reasoning |
| FACTUAL_QUERY | `low` | Simple fact retrieval, minimal reasoning needed |
| COMPARISON | `medium` to `high` | Comparing executives/strategies requires deeper analysis |

```python
def get_reasoning_effort(intent):
    """Map query intent to appropriate reasoning effort"""
    effort_map = {
        'ROUTING': 'medium',
        'STRATEGIC': 'medium',
        'FACTUAL_QUERY': 'low',
        'COMPARISON': 'high',
        'PROCEDURAL': 'low'
    }
    return effort_map.get(intent, 'medium')  # Default to medium
```

### 4. Adding Web Search for Real-Time Mandates

GPT-5 can search the web for the latest mandate information:

```python
def query_with_web_search(prompt, context, search_focus=None):
    """
    Use GPT-5's web search to get latest mandate information
    
    Args:
        prompt: User's question
        context: RAG context (from our database)
        search_focus: Optional - guide web search (e.g., "past 30 days")
    """
    
    # Enhance prompt to guide web search
    enhanced_prompt = f"""
{prompt}

Use web search to find the most recent information (past 30 days) about:
- Recent interviews and quotes
- New project announcements
- Strategy changes
- Executive moves

Combine web search results with the provided context for a comprehensive answer.

Context from our database:
{context}
"""
    
    payload = {
        "model": "gpt-5",
        "input": enhanced_prompt,
        "reasoning": {"effort": "high"},  # High effort for research
        "tools": [{"type": "web_search"}]
    }
    
    response = requests.post(
        'https://api.openai.com/v1/responses',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}'
        },
        json=payload,
        timeout=90  # Longer timeout for web search
    )
    
    result = response.json()
    return result['output_text']
```

**When to use web search**:
- User asks about "recent" or "latest" mandates
- Query mentions specific time periods ("this month", "Q4 2025")
- Executive information might be outdated
- User explicitly requests current information

### 5. Multi-Turn Conversations with `previous_response_id`

For follow-up questions, reuse reasoning context:

```python
def query_with_context_reuse(prompt, previous_response_id=None):
    """
    Use previous_response_id to maintain conversation context efficiently
    """
    payload = {
        "model": "gpt-5",
        "input": prompt,
        "reasoning": {"effort": "medium"}
    }
    
    # Reuse previous reasoning if available
    if previous_response_id:
        payload["previous_response_id"] = previous_response_id
    
    response = requests.post(
        'https://api.openai.com/v1/responses',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}'
        },
        json=payload
    )
    
    result = response.json()
    return result['output_text'], result['id']  # Return response_id for next turn
```

---

## Implementation Checklist

### Phase 1: Basic GPT-5 Integration
- [ ] Replace Chat Completions API calls with Responses API
- [ ] Implement proper error handling for Responses API
- [ ] Add reasoning effort selection based on query intent
- [ ] Test with all query types (ROUTING, STRATEGIC, FACTUAL_QUERY)

### Phase 2: Simulated Streaming
- [ ] Implement word-by-word chunking for smooth UX
- [ ] Add status updates during GPT-5 processing
- [ ] Test streaming simulation with various response lengths
- [ ] Optimize chunk size for best UX

### Phase 3: Web Search Integration
- [ ] Add web search for queries mentioning "recent" or "latest"
- [ ] Implement time-based search filtering
- [ ] Combine web search results with RAG context
- [ ] Add source citations from web search

### Phase 4: Multi-Turn Optimization
- [ ] Store `response_id` for each query
- [ ] Pass `previous_response_id` for follow-up questions
- [ ] Test token savings and latency improvements
- [ ] Implement session management for conversation history

---

## Code Migration Guide

### Before (Chat Completions API)
```python
stream = self.llm.chat.completions.create(
    model="gpt-5",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    stream=True,
    max_completion_tokens=2000
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        yield {'type': 'chunk', 'content': chunk.choices[0].delta.content}
```

### After (Responses API)
```python
import requests

# Get complete response
response = requests.post(
    'https://api.openai.com/v1/responses',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}'
    },
    json={
        'model': 'gpt-5',
        'input': f"{system_prompt}\\n\\n{user_prompt}",
        'reasoning': {'effort': 'medium'}
    }
)

full_answer = response.json()['output_text']

# Simulate streaming
words = full_answer.split(' ')
for i, word in enumerate(words):
    content = (' ' if i > 0 else '') + word
    yield {'type': 'chunk', 'content': content}
```

---

## Error Handling

### Common Errors and Solutions

**Error: "Invalid API endpoint"**
- **Cause**: Using Chat Completions endpoint for GPT-5
- **Solution**: Use `/v1/responses` instead of `/v1/chat/completions`

**Error: "Streaming is not supported"**
- **Cause**: Trying to use `stream=True` with GPT-5
- **Solution**: Remove streaming, simulate client-side

**Error: "Authentication failed"**
- **Cause**: API key expired or incorrect
- **Solution**: Use Manus-provided `OPENAI_API_KEY` environment variable

**Error: "Timeout"**
- **Cause**: GPT-5 with high reasoning effort can take 30-60 seconds
- **Solution**: Increase timeout to 90 seconds, show status updates

**Error: "Rate limit exceeded"**
- **Cause**: Too many requests
- **Solution**: Implement request queuing, add retry logic with exponential backoff

---

## Performance Optimization

### Token Usage

| Reasoning Effort | Avg Reasoning Tokens | Total Cost Multiplier |
|:----------------|:--------------------|:---------------------|
| `low` | 200-500 | 1.1x |
| `medium` | 500-1500 | 1.3x |
| `high` | 1500-5000+ | 2-3x |

**Optimization strategies**:
1. Use `low` effort for simple queries (FACTUAL_QUERY)
2. Use `medium` effort by default (good balance)
3. Only use `high` effort for complex research or comparisons
4. Use `previous_response_id` to avoid repeating reasoning

### Latency

| Configuration | Avg Latency |
|:-------------|:-----------|
| GPT-5 low effort, no web search | 3-5 seconds |
| GPT-5 medium effort, no web search | 5-10 seconds |
| GPT-5 high effort, no web search | 10-20 seconds |
| GPT-5 medium effort, with web search | 15-30 seconds |
| GPT-5 high effort, with web search | 30-60 seconds |

**Optimization strategies**:
1. Show detailed status updates for long-running queries
2. Cache common queries (e.g., popular executives)
3. Pre-fetch data for example questions
4. Use lower reasoning effort when possible

---

## Testing Plan

### Unit Tests
- [ ] Test Responses API connection
- [ ] Test reasoning effort levels
- [ ] Test web search integration
- [ ] Test error handling

### Integration Tests
- [ ] Test with all query types
- [ ] Test multi-turn conversations
- [ ] Test with/without web search
- [ ] Test simulated streaming

### Performance Tests
- [ ] Measure latency for each reasoning effort level
- [ ] Measure token usage
- [ ] Test under load (concurrent requests)
- [ ] Test timeout handling

---

## Rollout Strategy

### Phase 1: Development (Current)
- Implement Responses API in development environment
- Test with sample queries
- Validate error handling

### Phase 2: Staging
- Deploy to staging environment
- Run comprehensive test suite
- Gather performance metrics

### Phase 3: Production
- Gradual rollout (10% → 50% → 100%)
- Monitor error rates and latency
- Collect user feedback

---

## Resources

- [GPT-5 Best Practices Guide](./GPT5_BEST_PRACTICES.md)
- [OpenAI Responses API Documentation](https://platform.openai.com/docs/api-reference/responses)
- [Manus AI Environment Variables](https://docs.manus.im/environment)

---

**Next Steps**:
1. Review this guide
2. Implement Phase 1 (Basic GPT-5 Integration)
3. Test thoroughly
4. Deploy to staging
5. Gather feedback and iterate

