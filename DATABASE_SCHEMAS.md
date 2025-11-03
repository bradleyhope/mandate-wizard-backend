# Mandate Wizard Database Schemas

**Author:** Manus AI  
**Date:** October 31, 2025  
**Version:** 1.0

---

## Executive Summary

Mandate Wizard employs a dual-database architecture combining **Neo4j** (graph database) for relationship mapping and **Pinecone** (vector database) for semantic search. This document defines the complete schemas for all entity types, establishes quality standards, and provides guidelines for data integrity.

---

## Architecture Overview

### Database Roles

**Neo4j (Graph Database)**
- Stores structured entities and relationships
- Enables complex graph queries (e.g., "Which executives greenlight crime thrillers?")
- Maintains referential integrity through typed relationships
- Supports property-based filtering and aggregation

**Pinecone (Vector Database)**
- Stores semantic embeddings for natural language search
- Enables similarity-based retrieval (e.g., "Find shows similar to 3 Body Problem")
- Provides fast approximate nearest neighbor search
- Enriches results with metadata for filtering

**Hybrid Retrieval Strategy**
- Vector search finds semantically similar content
- Graph queries provide precise relationship-based results
- Combined results offer both breadth (semantic) and depth (structural)

---

## Entity Schemas

### 1. Greenlight

A **Greenlight** represents a TV show or film that has been officially approved for production by a streaming platform or network.

#### Neo4j Schema

**Node Label:** `Greenlight`

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `title` | String | ✅ Yes | Official title of the project | "3 Body Problem" |
| `genre` | String | ✅ Yes | Primary genre(s), comma-separated | "Sci-Fi, Mystery" |
| `format` | String | ✅ Yes | Production format | "Limited Series" |
| `streamer` | String | ✅ Yes | Platform greenlighting the project | "Netflix" |
| `source` | String | ⚠️ Recommended | URL to announcement article | "https://deadline.com/..." |
| `date` | String | ⚠️ Recommended | Greenlight announcement date | "2020-09-01" |
| `logline` | String | ⚠️ Recommended | One-sentence premise (50-100 words) | "Humanity's first contact with an alien civilization..." |
| `description` | String | ⚠️ Recommended | Detailed plot summary (100-200 words) | "Based on Liu Cixin's award-winning trilogy..." |
| `episode_count` | Integer | 🔵 Optional | Number of episodes ordered | 8 |
| `season_number` | Integer | 🔵 Optional | Season number (for renewals) | 2 |
| `production_company` | String | 🔵 Optional | Primary production company | "Plan B Entertainment" |
| `showrunner` | String | 🔵 Optional | Showrunner name(s) | "David Benioff, D.B. Weiss" |
| `cast` | String | 🔵 Optional | Lead cast members | "Benedict Wong, Jovan Adepo" |
| `created_at` | DateTime | 🔵 Auto | Record creation timestamp | "2025-10-31T00:00:00Z" |
| `updated_at` | DateTime | 🔵 Auto | Last update timestamp | "2025-10-31T12:00:00Z" |

**Relationships:**

| Relationship | Target Node | Properties | Description |
|--------------|-------------|------------|-------------|
| `GREENLIT_BY` | `Person` (Executive) | `role`, `date` | Executive who approved the project |
| `PRODUCED_BY` | `Person` (Producer) | `role` | Producer attached to the project |
| `STARS` | `Person` (Actor) | `role`, `character` | Lead actor in the project |
| `CREATED_BY` | `Person` (Creator) | `role` | Creator/showrunner of the project |
| `MADE_BY` | `Company` | `type` | Production company involved |
| `REPORTED_IN` | `NewsletterSource` | `date` | Source article reporting the greenlight |

#### Pinecone Schema

**Namespace:** `greenlights`

**Vector:** 384-dimensional embedding (SentenceTransformer `all-MiniLM-L6-v2`)

