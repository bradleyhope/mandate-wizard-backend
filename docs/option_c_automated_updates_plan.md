# Option C: Automated Update System - Design & Implementation Plan

**Date:** November 12, 2025  
**Status:** Planning Phase  
**Foundation:** Pro Architecture (deployed ✅)

---

## Executive Summary

Build an intelligent, automated system that:
1. **Monitors demand** for entities in real-time
2. **Triggers updates** automatically for critical/high-demand entities
3. **Scrapes newsletters** to refresh stale data
4. **Syncs across all systems** (PostgreSQL, Pinecone, Neo4j)
5. **Invalidates caches** intelligently
6. **Learns and optimizes** over time

**Goal:** Transform Mandate Wizard from reactive to **proactive** - automatically keeping high-value data fresh without manual intervention.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTOMATED UPDATE SYSTEM                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
        ┌─────────────────────────────────────────┐
        │     1. DEMAND MONITOR (Scheduler)       │
        │  - Runs every hour                      │
        │  - Checks priority/critical endpoints   │
        │  - Identifies entities needing updates  │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
        ┌─────────────────────────────────────────┐
        │     2. UPDATE ORCHESTRATOR              │
        │  - Prioritizes update queue             │
        │  - Manages rate limits                  │
        │  - Coordinates scraping jobs            │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
        ┌─────────────────────────────────────────┐
        │     3. NEWSLETTER SCRAPER               │
        │  - Fetches latest newsletters           │
        │  - Extracts entity mentions             │
        │  - Parses structured data               │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
        ┌─────────────────────────────────────────┐
        │     4. DATA PROCESSOR                   │
        │  - Validates scraped data               │
        │  - Merges with existing data            │
        │  - Generates embeddings                 │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
        ┌─────────────────────────────────────────┐
        │     5. SYNC ENGINE                      │
        │  - Updates PostgreSQL                   │
        │  - Updates Pinecone vectors             │
        │  - Updates Neo4j relationships          │
        │  - Invalidates Redis cache              │
        └──────────────────┬──────────────────────┘
                           │
                           ↓
        ┌─────────────────────────────────────────┐
        │     6. NOTIFICATION SERVICE             │
        │  - Logs update completion               │
        │  - Sends alerts for critical updates    │
        │  - Tracks success/failure metrics       │
        └─────────────────────────────────────────┘
```

---

## Component 1: Demand Monitor

### Purpose
Continuously monitor entity demand and identify candidates for automated updates.

### Implementation

**File:** `pro_architecture/automation/demand_monitor.py`

```python
class DemandMonitor:
    """
    Monitors entity demand and triggers automated updates.
    
    Runs on schedule (hourly) to check for:
    - Critical entities (high demand + stale data)
    - Trending entities (recent spike in queries)
    - Scheduled updates (based on priority schedule)
    """
    
    def check_critical_entities(self) -> List[str]:
        """Get entities requiring immediate updates"""
        # Call /api/priority/critical
        # Return list of entity IDs
        
    def check_trending_entities(self) -> List[str]:
        """Get entities with recent query spikes"""
        # Call /api/analytics/demand/trending
        # Return list of entity IDs
        
    def get_scheduled_updates(self) -> List[str]:
        """Get entities scheduled for today's update batch"""
        # Call /api/priority/schedule
        # Return today's batch
        
    def run_check(self) -> Dict[str, List[str]]:
        """Run all checks and return update candidates"""
        return {
            'critical': self.check_critical_entities(),
            'trending': self.check_trending_entities(),
            'scheduled': self.get_scheduled_updates()
        }
