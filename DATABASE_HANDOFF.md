# Mandate Wizard: Database Management Handoff

**Date:** October 26, 2025  
**Your Role:** Database Manager - You populate and maintain the intelligence layers  
**Other Role:** Web App Developer - Focuses on querying and logic

---

## 🎯 Your Mission

You are responsible for **populating Layers 3-8** of the Mandate Wizard database with high-quality intelligence data. The technical infrastructure is complete - you just need to fill it with content.

**Your databases:**
- **Pinecone** (Vector database for semantic search)
- **Neo4j** (Graph database for relationships)

**Your tools:**
- Bulk import scripts (automated)
- JSON data files (your input format)
- Validation scripts (quality checks)

---

## 📚 Essential Reading (In Order)

1. **[DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)** - Complete database specification
2. **[DATA_COLLECTION_PLAYBOOK.md](DATA_COLLECTION_PLAYBOOK.md)** - What data to collect
3. **[HANDOFF_TO_DATA_COLLECTION.md](HANDOFF_TO_DATA_COLLECTION.md)** - Workflow and priorities
4. **[data/README.md](data/README.md)** - Quick reference

---

## 🗄️ Database Structure Overview

### Pinecone (Vector Search)

**What it does:** Enables semantic search across all content

**Structure:**
```
mandate-wizard/
├── executives/          ✅ Complete (Layer 1)
├── quotes/              ✅ Complete (Layer 2)
├── production_companies/🔧 Empty (Layer 3) - YOUR JOB
├── greenlights/         🔧 Empty (Layer 4) - YOUR JOB
├── pitch_requirements/  🔧 Empty (Layer 5) - YOUR JOB
├── packaging/           🔧 Empty (Layer 6) - YOUR JOB
└── timing/              🔧 Empty (Layer 7) - YOUR JOB
```

**Each vector contains:**
- **ID:** Unique identifier (e.g., "prodco_studio_dragon")
- **Values:** 1536-dimensional embedding (auto-generated)
- **Metadata:** Structured data (you provide this)

### Neo4j (Graph Relationships)

**What it does:** Stores structured relationships between entities

**Node Types:**
- `Executive` ✅ Complete
- `ProductionCompany` 🔧 Empty - YOUR JOB
- `Project` 🔧 Empty - YOUR JOB
- `Talent` 🔧 Empty - YOUR JOB
- `IndustryEvent` 🔧 Empty - YOUR JOB

**Relationship Types:**
- `(Executive)-[:WORKS_WITH]->(ProductionCompany)` - YOUR JOB
- `(Executive)-[:GREENLIT]->(Project)` - YOUR JOB
- `(ProductionCompany)-[:PRODUCED]->(Project)` - YOUR JOB
- `(Executive)-[:ATTENDS]->(IndustryEvent)` - YOUR JOB

---

## 🚀 Your Workflow

### Step 1: Collect Data (Use Other Tools)

Follow the [DATA_COLLECTION_PLAYBOOK.md](DATA_COLLECTION_PLAYBOOK.md) to collect data and save it to JSON files in `/home/ubuntu/mandate_wizard_web_app/data/`.

**Priority Order:**
1. `recent_greenlights.json` (Layer 4) - HIGHEST PRIORITY
2. `production_companies.json` (Layer 3) - CRITICAL
3. `pitch_requirements.json` (Layer 5) - HIGH VALUE
4. `packaging_intelligence.json` (Layer 6) - NICE TO HAVE
5. `timing_strategy.json` (Layer 7) - NICE TO HAVE

### Step 2: Validate Data

Before importing, validate your JSON files:

```bash
cd /home/ubuntu/mandate_wizard_web_app
python3 import_data.py
```

This will check:
- ✅ JSON syntax is valid
- ✅ Required fields are present
- ✅ Dates are in correct format (YYYY-MM-DD)
- ✅ Executive names match database

Fix any errors before proceeding.

### Step 3: Import to Databases

Use the bulk import scripts to load data into both Pinecone and Neo4j:

**Layer 3 (Production Companies):**
```bash
cd /home/ubuntu/mandate_wizard_web_app
python3 scripts/bulk_import_layer3.py
```