**Metadata:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | String | Project title |
| `genre` | String | Genre(s) |
| `format` | String | Production format |
| `streamer` | String | Platform name |
| `date` | String | Greenlight date |
| `logline` | String | One-sentence premise |
| `description` | String | Detailed summary |
| `executives` | String | Comma-separated executive names |
| `showrunner` | String | Showrunner name(s) |
| `cast` | String | Lead cast |
| `source` | String | Article URL |

**Embedding Source:**
```
{title} - {genre} {format} greenlit by {streamer}. {logline} {description}
```

---

### 2. Person (Executive/Talent)

A **Person** represents an industry professional (executive, producer, actor, director, etc.).

#### Neo4j Schema

**Node Label:** `Person`

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | String | ✅ Yes | Full name | "Peter Friedlander" |
| `title` | String | ⚠️ Recommended | Current job title | "VP, Scripted Series" |
| `company` | String | ⚠️ Recommended | Current employer | "Netflix" |
| `role` | String | ⚠️ Recommended | Primary role category | "Executive" |
| `bio` | String | 🔵 Optional | Professional biography | "Peter Friedlander oversees..." |
| `linkedin_url` | String | 🔵 Optional | LinkedIn profile URL | "https://linkedin.com/in/..." |
| `imdb_url` | String | 🔵 Optional | IMDb profile URL | "https://imdb.com/name/..." |
| `email` | String | 🔵 Optional | Professional email | "peter@netflix.com" |
| `created_at` | DateTime | 🔵 Auto | Record creation timestamp | "2025-10-31T00:00:00Z" |

**Relationships:**

| Relationship | Target Node | Properties | Description |
|--------------|-------------|------------|-------------|
| `GREENLIT` | `Greenlight` | `date`, `role` | Projects this executive greenlit |
| `PRODUCED` | `Greenlight` | `role` | Projects this person produced |
| `ACTED_IN` | `Greenlight` | `character`, `role` | Projects this person acted in |
| `CREATED` | `Greenlight` | `role` | Projects this person created |
| `WORKS_FOR` | `Company` | `start_date`, `title` | Current/past employment |
| `QUOTED_IN` | `Quote` | `date` | Quotes attributed to this person |

#### Pinecone Schema

**Namespace:** `people`

**Metadata:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Person name |
| `title` | String | Job title |
| `company` | String | Employer |
| `role` | String | Role category |
| `bio` | String | Biography |
| `greenlights` | String | Comma-separated greenlight titles |
| `genres` | String | Preferred genres (inferred from greenlights) |

---

### 3. Quote

A **Quote** represents a strategic statement from an industry executive about content strategy, market trends, or business decisions.

#### Neo4j Schema

**Node Label:** `Quote`

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `quote` | String | ✅ Yes | The actual quote text | "We're doubling down on international content..." |
| `executive` | String | ✅ Yes | Executive name | "Bela Bajaria" |
| `title` | String | ⚠️ Recommended | Executive title | "Chief Content Officer" |
| `company` | String | ⚠️ Recommended | Company name | "Netflix" |
| `context` | String | ⚠️ Recommended | Surrounding context (100-200 words) | "Speaking at the Code Conference..." |
| `source` | String | ⚠️ Recommended | Source article URL | "https://puck.news/..." |
| `date` | String | ⚠️ Recommended | Quote date | "2025-09-15" |
| `topic` | String | 🔵 Optional | Main topic/theme | "International Expansion" |
| `sentiment` | String | 🔵 Optional | Sentiment (positive/neutral/negative) | "positive" |
| `created_at` | DateTime | 🔵 Auto | Record creation timestamp | "2025-10-31T00:00:00Z" |

**Relationships:**

| Relationship | Target Node | Properties | Description |
|--------------|-------------|------------|-------------|
| `SAID_BY` | `Person` | `date` | Executive who said the quote |
| `ABOUT` | `Greenlight` | - | Quote referencing a specific project |
| `REPORTED_IN` | `NewsletterSource` | `date` | Source article |

#### Pinecone Schema

**Namespace:** `quotes`

**Metadata:**