```

### Configuration

```python
MONITOR_CONFIG = {
    'schedule': 'hourly',  # or cron expression
    'critical_threshold': 10,  # demand_score >= 10
    'stale_threshold_days': 30,
    'trending_window': '7d',
    'max_updates_per_run': 50
}
```

### Deployment
- **Platform:** Render Cron Job (free tier: 1 job/day, or Background Worker with scheduler)
- **Alternative:** GitHub Actions (runs on schedule)
- **Cost:** Free (if using GitHub Actions) or $7/mo (if using Render Background Worker)

---

## Component 2: Update Orchestrator

### Purpose
Manages the update queue, prioritizes work, and coordinates scraping jobs.

### Implementation

**File:** `pro_architecture/automation/update_orchestrator.py`

```python
class UpdateOrchestrator:
    """
    Orchestrates automated entity updates.
    
    Responsibilities:
    - Prioritize update queue
    - Manage rate limits
    - Coordinate scraping jobs
    - Track update status
    """
    
    def __init__(self):
        self.priority_engine = PriorityEngine()
        self.scraper = NewsletterScraper()
        self.sync_engine = SyncEngine()
        
    def prioritize_updates(self, candidates: Dict) -> List[Dict]:
        """
        Prioritize update candidates.
        
        Order:
        1. Critical entities (high demand + stale)
        2. Trending entities (recent spike)
        3. Scheduled entities (daily batch)
        """
        prioritized = []
        
        # Critical first
        for entity_id in candidates['critical']:
            prioritized.append({
                'entity_id': entity_id,
                'priority': 'CRITICAL',
                'reason': 'high_demand_stale'
            })
        
        # Trending second
        for entity_id in candidates['trending']:
            if entity_id not in [e['entity_id'] for e in prioritized]:
                prioritized.append({
                    'entity_id': entity_id,
                    'priority': 'HIGH',
                    'reason': 'trending'
                })
        
        # Scheduled third
        for entity_id in candidates['scheduled']:
            if entity_id not in [e['entity_id'] for e in prioritized]:
                prioritized.append({
                    'entity_id': entity_id,
                    'priority': 'MEDIUM',
                    'reason': 'scheduled'
                })
        
        return prioritized
    
    def process_update_queue(self, queue: List[Dict]):
        """
        Process update queue with rate limiting.
        """
        for item in queue:
            try:
                # Scrape data
                scraped_data = self.scraper.scrape_entity(item['entity_id'])
                
                # Process and sync
                if scraped_data:
                    self.sync_engine.sync_entity(
                        item['entity_id'],
                        scraped_data
                    )
                    
                    # Log success
                    self.log_update_success(item)
                else:
                    self.log_update_failure(item, 'no_data_found')
                    
            except Exception as e:
                self.log_update_failure(item, str(e))
                
            # Rate limiting
            time.sleep(2)  # 2 seconds between updates
```

### Rate Limiting Strategy

```python
RATE_LIMITS = {
    'newsletter_scraping': {
        'requests_per_minute': 30,
        'requests_per_hour': 500
    },
    'embedding_generation': {
        'requests_per_minute': 60,
        'requests_per_hour': 3000
    },
    'database_writes': {
        'batch_size': 10,
        'delay_between_batches': 1  # second
    }
}
```

---

## Component 3: Newsletter Scraper

### Purpose
Scrape newsletters to extract fresh entity data.

### Implementation

**File:** `pro_architecture/automation/newsletter_scraper.py`

```python
class NewsletterScraper:
    """
    Scrapes newsletters for entity updates.
    
    Sources:
    - The Ankler
    - Puck News
    - Deadline Hollywood
    - Variety
    - Hollywood Reporter
    """
    
    def __init__(self):
        self.sources = [
            {'name': 'ankler', 'url': 'https://theankler.com'},
            {'name': 'puck', 'url': 'https://puck.news'},
            # ... more sources
        ]
    
    def scrape_entity(self, entity_id: str) -> Dict:
        """
        Scrape newsletters for entity mentions.
        
        Returns:
        {
            'entity_id': str,
            'mentions': List[Dict],
            'updated_attributes': Dict,
            'new_relationships': List[Dict],
            'confidence_score': float
        }
        """
        # Get entity from PostgreSQL
        entity = self.get_entity(entity_id)
        
        # Search newsletters for entity mentions
        mentions = []
        for source in self.sources:
            results = self.search_source(source, entity['name'])
            mentions.extend(results)
        
        # Extract structured data
        extracted_data = self.extract_data(mentions, entity)
        
        return extracted_data
    
    def search_source(self, source: Dict, entity_name: str) -> List[Dict]:
        """Search a specific newsletter source"""
        # Use existing newsletter pipeline
        # Or implement new scraping logic
        pass
    
    def extract_data(self, mentions: List, entity: Dict) -> Dict:
        """Extract structured data from mentions using LLM"""
        # Use GPT-4 or similar to extract:
        # - Job changes
        # - New projects
        # - Relationships
        # - Company news
        pass
