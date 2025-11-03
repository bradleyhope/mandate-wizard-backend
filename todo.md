# Mandate Wizard Backend TODO

## Completed
- [x] Fix GPT-5 API integration (use Responses API with web search tool)
- [x] Test GPT-5 web search for enrichment
- [x] Basic healer for incomplete Pinecone records
- [x] Prototype intelligent healer with gap analysis

## In Progress - Comprehensive Intelligent Healer v2.0
- [x] Implement retry logic with exponential backoff
- [x] Increase timeout to 240 seconds for GPT-5
- [x] Add rate limiting (5 seconds between requests)
- [ ] Core Architecture
  - [ ] Entity classification system (ProductionCompany, Studio, MediaOutlet, TalentAgency, Streamer)
  - [ ] Data quality scoring (0-100% completeness per card)
  - [ ] Smart deduplication and canonical name resolution
  - [ ] Cross-database sync (Pinecone + Neo4j)
  - [ ] Temporal tracking (last_updated, data_freshness)

- [ ] Phase 1: Deep Healing with Quality Scoring
  - [ ] Heal all Mandates (825) with completeness scoring
  - [ ] Heal all People (386) with career timeline
  - [ ] Heal all Production Companies (247) with proper classification
  - [ ] Heal all Greenlights (114 Pinecone + 70 Neo4j)
  - [ ] Heal all Quotes (211 Pinecone + 160 Neo4j)
  - [ ] Update both Pinecone and Neo4j simultaneously

- [ ] Phase 2: Intelligent Gap Analysis
  - [ ] Extract and classify all mentioned entities
  - [ ] Detect missing People cards (with importance scoring)
  - [ ] Detect missing Production Company cards (real prodcos only)
  - [ ] Detect missing Project/Greenlight cards
  - [ ] Identify duplicate entities across databases
  - [ ] Generate prioritized research queue

- [ ] Phase 3: Rich Relationship Building
  - [ ] Person-Mandate relationships (OVERSEES, CREATED, PITCHED)
  - [ ] Person-Person relationships (WORKED_WITH, MENTORED, PARTNERED)
  - [ ] Person-Company relationships (WORKS_AT, FOUNDED, LEFT)
  - [ ] Company-Project relationships (PRODUCES, DISTRIBUTES)
  - [ ] Temporal relationships with date properties
  - [ ] Build Hollywood ecosystem graph over time

- [ ] Phase 4: Coverage Metrics & Analytics
  - [ ] Calculate industry coverage by genre
  - [ ] Calculate coverage by studio/streamer
  - [ ] Track top executives coverage (% in database)
  - [ ] Identify underrepresented areas
  - [ ] Generate coverage report

- [ ] Phase 5: Continuous Monitoring System
  - [ ] Scheduled healing runs (daily/weekly)
  - [ ] Stale data detection (>6 months old)
  - [ ] Auto-prioritization for re-healing
  - [ ] Gap detection alerts
  - [ ] Owner notification system
  - [ ] Research queue generation

- [ ] Phase 6: Monitoring Dashboard
  - [ ] Real-time healing progress display
  - [ ] Data quality metrics visualization
  - [ ] Gap analysis charts
  - [ ] Coverage heatmaps
  - [ ] Research queue management UI

## Future Features
- [ ] Activity log & quality control dashboard
- [ ] Comprehensive scraping from 38 sources
- [ ] Query interface refinements
- [ ] Automated entity merging and deduplication
- [ ] Machine learning for entity classification



## Speed Improvements & Database Updates
- [x] Speed up healing process (optimized settings)
- [ ] Implement parallel processing with 5 workers
  - [ ] Reduce rate limiting from 5s to 2-3s
  - [ ] Reduce timeout from 240s to 180s
  - [ ] Use lower reasoning effort ("low" instead of "medium")
  - [ ] Implement checkpoint system (save every 50 mandates)
- [ ] Update Pinecone/Neo4j with healed data from 100 completed mandates
- [ ] Resume healing from mandate #104