| Field | Type | Description |
|-------|------|-------------|
| `quote` | String | Quote text |
| `executive` | String | Executive name |
| `title` | String | Executive title |
| `company` | String | Company name |
| `context` | String | Surrounding context |
| `date` | String | Quote date |
| `topic` | String | Topic/theme |
| `source` | String | Source URL |

---

### 4. Production Deal

A **Production Deal** represents an overall deal or first-look agreement between talent/companies and streamers.

#### Neo4j Schema

**Node Label:** `ProductionDeal`

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `company` | String | ✅ Yes | Production company or talent name | "Jaume Collet-Serra" |
| `deal_type` | String | ✅ Yes | Type of deal | "Overall Film Deal" |
| `platform` | String | ✅ Yes | Streaming platform | "Netflix" |
| `year` | String | ⚠️ Recommended | Deal announcement year | "2025" |
| `duration` | String | 🔵 Optional | Deal duration | "Multi-year" |
| `genre_focus` | String | 🔵 Optional | Genre focus | "Action, Thriller" |
| `notable_projects` | String | 🔵 Optional | Notable past projects | "The Shallows, Black Adam" |
| `source` | String | ⚠️ Recommended | Source article URL | "https://variety.com/..." |
| `date` | String | ⚠️ Recommended | Announcement date | "2025-08-20" |
| `created_at` | DateTime | 🔵 Auto | Record creation timestamp | "2025-10-31T00:00:00Z" |

**Relationships:**

| Relationship | Target Node | Properties | Description |
|--------------|-------------|------------|-------------|
| `SIGNED_BY` | `Person` | `role` | Talent who signed the deal |
| `WITH_COMPANY` | `Company` | - | Production company involved |
| `WITH_PLATFORM` | `Company` | - | Streaming platform |
| `REPORTED_IN` | `NewsletterSource` | `date` | Source article |

#### Pinecone Schema

**Namespace:** `deals`

**Metadata:**

| Field | Type | Description |
|-------|------|-------------|
| `company` | String | Company/talent name |
| `deal_type` | String | Deal type |
| `platform` | String | Platform name |
| `year` | String | Deal year |
| `genre_focus` | String | Genre focus |
| `notable_projects` | String | Past projects |
| `source` | String | Source URL |

---

## Quality Standards

### Completeness Tiers

| Tier | Score | Criteria | Action Required |
|------|-------|----------|-----------------|
| **Critical** | <50% | Missing required fields | 🔴 Immediate healing required |
| **Incomplete** | 50-79% | Missing recommended fields | ⚠️ Healing recommended |
| **Complete** | 80-94% | All required + most recommended | 🟢 Monitor for staleness |
| **High-Quality** | 95-100% | All fields populated | ✅ Maintain quality |

### Field Weights (Greenlights)

| Field | Weight | Rationale |
|-------|--------|-----------|
| `title` | 20% | Core identifier |
| `executive` | 20% | Enables executive profiling |
| `genre` | 15% | Essential for categorization |
| `format` | 15% | Essential for analysis |
| `talent` | 15% | Relationship mapping |
| `production_company` | 10% | Industry insights |
| `date` | 5% | Temporal analysis |

### Staleness Detection

**Staleness Criteria:**

| Entity Type | Staleness Threshold | Update Trigger |
|-------------|---------------------|----------------|
| Greenlight | 90 days without update | Check for production updates, cast announcements |
| Quote | 180 days without update | Check for new quotes from same executive |
| Deal | 365 days without update | Check for deal renewals or new projects |
| Person | 180 days without update | Check for job changes, new projects |

**Update Sources:**
- Trade publications (Deadline, Variety, THR)
- Netflix Tudum blog
- Company press releases
- LinkedIn updates (for Person entities)

---

## Data Validation Rules

### Required Field Validation

```python
def validate_greenlight(record):
    required = ['title', 'genre', 'format', 'streamer']
    missing = [f for f in required if not record.get(f)]
    return len(missing) == 0, missing
```