**Layer 4 (Recent Greenlights):**
```bash
python3 scripts/bulk_import_layer4.py
```

**Layer 5-7:** (Scripts to be created as needed)

### Step 4: Verify Import

**Check Pinecone:**
- Go to Pinecone dashboard
- Verify vectors were created in correct namespace
- Check vector count matches your data

**Check Neo4j:**
```cypher
// Count production companies
MATCH (pc:ProductionCompany) RETURN count(pc)

// Count projects
MATCH (p:Project) RETURN count(p)

// Check relationships
MATCH (e:Executive)-[:WORKS_WITH]->(pc:ProductionCompany)
RETURN e.name, pc.name LIMIT 10
```

### Step 5: Test in Web App

Ask test queries in the web app:
- "What production companies work with Don Kang?"
- "What has Peter Friedlander greenlit recently?"
- "How do I pitch to Brandon Riegg?"

Verify answers use your new data.

---

## 📋 Layer-by-Layer Guide

### Layer 3: Production Companies

**What Goes Here:**
- Production company profiles
- Netflix deal information
- Submission policies
- Contact information
- Executive relationships

**JSON File:** `data/production_companies.json`

**Import Script:** `scripts/bulk_import_layer3.py`

**Example Entry:**
```json
{
  "company_name": "Studio Dragon",
  "country": "South Korea",
  "specializations": ["Drama", "Thriller"],
  "netflix_relationship": {
    "has_deal": true,
    "deal_type": "First-look deal",
    "deal_year": 2021,
    "primary_executive": "Don Kang"
  },
  "notable_projects": [
    {"title": "Squid Game", "year": 2021, "genre": "Thriller"}
  ],
  "submission_info": {
    "accepts_unsolicited": false,
    "submission_method": "Through agent/manager only",
    "website": "https://www.studiodragon.net"
  }
}
```

**What Happens When You Import:**
1. **Pinecone:** Vector created in `production_companies` namespace
2. **Neo4j:** `ProductionCompany` node created
3. **Neo4j:** `(Executive)-[:WORKS_WITH]->(ProductionCompany)` relationship created

**Target:** 50+ companies

---

### Layer 4: Recent Greenlights

**What Goes Here:**
- Projects greenlit in last 12 months
- Executive who greenlit it
- Production details
- Budget information
- Key talent

**JSON File:** `data/recent_greenlights.json`

**Import Script:** `scripts/bulk_import_layer4.py`

**Example Entry:**
```json
{
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
  "notes": "Renewal after strong Season 1 performance"
}
```

**What Happens When You Import:**
1. **Pinecone:** Vector created in `greenlights` namespace
2. **Neo4j:** `Project` node created
3. **Neo4j:** `(Executive)-[:GREENLIT]->(Project)` relationship created
4. **Neo4j:** `(ProductionCompany)-[:PRODUCED]->(Project)` relationship created

**Target:** 100+ greenlights

---

### Layer 5: Pitch Requirements

**What Goes Here:**
- Pitch process by executive
- Required materials
- Meeting format
- Decision timelines
- Preferences

**JSON File:** `data/pitch_requirements.json`

**Import Script:** (To be created)

**Example Entry:**
```json
{
  "executive_name": "Peter Friedlander",
  "content_type": "Scripted Series",
  "submission_process": {
    "step_1": "Secure representation (agent or manager)",
    "step_2": "Agent submits logline and one-pager",
    "step_3": "Request for series bible and pilot script"
  },
  "required_materials": {
    "logline": {
      "required": true,
      "format": "1-2 sentences, under 50 words"
    },
    "one_pager": {
      "required": true,
      "format": "1 page PDF, single-spaced"
    }
  },
  "pitch_meeting_format": {
    "duration": "30-45 minutes",
    "presentation_style": "Conversational, not formal"
  },
  "decision_timeline": {
    "initial_response": "1-2 weeks",
    "development_decision": "4-8 weeks",
    "greenlight_decision": "3-6 months"
  },
  "preferences": {
    "loves": ["Character-driven", "Elevated genre"],
    "avoids": ["Procedurals", "Anthology"]
  }
}
```