## Hollywood Signal Subscription Gate
- [x] Fixed backend connection error (installed PyJWT)
- [x] Backend running on port 5000
- [x] Received Ghost API credentials
- [x] Implement Ghost Members API authentication
  - [x] Research Hollywood Signal subscription/payment platform (Ghost)
  - [x] Design authentication flow (magic link + email/password)
  - [x] Create backend Ghost auth service
  - [ ] Add login page to frontend
  - [ ] Implement backend authentication middleware
  - [ ] Integrate with Hollywood Signal subscriber database/API
  - [ ] Add subscription status check before allowing access
  - [ ] Handle subscription expiration/cancellation
  - [ ] Add "Subscribe" CTA for non-subscribers




## Security & Abuse Prevention
- [x] Comprehensive security audit (SECURITY_AUDIT.md created)
- [x] Implemented rate limiting system
- [x] Implemented input validation and sanitization
- [x] Restricted CORS to specific origins
- [x] Added backend authentication to all query endpoints
- [ ] Remaining security tasks
  - [ ] Review all API endpoints for vulnerabilities
  - [ ] Check for SQL injection, XSS, CSRF risks
  - [ ] Validate input sanitization
  - [ ] Review authentication/authorization logic
  - [ ] Check for exposed secrets/credentials
  - [ ] Review CORS configuration
  - [ ] Check rate limiting implementation

- [ ] Credit abuse prevention system
  - [ ] Implement rate limiting per user/IP
  - [ ] Track API usage per user
  - [ ] Set query limits (e.g., 100 queries/day for paid, 3/day for free)
  - [ ] Detect and block suspicious patterns (rapid-fire queries, scraping)
  - [ ] Add CAPTCHA for suspicious activity
  - [ ] Implement cost tracking (GPT-5 API costs)
  - [ ] Alert system for unusual usage patterns

## User Analytics & Engagement
- [ ] Deep chat analytics system
  - [ ] Log all user queries with metadata (user, timestamp, intent, response time)
  - [ ] Track query success/failure rates
  - [ ] Analyze query patterns and topics
  - [ ] Identify common questions and pain points
  - [ ] Track user satisfaction (implicit: follow-up questions, explicit: ratings)
  - [ ] Build dashboard for analytics visualization
  - [ ] Generate weekly/monthly reports
  - [ ] A/B testing framework for response quality
  - [ ] User journey mapping (what do users ask first, then what?)
  - [ ] Identify drop-off points

## Capacity & Performance
- [ ] Capacity planning and review
  - [ ] Measure current system capacity (requests/second, concurrent users)
  - [ ] Database performance review (Pinecone, Neo4j query times)
  - [ ] GPT-5 API rate limits and costs
  - [ ] Memory usage and optimization
  - [ ] Identify bottlenecks
  - [ ] Load testing
  - [ ] Scaling strategy (horizontal/vertical)
  - [ ] Cost projections at scale

- [ ] High-level code review
  - [ ] Review architecture and design patterns
  - [ ] Identify technical debt
  - [ ] Code quality assessment
  - [ ] Performance optimization opportunities
  - [ ] Refactoring recommendations
  - [ ] Documentation gaps
  - [ ] Testing coverage




## Deep Chat Analytics
- [x] Implement comprehensive chat analytics system
  - [x] Created chat_analytics.py - Analytics engine
  - [x] Track all queries with full metadata
  - [x] Per-user statistics and journey analysis
  - [x] Pattern extraction (topics, intents, keywords)
  - [x] Performance metrics (response times, success rates)
  - [x] Engagement analysis (sessions, drop-off rates)
  - [x] Analytics API endpoints (/api/analytics/*)
  - [x] Integrated analytics logging into query endpoints




## Engine Optimization & Testing
- [ ] Create detailed user personas (5-7 personas)
- [ ] Run deep testing sessions (10+ questions per persona)
- [ ] Analyze query patterns and failure modes
- [ ] Optimize HybridRAG engine based on findings
- [ ] Improve response quality and relevance
- [ ] Add persona-specific intelligence features




## Authentication Issues
- [ ] Fix frontend authentication flow for bradley@projectbrazen.com
- [ ] Add development bypass for testing
- [ ] Debug CORS/API connection between frontend and backend




## Frontend Connection Issues
- [x] Backend API verified working (returns 7 cards successfully)
- [x] CORS headers confirmed correct
- [x] Added console logging to frontend
- [x] Added CORS mode and credentials to fetch
- [x] Created test page - works perfectly!
- [ ] CRITICAL: React frontend still failing - likely Vite build issue
- [ ] Cleared cache but still failing
- [ ] Need to check if it's a proxy/routing issue in Vite config