### URL Validation

```python
def validate_url(url):
    if not url:
        return False
    return url.startswith('http://') or url.startswith('https://')
```

### Date Format Validation

```python
def validate_date(date_str):
    # Expected format: YYYY-MM-DD
    import re
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    return bool(re.match(pattern, date_str))
```

### Executive Name Validation

```python
def validate_executive(name):
    # Should be a person name, not "Unknown" or generic text
    invalid_values = ['Unknown', 'None', '', 'TBD', 'N/A']
    return name not in invalid_values and len(name.split()) >= 2
```

---

## Sync Strategy

### Neo4j → Pinecone Sync

**When to sync:**
- After creating new Greenlight/Quote/Deal in Neo4j
- After enriching existing records with new data
- After fixing data quality issues

**Sync process:**
1. Query Neo4j for updated records
2. Generate embeddings from text fields
3. Upsert to Pinecone with metadata
4. Verify vector count matches Neo4j count

### Pinecone → Neo4j Sync

**When to sync:**
- After bulk import to Pinecone
- When Pinecone has richer metadata than Neo4j

**Sync process:**
1. Query Pinecone for all vectors in namespace
2. Extract metadata
3. Match to Neo4j nodes by title/ID
4. Update Neo4j properties if newer

---

## Best Practices

### Data Entry

1. **Always validate before insert** - Check required fields and formats
2. **Use authoritative sources** - Prefer trade publications over Wikipedia
3. **Extract, don't generate** - Only use information from source articles
4. **Normalize names** - Use consistent formatting for people/companies
5. **Link relationships** - Always create `GREENLIT_BY`, `PRODUCED_BY` edges

### Data Enrichment

1. **Prioritize executives** - Executive relationships are highest value
2. **Enrich in batches** - Process 10-20 records at a time
3. **Save intermediate results** - Enable recovery from failures
4. **Verify before update** - Don't overwrite good data with bad
5. **Track provenance** - Record source URLs and update timestamps

### Quality Monitoring

1. **Daily completeness checks** - Measure % of records at each tier
2. **Weekly staleness audits** - Identify records needing updates
3. **Monthly schema compliance** - Verify all fields match schema
4. **Quarterly relationship audits** - Check for orphaned nodes

---

## Appendix: Example Records

### High-Quality Greenlight

```json
{
  "title": "3 Body Problem",
  "genre": "Sci-Fi, Mystery",
  "format": "Limited Series",
  "streamer": "Netflix",
  "source": "https://deadline.com/2020/09/david-benioff-d-b-weiss-three-body-problem-netflix-1203028218/",
  "date": "2020-09-01",
  "logline": "Humanity's first contact with an alien civilization unfolds through decades of scientific discovery and political intrigue.",
  "description": "Based on Liu Cixin's award-winning trilogy, 3 Body Problem follows a group of scientists who discover evidence of an alien civilization and must navigate the consequences of this revelation across multiple timelines.",
  "episode_count": 8,
  "production_company": "Plan B Entertainment",
  "showrunner": "David Benioff, D.B. Weiss, Alexander Woo",
  "cast": "Benedict Wong, Jovan Adepo, Eiza González",
  "executives": "Peter Friedlander"
}
```

### High-Quality Quote

```json
{
  "quote": "We're doubling down on international content because we've seen that great stories can come from anywhere and resonate everywhere.",
  "executive": "Bela Bajaria",
  "title": "Chief Content Officer",
  "company": "Netflix",
  "context": "Speaking at the Code Conference in September 2025, Bela Bajaria emphasized Netflix's commitment to global storytelling, citing the success of Squid Game and Money Heist as proof that audiences worldwide are hungry for diverse narratives.",
  "source": "https://puck.news/bela-bajaria-international-expansion/",
  "date": "2025-09-15",
  "topic": "International Expansion",
  "sentiment": "positive"
}
```

---

**Document Version:** 1.0  
**Last Updated:** October 31, 2025  
**Maintained By:** Manus AI