```

### Newsletter Sources

| Source | Type | Update Frequency | Priority |
|--------|------|------------------|----------|
| The Ankler | Newsletter | Daily | High |
| Puck News | Newsletter | Daily | High |
| Deadline | News Site | Real-time | Medium |
| Variety | News Site | Real-time | Medium |
| Hollywood Reporter | News Site | Real-time | Medium |

### Scraping Strategy

1. **For Critical Entities:** Scrape all sources
2. **For Trending Entities:** Scrape top 3 sources
3. **For Scheduled Entities:** Scrape primary source only

---

## Component 4: Data Processor

### Purpose
Validate, merge, and enrich scraped data before syncing.

### Implementation

**File:** `pro_architecture/automation/data_processor.py`

```python
class DataProcessor:
    """
    Processes scraped data before syncing.
    
    Steps:
    1. Validate data quality
    2. Merge with existing data
    3. Generate embeddings
    4. Extract relationships
    """
    
    def process(self, scraped_data: Dict, existing_entity: Dict) -> Dict:
        """Process scraped data"""
        
        # 1. Validate
        if not self.validate(scraped_data):
            raise ValueError("Invalid scraped data")
        
        # 2. Merge
        merged = self.merge_data(scraped_data, existing_entity)
        
        # 3. Generate embeddings
        merged['embedding'] = self.generate_embedding(merged)
        
        # 4. Extract relationships
        merged['relationships'] = self.extract_relationships(scraped_data)
        
        # 5. Calculate confidence
        merged['confidence_score'] = self.calculate_confidence(scraped_data)
        
        return merged
    
    def validate(self, data: Dict) -> bool:
        """Validate scraped data quality"""
        # Check for required fields
        # Verify data freshness
        # Validate sources
        pass
    
    def merge_data(self, new: Dict, existing: Dict) -> Dict:
        """Merge new data with existing"""
        # Smart merge strategy:
        # - Keep existing if new is empty
        # - Append to arrays (mentions, projects)
        # - Update scalars if confidence > existing
        pass
    
    def generate_embedding(self, entity: Dict) -> List[float]:
        """Generate embedding vector"""
        # Use existing embedder
        pass
    
    def extract_relationships(self, data: Dict) -> List[Dict]:
        """Extract entity relationships"""
        # Parse mentions for relationships
        # Use LLM to identify connections
        pass
```

### Data Validation Rules

```python
VALIDATION_RULES = {
    'required_fields': ['entity_id', 'name', 'entity_type'],
    'min_confidence': 0.5,
    'max_age_days': 90,
    'min_mentions': 1,
    'allowed_sources': ['ankler', 'puck', 'deadline', 'variety', 'thr']
}
```

---

## Component 5: Sync Engine

### Purpose
Synchronize updated data across all systems (PostgreSQL, Pinecone, Neo4j, Redis).

### Implementation

**File:** `pro_architecture/automation/sync_engine.py`

```python
class SyncEngine:
    """
    Syncs entity updates across all systems.
    
    Systems:
    - PostgreSQL (source of truth)
    - Pinecone (vector search)
    - Neo4j (knowledge graph)
    - Redis (cache invalidation)
    """
    
    def __init__(self):
        self.pg_client = PostgresClient()
        self.pinecone_client = PineconeClient()
        self.neo4j_client = Neo4jClient()
        self.cache_manager = CacheManager()
    
    def sync_entity(self, entity_id: str, processed_data: Dict):
        """
        Sync entity across all systems.
        
        Order:
        1. PostgreSQL (source of truth)
        2. Pinecone (vector index)
        3. Neo4j (relationships)
        4. Redis (invalidate cache)
        """
        
        # 1. Update PostgreSQL
        self.pg_client.update_entity(entity_id, processed_data)
        
        # 2. Update Pinecone
        self.pinecone_client.upsert(
            id=entity_id,
            values=processed_data['embedding'],
            metadata={
                'name': processed_data['name'],
                'entity_type': processed_data['entity_type'],
                'updated_at': datetime.utcnow().isoformat()
            }
        )
        
        # 3. Update Neo4j
        self.sync_neo4j_relationships(entity_id, processed_data['relationships'])
        
        # 4. Invalidate cache
        self.cache_manager.invalidate_entity(entity_id)
        
        # 5. Log sync
        self.log_sync_success(entity_id)
    
    def sync_neo4j_relationships(self, entity_id: str, relationships: List[Dict]):
        """Sync relationships to Neo4j"""
        for rel in relationships:
            self.neo4j_client.create_or_update_relationship(
                from_id=entity_id,
                to_id=rel['target_id'],
                rel_type=rel['type'],
                properties=rel.get('properties', {})
            )
```

### Sync Strategy

**Atomic Updates:**
- Use database transactions
- Rollback on failure
- Retry logic (3 attempts)

**Consistency:**
- PostgreSQL is source of truth
- Other systems sync from PostgreSQL
- Cache invalidation happens last

---

## Component 6: Notification Service

### Purpose
Track update status and send notifications.

### Implementation

**File:** `pro_architecture/automation/notification_service.py`

```python
class NotificationService:
    """
    Tracks updates and sends notifications.
    
    Notifications:
    - Update completion
    - Critical entity alerts
    - Failure notifications
    - Daily summary
    """
    
    def notify_update_complete(self, entity_id: str, stats: Dict):
        """Notify when entity update completes"""
        # Log to database
        # Send webhook (optional)
        # Update metrics
        pass
    
    def notify_critical_entity(self, entity_id: str, reason: str):
        """Alert when entity becomes critical"""
        # Send email/Slack notification
        # Log alert
        pass
    
    def notify_failure(self, entity_id: str, error: str):
        """Notify on update failure"""
        # Log error
        # Send alert if critical
        pass
    
    def send_daily_summary(self):
        """Send daily update summary"""
        # Aggregate stats
        # Send report
        pass