**What Happens When You Import:**
1. **Pinecone:** Vector created in `pitch_requirements` namespace

**Target:** 20+ entries

---

### Layer 6: Packaging Intelligence

**What Goes Here:**
- Showrunner preferences
- Director preferences
- Cast requirements
- Production company preferences
- Successful package examples

**JSON File:** `data/packaging_intelligence.json`

**Import Script:** (To be created)

**Target:** 15+ entries

---

### Layer 7: Timing & Strategy

**What Goes Here:**
- Industry events
- Executive schedules
- Best times to pitch
- Seasonal patterns

**JSON File:** `data/timing_strategy.json`

**Import Script:** (To be created)

**Target:** 20 events + 10 schedules

---

## 🔧 Bulk Import Scripts

### What They Do

1. **Load JSON data** from `data/` directory
2. **Generate embeddings** using OpenAI API
3. **Upsert to Pinecone** (vector database)
4. **Create nodes in Neo4j** (graph database)
5. **Create relationships** between entities
6. **Validate** and report errors

### How to Use

```bash
# Layer 3: Production Companies
python3 scripts/bulk_import_layer3.py

# Layer 4: Recent Greenlights
python3 scripts/bulk_import_layer4.py

# Layer 5-7: (Scripts to be created as needed)
```

### What to Expect

**Output:**
```
======================================================================
LAYER 3 BULK IMPORT: PRODUCTION COMPANIES
======================================================================

📂 Loading data from: /home/ubuntu/mandate_wizard_web_app/data/production_companies.json
✅ Loaded 50 production companies

======================================================================
IMPORTING TO PINECONE
======================================================================

Processing 1/50: Studio Dragon
  Text: Studio Dragon is a production company based in South Korea...
  ✅ Prepared vector: prodco_studio_dragon

...

📤 Upserting 50 vectors to Pinecone...
✅ Successfully imported 50 production companies to Pinecone

======================================================================
IMPORTING TO NEO4J
======================================================================

Processing 1/50: Studio Dragon
  ✅ Created ProductionCompany node
  ✅ Linked to executive: Don Kang

...

✅ Successfully imported 50 production companies to Neo4j

======================================================================
IMPORT COMPLETE
======================================================================
✅ 50 production companies imported successfully
```

---

## ✅ Quality Standards

### Before Importing

**JSON Validation:**
```bash
python3 -m json.tool data/production_companies.json > /dev/null
```

**Data Validation:**
```bash
python3 import_data.py
```

### Data Quality Checklist

- [ ] All required fields filled in
- [ ] Dates in YYYY-MM-DD format
- [ ] Executive names match exactly (Don Kang, not "Don")
- [ ] Source URLs are valid
- [ ] No trailing commas in JSON
- [ ] Proper quote escaping
- [ ] No duplicate entries

### Executive Name Matching

**CRITICAL:** Executive names must match EXACTLY what's in the database.

**Correct:**
- Don Kang
- Peter Friedlander
- Francisco Ramos
- Brandon Riegg

**Wrong:**
- Don Kong (typo)
- Peter F. (abbreviated)
- Francisco (first name only)
- Brandon (first name only)

**How to Check:**
```cypher
// Get all executive names
MATCH (e:Executive) RETURN e.name ORDER BY e.name
```

---

## 🔍 Verification Queries

### Pinecone

```python
import pinecone
import os

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("mandate-wizard")

# Check vector count by namespace
stats = index.describe_index_stats()
print(stats)

# Query a namespace
results = index.query(
    vector=[0.1] * 1536,  # dummy vector
    namespace="production_companies",
    top_k=5,
    include_metadata=True
)
print(results)
```

### Neo4j

```cypher
// Count all nodes by type
MATCH (n) RETURN labels(n), count(n)

// Check production companies
MATCH (pc:ProductionCompany)
RETURN pc.name, pc.country, pc.has_netflix_deal
LIMIT 10

// Check greenlights
MATCH (p:Project)
RETURN p.title, p.genre, p.greenlight_date
ORDER BY p.greenlight_date DESC
LIMIT 10

// Check relationships
MATCH (e:Executive)-[r:WORKS_WITH]->(pc:ProductionCompany)
RETURN e.name, type(r), pc.name
LIMIT 10

MATCH (e:Executive)-[r:GREENLIT]->(p:Project)
RETURN e.name, p.title, r.date
ORDER BY r.date DESC
LIMIT 10
```

