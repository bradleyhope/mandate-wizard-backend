# Mandate Wizard: Database Architecture

**Version:** 2.0  
**Last Updated:** October 26, 2025  
**Purpose:** Complete specification of Pinecone and Neo4j database structure for Layers 1-8

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Pinecone Structure](#pinecone-structure)
3. [Neo4j Structure](#neo4j-structure)
4. [Layer-by-Layer Specifications](#layer-by-layer-specifications)
5. [Data Flow](#data-flow)
6. [Update Procedures](#update-procedures)
7. [Query Patterns](#query-patterns)

---

## Overview

### Database Architecture

The Mandate Wizard uses a **hybrid database architecture**:

1. **Pinecone (Vector Database)**
   - Stores embeddings for semantic search
   - Organized by namespaces (one per layer)
   - Enables fast similarity search across all content

2. **Neo4j (Graph Database)**
   - Stores structured relationships
   - Executive → Production Company → Projects
   - Enables complex relationship queries

3. **Redis (Cache)**
   - Caches query results
   - Stores user sessions
   - Improves response time

### Current State

**✅ Layers 1-2 (Complete):**
- Layer 1: Executive routing (Neo4j + Pinecone)
- Layer 2: Executive mandates (Pinecone quotes namespace)

**🔧 Layers 3-8 (Structure Ready, Data Needed):**
- Layer 3: Production companies
- Layer 4: Recent greenlights
- Layer 5: Pitch requirements
- Layer 6: Packaging intelligence
- Layer 7: Timing & strategy
- Layer 8: Success metrics (optional)

---

## Pinecone Structure

### Index Configuration

**Index Name:** `mandate-wizard`  
**Dimensions:** 1536 (OpenAI text-embedding-3-small)  
**Metric:** Cosine similarity  
**Pod Type:** p1.x1

### Namespace Organization

Each layer has its own namespace for isolation and efficient querying:

```
mandate-wizard/
├── executives/          # Layer 1: Executive profiles
├── quotes/              # Layer 2: Executive quotes and mandates
├── production_companies/# Layer 3: Production company info
├── greenlights/         # Layer 4: Recent greenlight announcements
├── pitch_requirements/  # Layer 5: Pitch format requirements
├── packaging/           # Layer 6: Talent/packaging preferences
├── timing/              # Layer 7: Industry events and schedules
└── success_metrics/     # Layer 8: Historical success data (optional)
```

### Vector Metadata Structure

Each vector in Pinecone has:
1. **id** - Unique identifier
2. **values** - 1536-dimensional embedding
3. **metadata** - Structured data (varies by namespace)

---

## Neo4j Structure

### Node Types

```cypher
// Layer 1: Executives
(:Executive {
  name: string,
  title: string,
  region: string,
  content_type: string,
  email: string,
  bio: string
})

// Layer 3: Production Companies
(:ProductionCompany {
  name: string,
  country: string,
  specializations: [string],
  has_netflix_deal: boolean,
  deal_type: string,
  deal_year: integer,
  website: string,
  submission_method: string,
  notes: string
})

// Layer 4: Projects (Greenlights)
(:Project {
  title: string,
  greenlight_date: date,
  announcement_date: date,
  genre: string,
  format: string,
  season_number: integer,
  episode_count: integer,
  budget_range: string,
  target_release: string,
  source_url: string,
  notes: string
})

// Layer 6: Talent
(:Talent {
  name: string,
  role: string,  // "showrunner", "director", "actor", "producer"
  tier: string,  // "tier_1", "tier_2"
  notes: string
})

// Layer 7: Events
(:IndustryEvent {
  name: string,
  start_date: date,
  end_date: date,
  location: string,
  opportunity_type: string,
  notes: string
})
```

### Relationship Types

```cypher
// Layer 1 → Layer 3
(:Executive)-[:WORKS_WITH {primary: boolean}]->(:ProductionCompany)

// Layer 3 → Layer 4
(:ProductionCompany)-[:PRODUCED]->(:Project)

// Layer 1 → Layer 4
(:Executive)-[:GREENLIT {date: date}]->(:Project)

// Layer 4 → Layer 6
(:Project)-[:ATTACHED {role: string}]->(:Talent)

// Layer 1 → Layer 7
(:Executive)-[:ATTENDS]->(:IndustryEvent)
```

---

## Layer-by-Layer Specifications

### Layer 1: Executive Routing (✅ Complete)

**Purpose:** Identify which executive handles what content

**Pinecone Namespace:** `executives`

**Vector Metadata:**
```json
{
  "id": "exec_peter_friedlander",
  "metadata": {
    "name": "Peter Friedlander",
    "title": "VP, U.S. Scripted Series",
    "region": "United States",
    "content_types": ["Drama", "Limited Series", "Thriller"],
    "email": "peter.friedlander@netflix.com",
    "bio": "Oversees all U.S. scripted series development...",
    "layer": "executives"
  }
}
```

**Neo4j Node:**
```cypher
CREATE (:Executive {
  name: "Peter Friedlander",
  title: "VP, U.S. Scripted Series",
  region: "United States",
  content_type: "Scripted Drama",
  email: "peter.friedlander@netflix.com",
  bio: "Oversees all U.S. scripted series development..."
})
```

**Text to Embed:**
```
Peter Friedlander, VP of U.S. Scripted Series at Netflix. Oversees drama, thriller, and limited series development for the United States market. Focus on character-driven narratives with international appeal.
```

---

### Layer 2: Executive Mandates (✅ Complete)

**Purpose:** Understand what each executive wants

**Pinecone Namespace:** `quotes`

**Vector Metadata:**
```json
{
  "id": "quote_peter_friedlander_001",
  "metadata": {
    "executive_name": "Peter Friedlander",
    "quote_text": "We're looking for elevated genre content that travels globally...",
    "source": "Variety Interview",
    "date": "2024-03-15",
    "url": "https://variety.com/...",
    "themes": ["elevated genre", "global appeal", "character-driven"],
    "layer": "quotes"
  }
}
```

**Text to Embed:**
```
Peter Friedlander on content strategy: "We're looking for elevated genre content that travels globally. Character-driven narratives that feel both specific and universal."
```

---

### Layer 3: Production Companies (🔧 Structure Ready)

**Purpose:** Show users how to access executives through production companies

**Pinecone Namespace:** `production_companies`

**Vector Metadata:**
```json
{
  "id": "prodco_studio_dragon",
  "metadata": {
    "company_name": "Studio Dragon",
    "country": "South Korea",
    "specializations": ["Drama", "Thriller", "Romance"],
    "has_netflix_deal": true,
    "deal_type": "First-look deal",
    "deal_year": 2021,
    "primary_executive": "Don Kang",
    "notable_projects": ["Squid Game", "Kingdom"],
    "submission_method": "Through agent/manager only",
    "website": "https://www.studiodragon.net",
    "notes": "Major Korean production company with exclusive Netflix partnership",
    "layer": "production_companies"
  }
}
```

**Neo4j Nodes & Relationships:**
```cypher
// Create production company node
CREATE (pc:ProductionCompany {
  name: "Studio Dragon",
  country: "South Korea",
  specializations: ["Drama", "Thriller", "Romance"],
  has_netflix_deal: true,
  deal_type: "First-look deal",
  deal_year: 2021,
  website: "https://www.studiodragon.net",
  submission_method: "Through agent/manager only",
  notes: "Major Korean production company"
})

// Link to executive
MATCH (e:Executive {name: "Don Kang"})
MATCH (pc:ProductionCompany {name: "Studio Dragon"})
CREATE (e)-[:WORKS_WITH {primary: true, since: 2021}]->(pc)

// Link to projects
MATCH (pc:ProductionCompany {name: "Studio Dragon"})
CREATE (pc)-[:PRODUCED {year: 2021}]->(:Project {title: "Squid Game"})
CREATE (pc)-[:PRODUCED {year: 2019}]->(:Project {title: "Kingdom"})
```

**Text to Embed:**
```
Studio Dragon is a major South Korean production company specializing in drama, thriller, and romance content. They have a first-look deal with Netflix since 2021, working primarily with Don Kang. Notable productions include Squid Game and Kingdom. Submissions accepted through agent/manager only.
```

**What Goes Here:**
- Production company profiles
- Netflix deal information
- Submission policies
- Contact information
- Notable projects
- Executive relationships

**Update Frequency:** Monthly (when new deals announced)

---

### Layer 4: Recent Greenlights (🔧 Structure Ready)

**Purpose:** Show what executives have recently greenlit to understand current priorities

**Pinecone Namespace:** `greenlights`

**Vector Metadata:**
```json
{
  "id": "greenlight_diplomat_s2",
  "metadata": {
    "project_title": "The Diplomat Season 2",
    "executive_name": "Peter Friedlander",
    "greenlight_date": "2023-05-01",
    "announcement_date": "2023-05-15",
    "genre": "Political Drama",
    "format": "Series",
    "season_number": 2,
    "episode_count": 8,
    "production_company": "Debora Cahn Productions",
    "showrunner": "Debora Cahn",
    "cast": ["Keri Russell", "Rufus Sewell"],
    "budget_range": "$5-8M per episode",
    "target_release": "Q2 2024",
    "source_url": "https://deadline.com/...",
    "notes": "Renewal after strong Season 1 performance",
    "layer": "greenlights"
  }
}
```

**Neo4j Nodes & Relationships:**
```cypher
// Create project node
CREATE (p:Project {
  title: "The Diplomat Season 2",
  greenlight_date: date('2023-05-01'),
  announcement_date: date('2023-05-15'),
  genre: "Political Drama",
  format: "Series",
  season_number: 2,
  episode_count: 8,
  budget_range: "$5-8M per episode",
  target_release: "Q2 2024",
  source_url: "https://deadline.com/...",
  notes: "Renewal after strong Season 1 performance"
})

// Link to executive
MATCH (e:Executive {name: "Peter Friedlander"})
MATCH (p:Project {title: "The Diplomat Season 2"})
CREATE (e)-[:GREENLIT {date: date('2023-05-01')}]->(p)

// Link to production company
MATCH (pc:ProductionCompany {name: "Debora Cahn Productions"})
MATCH (p:Project {title: "The Diplomat Season 2"})
CREATE (pc)-[:PRODUCED]->(p)
```

**Text to Embed:**
```
Peter Friedlander greenlit The Diplomat Season 2 in May 2023. Political drama series, 8 episodes, produced by Debora Cahn Productions. Stars Keri Russell and Rufus Sewell. Budget $5-8M per episode. Renewal after strong Season 1 performance. Target release Q2 2024.
```

**What Goes Here:**
- Project greenlights from last 12 months
- Executive who greenlit it
- Production details (genre, format, episode count)
- Budget information (if available)
- Production company
- Key talent attached
- Target release dates

**Update Frequency:** Weekly (as new greenlights announced)

---

### Layer 5: Pitch Requirements (🔧 Structure Ready)

**Purpose:** Tell users exactly how to format their pitch for specific executives

**Pinecone Namespace:** `pitch_requirements`

**Vector Metadata:**
```json
{
  "id": "pitch_peter_friedlander_scripted",
  "metadata": {
    "executive_name": "Peter Friedlander",
    "content_type": "Scripted Series",
    "submission_steps": [
      "Secure representation (agent or manager)",
      "Agent submits logline and one-pager",
      "Request for series bible and pilot script",
      "Pitch meeting scheduled (30-45 minutes)",
      "Follow-up materials if interested"
    ],
    "required_materials": {
      "logline": "1-2 sentences, under 50 words",
      "one_pager": "1 page PDF, single-spaced",
      "series_bible": "10-20 pages",
      "pilot_script": "50-65 pages, standard format"
    },
    "meeting_duration": "30-45 minutes",
    "decision_timeline": {
      "initial_response": "1-2 weeks",
      "development_decision": "4-8 weeks",
      "greenlight_decision": "3-6 months"
    },
    "preferences_loves": ["Character-driven", "Elevated genre", "International appeal"],
    "preferences_avoids": ["Procedurals", "Anthology", "Overly niche"],
    "source_url": "https://...",
    "last_updated": "2024-10-01",
    "layer": "pitch_requirements"
  }
}
```

**Text to Embed:**
```
Pitch requirements for Peter Friedlander (Scripted Series): Secure agent representation, submit logline and one-pager, then series bible (10-20 pages) and pilot script (50-65 pages). Pitch meeting is 30-45 minutes, conversational style. Loves character-driven, elevated genre content with international appeal. Avoids procedurals and anthology formats. Initial response in 1-2 weeks, development decision in 4-8 weeks, greenlight decision in 3-6 months.
```

**What Goes Here:**
- Step-by-step submission process
- Required materials and formats
- Pitch meeting structure
- Decision timelines
- Executive preferences (loves/avoids)
- Formatting requirements

**Update Frequency:** Quarterly (or when process changes)

---

### Layer 6: Packaging Intelligence (🔧 Structure Ready)

**Purpose:** Help users understand what talent/packaging makes projects more attractive

**Pinecone Namespace:** `packaging`

**Vector Metadata:**
```json
{
  "id": "packaging_peter_friedlander_drama",
  "metadata": {
    "executive_name": "Peter Friedlander",
    "content_type": "Scripted Drama",
    "showrunner_tier1": ["Shonda Rhimes", "Ryan Murphy", "Jenji Kohan"],
    "showrunner_tier2": ["Emerging showrunners with 1-2 successful series"],
    "showrunner_notes": "Values proven track record or unique voice",
    "director_preferences": ["Film directors transitioning to TV", "Distinctive visual style"],
    "cast_importance": "High - needs recognizable name for marketing",
    "cast_preference": "Star-driven preferred over ensemble",
    "international_appeal": "Critical",
    "production_company_importance": "High",
    "preferred_prodcos": ["21 Laps", "Shondaland", "Tomorrow Studios"],
    "successful_packages": [
      {
        "project": "The Diplomat",
        "package": "Debora Cahn + Keri Russell + Janice Williams",
        "why_worked": "Proven showrunner + Emmy-winning star + experienced producer"
      }
    ],
    "packaging_tips": [
      "Attach showrunner before pitching if possible",
      "Star attachment significantly increases greenlight chances",
      "International cast member helps with global appeal"
    ],
    "source_url": "https://...",
    "last_updated": "2024-10-01",
    "layer": "packaging"
  }
}
```

**Neo4j Nodes & Relationships:**
```cypher
// Create talent nodes
CREATE (t1:Talent {name: "Shonda Rhimes", role: "showrunner", tier: "tier_1"})
CREATE (t2:Talent {name: "Keri Russell", role: "actor", tier: "tier_1"})

// Link talent preferences to executive
MATCH (e:Executive {name: "Peter Friedlander"})
MATCH (t:Talent {name: "Shonda Rhimes"})
CREATE (e)-[:PREFERS {importance: "high"}]->(t)
```

**Text to Embed:**
```
Packaging intelligence for Peter Friedlander (Scripted Drama): Tier 1 showrunners include Shonda Rhimes, Ryan Murphy, Jenji Kohan. Values proven track record or unique voice. Prefers film directors transitioning to TV with distinctive visual style. Star-driven cast is critical for marketing, international appeal essential. Preferred production companies: 21 Laps, Shondaland, Tomorrow Studios. Successful package example: The Diplomat with Debora Cahn (showrunner), Keri Russell (star), Janice Williams (producer). Tips: Attach showrunner before pitching, star attachment significantly increases greenlight chances.
```

**What Goes Here:**
- Showrunner preferences (tier 1, tier 2)
- Director preferences
- Cast requirements (star vs ensemble)
- Production company preferences
- Successful package examples
- Packaging tips and strategies

**Update Frequency:** Quarterly (or when patterns change)

---

### Layer 7: Timing & Strategy (🔧 Structure Ready)

**Purpose:** Help users understand when to pitch (events, schedules, seasonal patterns)

**Pinecone Namespace:** `timing`

**Vector Metadata:**

**Type A: Industry Events**
```json
{
  "id": "event_busan_2024",
  "metadata": {
    "type": "industry_event",
    "event_name": "Busan International Film Festival",
    "start_date": "2024-10-02",
    "end_date": "2024-10-11",
    "location": "Busan, South Korea",
    "relevant_executives": ["Don Kang", "Kaata Sakamoto"],
    "opportunity_type": "In-person meetings",
    "notes": "Major Asian content market. Don Kang typically attends.",
    "layer": "timing"
  }
}
```

**Type B: Executive Schedules**
```json
{
  "id": "schedule_peter_friedlander",
  "metadata": {
    "type": "executive_schedule",
    "executive_name": "Peter Friedlander",
    "typical_availability": "Tuesdays-Thursdays",
    "busy_periods": ["May (Upfronts)", "December (Holidays)"],
    "best_time_to_pitch": "September-November",
    "notes": "Most responsive in fall during development season",
    "layer": "timing"
  }
}
```

**Type C: Seasonal Patterns**
```json
{
  "id": "seasonal_general",
  "metadata": {
    "type": "seasonal_pattern",
    "best_months": ["September", "October", "January", "February"],
    "avoid_months": ["December", "July", "August"],
    "reasons": "Avoid year-end holidays and summer vacation. Fall and early year are budget planning seasons.",
    "layer": "timing"
  }
}
```

**Neo4j Nodes & Relationships:**
```cypher
// Create event node
CREATE (ev:IndustryEvent {
  name: "Busan International Film Festival",
  start_date: date('2024-10-02'),
  end_date: date('2024-10-11'),
  location: "Busan, South Korea",
  opportunity_type: "In-person meetings",
  notes: "Major Asian content market"
})

// Link executives who attend
MATCH (e:Executive {name: "Don Kang"})
MATCH (ev:IndustryEvent {name: "Busan International Film Festival"})
CREATE (e)-[:ATTENDS]->(ev)
```

**Text to Embed:**
```
Busan International Film Festival, October 2-11, 2024, Busan, South Korea. Don Kang and Kaata Sakamoto typically attend. Major Asian content market with opportunities for in-person meetings. Best time to connect with Korean and Japanese content executives.
```

**What Goes Here:**
- Major industry events (festivals, conferences)
- Executive attendance patterns
- Best times to pitch (seasonal)
- Busy periods to avoid
- Executive typical availability

**Update Frequency:** Monthly (for events), Quarterly (for patterns)

---

### Layer 8: Success Metrics (🔧 Optional)

**Purpose:** Provide historical success rates and timelines

**Pinecone Namespace:** `success_metrics`

**Vector Metadata:**
```json
{
  "id": "metrics_peter_friedlander_drama",
  "metadata": {
    "executive_name": "Peter Friedlander",
    "content_type": "Scripted Drama",
    "greenlight_rate": 0.15,  // 15% of pitches greenlit
    "avg_decision_time_days": 120,
    "avg_development_time_months": 8,
    "successful_genres": ["Political Drama", "Thriller", "Limited Series"],
    "success_factors": [
      "Star attachment",
      "Proven showrunner",
      "International appeal"
    ],
    "layer": "success_metrics"
  }
}
```

**Text to Embed:**
```
Success metrics for Peter Friedlander (Scripted Drama): 15% greenlight rate, average 120 days for decision, 8 months development time. Most successful genres: political drama, thriller, limited series. Key success factors: star attachment, proven showrunner, international appeal.
```

**What Goes Here:**
- Greenlight rates by executive/genre
- Average decision timelines
- Success factors and patterns
- Genre performance data

**Update Frequency:** Annually (or when significant data available)

---

## Data Flow

### How Data Moves Through the System

```
User Query
    ↓
Persona Detection (LangGraph)
    ↓
Determine Needed Layers
    ↓
Layer 1: Query Pinecone "executives" → Get executive name
    ↓
Layer 2: Query Pinecone "quotes" → Get mandate/preferences
    ↓
Layer 3: Query Neo4j → Get production companies for executive
         Query Pinecone "production_companies" → Get submission details
    ↓
Layer 4: Query Neo4j → Get recent greenlights by executive
         Query Pinecone "greenlights" → Get project details
    ↓
Layer 5: Query Pinecone "pitch_requirements" → Get pitch format
    ↓
Layer 6: Query Pinecone "packaging" → Get talent preferences
    ↓
Layer 7: Query Pinecone "timing" → Get event schedules
    ↓
Generate Answer (GPT-5)
    ↓
Return to User
```

### Query Patterns

**Pattern 1: Executive Routing**
```python
# Query Pinecone executives namespace
results = pinecone_index.query(
    vector=embed("Who handles Korean content?"),
    namespace="executives",
    top_k=3,
    include_metadata=True
)
# Returns: Don Kang
```

**Pattern 2: Recent Greenlights**
```python
# First get executive name from Layer 1
executive_name = "Don Kang"

# Query Neo4j for recent greenlights
query = """
MATCH (e:Executive {name: $exec_name})-[r:GREENLIT]->(p:Project)
WHERE r.date > date('2024-01-01')
RETURN p.title, p.genre, r.date
ORDER BY r.date DESC
LIMIT 10
"""

# Or query Pinecone greenlights namespace
results = pinecone_index.query(
    vector=embed("What has Don Kang greenlit recently?"),
    namespace="greenlights",
    filter={"executive_name": "Don Kang"},
    top_k=10
)
```

**Pattern 3: Production Company Access**
```python
# Query Neo4j for production companies
query = """
MATCH (e:Executive {name: $exec_name})-[:WORKS_WITH]->(pc:ProductionCompany)
RETURN pc.name, pc.submission_method, pc.website
"""

# Or query Pinecone production_companies namespace
results = pinecone_index.query(
    vector=embed("What production companies work with Don Kang?"),
    namespace="production_companies",
    filter={"primary_executive": "Don Kang"},
    top_k=5
)
```

---

## Update Procedures

### Adding New Data

**For Pinecone:**

```python
from openai import OpenAI
import pinecone

# Initialize
client = OpenAI()
pc = pinecone.Pinecone(api_key="...")
index = pc.Index("mandate-wizard")

# Create embedding
text = "Studio Dragon is a major South Korean production company..."
embedding = client.embeddings.create(
    model="text-embedding-3-small",
    input=text
).data[0].embedding

# Upsert to Pinecone
index.upsert(
    vectors=[{
        "id": "prodco_studio_dragon",
        "values": embedding,
        "metadata": {
            "company_name": "Studio Dragon",
            "country": "South Korea",
            # ... all other metadata fields
            "layer": "production_companies"
        }
    }],
    namespace="production_companies"
)
```

**For Neo4j:**

```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    session.run("""
        CREATE (pc:ProductionCompany {
            name: $name,
            country: $country,
            has_netflix_deal: $has_deal
        })
    """, name="Studio Dragon", country="South Korea", has_deal=True)
    
    # Link to executive
    session.run("""
        MATCH (e:Executive {name: $exec_name})
        MATCH (pc:ProductionCompany {name: $company_name})
        CREATE (e)-[:WORKS_WITH {primary: true}]->(pc)
    """, exec_name="Don Kang", company_name="Studio Dragon")
```

### Bulk Import Scripts

See `/home/ubuntu/mandate_wizard_web_app/scripts/` for:
- `bulk_import_layer3.py` - Import production companies
- `bulk_import_layer4.py` - Import greenlights
- `bulk_import_layer5.py` - Import pitch requirements
- `bulk_import_layer6.py` - Import packaging intelligence
- `bulk_import_layer7.py` - Import timing data

---

## Summary: What Goes Where

### Pinecone (Vector Search)
- **Use for:** Semantic search, finding similar content
- **Stores:** Text embeddings + metadata
- **Organized by:** Namespaces (one per layer)
- **Query method:** Similarity search

### Neo4j (Graph Relationships)
- **Use for:** Relationship queries, structured data
- **Stores:** Nodes and relationships
- **Organized by:** Node types and relationship types
- **Query method:** Cypher queries

### When to Use Which

**Use Pinecone when:**
- User asks open-ended questions ("Who handles Korean content?")
- Need semantic similarity ("Find executives like Peter Friedlander")
- Searching across text content

**Use Neo4j when:**
- Need relationship traversal ("What production companies work with this executive?")
- Need structured queries ("Show all greenlights in last 6 months")
- Need to join multiple entity types

**Use Both when:**
- Complex queries requiring both semantic search and relationships
- Example: "What production companies in Korea have greenlit thrillers with Don Kang?"
  1. Pinecone: Find Don Kang (semantic)
  2. Neo4j: Get production companies (relationship)
  3. Neo4j: Filter by genre (structured)

---

**END OF DATABASE ARCHITECTURE DOCUMENT**