```

---

## Implementation Phases

### Phase 1: Core Automation (Week 1-2)

**Goal:** Basic automated updates for critical entities

**Tasks:**
1. Build Demand Monitor
2. Build Update Orchestrator
3. Integrate existing newsletter scraper
4. Build Sync Engine
5. Test with 10 entities

**Deliverables:**
- Automated updates for critical entities
- Hourly monitoring
- Basic logging

### Phase 2: Advanced Scraping (Week 3-4)

**Goal:** Enhanced scraping and data processing

**Tasks:**
1. Build Data Processor
2. Improve newsletter scraping
3. Add relationship extraction
4. Implement confidence scoring
5. Test with 100 entities

**Deliverables:**
- High-quality data extraction
- Relationship discovery
- Confidence metrics

### Phase 3: Scale & Optimize (Week 5-6)

**Goal:** Scale to all entities and optimize performance

**Tasks:**
1. Implement rate limiting
2. Add retry logic
3. Optimize database queries
4. Add monitoring/alerting
5. Test with all 6,408 entities

**Deliverables:**
- Full automation for all entities
- Performance optimizations
- Comprehensive monitoring

### Phase 4: Intelligence & Learning (Week 7-8)

**Goal:** Add ML-based optimization

**Tasks:**
1. Track update effectiveness
2. Learn optimal update frequency
3. Predict trending entities
4. Optimize scraping sources
5. A/B test strategies

**Deliverables:**
- ML-optimized update scheduling
- Predictive analytics
- Continuous improvement

---

## Cost Estimate

### Infrastructure

| Component | Platform | Cost |
|-----------|----------|------|
| Demand Monitor | GitHub Actions | Free |
| Update Orchestrator | Render Background Worker | $7/mo |
| Newsletter Scraping | Existing infrastructure | $0 |
| Data Processing | Render (included) | $0 |
| Sync Engine | Render (included) | $0 |
| Notifications | Email/Logs | Free |
| **TOTAL** | | **$7/mo** |

### API Costs

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI (GPT-4) | 1000 updates/day @ $0.01/update | $10/day = $300/mo |
| Pinecone | Existing plan | $0 |
| PostgreSQL | Existing plan | $0 |
| **TOTAL** | | **~$300/mo** |

**Note:** Can reduce API costs by:
- Using GPT-3.5 instead of GPT-4 (~10x cheaper)
- Caching LLM responses
- Batching requests
- Only processing critical/trending entities

**Optimized Cost:** ~$30-50/mo

---

## Success Metrics

### Performance Metrics

- **Update Latency:** < 5 minutes from detection to sync
- **Success Rate:** > 95% of updates successful
- **Data Quality:** > 90% confidence score
- **Coverage:** 100% of critical entities updated within 24h

### Business Metrics

- **Freshness:** Average entity age < 30 days
- **User Satisfaction:** Reduced "data is stale" feedback
- **Query Accuracy:** Improved answer quality
- **Engagement:** Increased user queries (better data = more usage)

---

## Risk Mitigation

### Technical Risks

1. **Scraping Failures**
   - Mitigation: Multiple sources, retry logic
   
2. **Rate Limiting**
   - Mitigation: Distributed scraping, backoff strategy
   
3. **Data Quality**
   - Mitigation: Validation rules, confidence scoring
   
4. **System Overload**
   - Mitigation: Queue management, rate limiting

### Business Risks

1. **High API Costs**
   - Mitigation: Use cheaper models, cache responses
   
2. **Legal Issues (Scraping)**
   - Mitigation: Respect robots.txt, use public APIs where available
   
3. **Data Accuracy**
   - Mitigation: Human review for critical entities, confidence thresholds

---

## Next Steps

1. **Review this plan** - Feedback and adjustments
2. **Prioritize features** - What to build first?
3. **Set timeline** - When to start implementation?
4. **Allocate resources** - Who will work on this?
5. **Start Phase 1** - Build core automation

---

## Conclusion

The Automated Update System will transform Mandate Wizard from a static knowledge base into a **living, self-updating intelligence platform**.

**Key Benefits:**
- ✅ Always-fresh data for high-demand entities
- ✅ Reduced manual maintenance
- ✅ Better user experience
- ✅ Scalable to 10x more entities
- ✅ Data-driven prioritization

**Ready to proceed with implementation?**