---

## 📊 Progress Tracking

### Current Status

**Layer 1 (Executive Routing):** ✅ Complete (266 executives)  
**Layer 2 (Executive Mandates):** ✅ Complete (147 quotes)  
**Layer 3 (Production Companies):** 🔧 0 / 50 target  
**Layer 4 (Recent Greenlights):** 🔧 0 / 100 target  
**Layer 5 (Pitch Requirements):** 🔧 0 / 20 target  
**Layer 6 (Packaging Intelligence):** 🔧 0 / 15 target  
**Layer 7 (Timing & Strategy):** 🔧 0 / 30 target  

### Update This As You Go

```
Layer 3: [    ] 0/50 (0%)
Layer 4: [    ] 0/100 (0%)
Layer 5: [    ] 0/20 (0%)
Layer 6: [    ] 0/15 (0%)
Layer 7: [    ] 0/30 (0%)
```

---

## 🆘 Troubleshooting

### Issue: Import script fails with "Executive not found"

**Cause:** Executive name doesn't match database  
**Solution:** Check exact spelling, query Neo4j for correct name

### Issue: JSON syntax error

**Cause:** Trailing comma, missing quote, etc.  
**Solution:** Use `python3 -m json.tool file.json` to validate

### Issue: Pinecone API error

**Cause:** API key not set or invalid  
**Solution:** Check `PINECONE_API_KEY` environment variable

### Issue: Neo4j connection error

**Cause:** Neo4j not running or wrong credentials  
**Solution:** Check Neo4j status, verify `NEO4J_PASSWORD`

### Issue: Embedding generation slow

**Cause:** OpenAI API rate limits  
**Solution:** Normal, be patient. Script handles retries.

---

## 📞 Coordination with Web App Developer

### What You Own

- **Data collection** (research, JSON files)
- **Data validation** (quality checks)
- **Database population** (running import scripts)
- **Data maintenance** (updates, corrections)

### What They Own

- **Query logic** (how data is retrieved)
- **Answer generation** (GPT-5 prompts)
- **User interface** (web app)
- **Pathway logic** (LangGraph workflows)

### Communication

**When you add new data:**
1. Run import scripts
2. Verify in Pinecone/Neo4j
3. Notify web app developer
4. They test queries

**When you find issues:**
1. Document the problem
2. Check if it's data or code
3. If data: Fix and re-import
4. If code: Notify web app developer

---

## 🎯 Success Criteria

### Minimum Viable

- 50+ production companies (Layer 3)
- 100+ recent greenlights (Layer 4)
- 20+ pitch requirements (Layer 5)

### Ideal Complete

- 100+ production companies
- 200+ recent greenlights
- 50+ pitch requirements
- 15+ packaging intelligence entries
- 30+ timing/strategy entries

### Quality Metrics

- 0 JSON syntax errors
- <5% missing required fields
- 100% valid source URLs
- 100% executive name matches
- All imports successful

---

## 🚀 Getting Started (Right Now)

1. **Read [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md)**
   - Understand Pinecone and Neo4j structure
   - See what goes in each layer

2. **Read [DATA_COLLECTION_PLAYBOOK.md](DATA_COLLECTION_PLAYBOOK.md)**
   - Learn what data to collect
   - Understand quality standards

3. **Start Collecting Layer 4 Data**
   - Go to Deadline Hollywood
   - Search "Netflix greenlight 2024"
   - Fill `data/recent_greenlights.json`

4. **Validate Your Data**
   ```bash
   python3 import_data.py
   ```

5. **Import to Databases**
   ```bash
   python3 scripts/bulk_import_layer4.py
   ```

6. **Verify Import**
   - Check Pinecone dashboard
   - Query Neo4j
   - Test in web app

7. **Repeat for Layers 3, 5, 6, 7**

---

**You've got this! The databases are ready - they just need your data!** 🚀

---

**END OF DATABASE HANDOFF DOCUMENT**

