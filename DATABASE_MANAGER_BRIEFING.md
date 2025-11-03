# Mandate Wizard: Database Manager Briefing

**Date:** October 26, 2025  
**Your Role:** Database Manager  
**Status:** Technical infrastructure 95% complete, data layers 30% complete

---

## 🎯 Executive Summary

You know Mandate Wizard in theory - now it's time to populate it with intelligence. The technical system is **fully operational** with LangChain, LangGraph, GPT-5, Mem0, and persona detection all working. Your job: **Fill Layers 3-8 with data**.

**What's Complete:**
- ✅ Layer 1: Executive Routing (266 executives)
- ✅ Layer 2: Executive Mandates (147 quotes)
- ✅ GPT-5 Responses API integration
- ✅ LangGraph 8-layer pathway system
- ✅ Persona detection (90% accuracy)
- ✅ Crisis mode detection
- ✅ All critical bugs fixed

**What You Need to Do:**
- 🔧 Layer 3: Production Companies (0/50 target)
- 🔧 Layer 4: Recent Greenlights (0/100 target)
- 🔧 Layer 5: Pitch Requirements (0/20 target)
- 🔧 Layer 6: Packaging Intelligence (0/15 target)
- 🔧 Layer 7: Timing & Strategy (0/30 target)

---

## 📦 What's in This Package

```
database_manager_package/
├── DATABASE_MANAGER_BRIEFING.md     ← YOU ARE HERE (Start here)
├── DATABASE_ARCHITECTURE.md         ← Technical specs (reference)
├── DATA_COLLECTION_PLAYBOOK.md      ← What data to collect
├── DATABASE_HANDOFF.md              ← Operational procedures
├── data/
│   ├── README.md                    ← Quick reference
│   ├── production_companies_EXAMPLE.json
│   ├── recent_greenlights_EXAMPLE.json
│   ├── production_companies.json    ← Fill this
│   ├── recent_greenlights.json      ← Fill this
│   ├── pitch_requirements.json      ← Fill this
│   ├── packaging_intelligence.json  ← Fill this
│   └── timing_strategy.json         ← Fill this
├── scripts/
│   ├── bulk_import_layer3.py        ← Import production companies
│   └── bulk_import_layer4.py        ← Import greenlights
└── import_data.py                   ← Validation tool
```

---

## 🚀 Your 5-Step Workflow

### **Step 1: Understand the Architecture**

**Read:** `DATABASE_ARCHITECTURE.md`

**Key Concepts:**
- **Pinecone** = Vector database for semantic search
- **Neo4j** = Graph database for relationships
- **Layers 3-8** = Intelligence layers you're populating
- **Embeddings** = Auto-generated from your data
- **Metadata** = Structured data you provide

**Databases:**
```
Pinecone: mandate-wizard/
├── production_companies/  ← Layer 3 (you fill)
├── greenlights/           ← Layer 4 (you fill)
├── pitch_requirements/    ← Layer 5 (you fill)
├── packaging/             ← Layer 6 (you fill)
└── timing/                ← Layer 7 (you fill)

Neo4j:
├── ProductionCompany nodes    ← Layer 3 (you create)
├── Project nodes              ← Layer 4 (you create)
├── (Executive)-[:WORKS_WITH]->(ProductionCompany)
└── (Executive)-[:GREENLIT]->(Project)
```

---

### **Step 2: Collect Data**

**Read:** `DATA_COLLECTION_PLAYBOOK.md`

**Priority Order:**

#### **🔥 PRIORITY 1: Layer 4 (Recent Greenlights)**
**Target:** 100+ greenlights from 2024

**Sources:**
- Deadline Hollywood: https://deadline.com/tag/netflix/
- Variety: https://variety.com/t/netflix/
- The Hollywood Reporter: https://www.hollywoodreporter.com/t/netflix/
- Netflix press releases: https://about.netflix.com/en/news

**What to Collect:**
- Project title
- Executive who greenlit it
- Greenlight date (YYYY-MM-DD)
- Genre, format, episode count
- Production company
- Showrunner, cast
- Budget range (if available)
- Source URL

**Save to:** `data/recent_greenlights.json`

**Example:**
```json
{
  "greenlights": [
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
  ]
}
```

---

#### **🔥 PRIORITY 2: Layer 3 (Production Companies)**
**Target:** 50+ companies with Netflix deals

**Sources:**
- IMDb Pro
- Production company websites
- Industry directories
- Netflix partnership announcements

**What to Collect:**
- Company name
- Country
- Specializations (genres)
- Netflix deal info (type, year, primary executive)
- Notable projects
- Submission policies
- Contact info

**Save to:** `data/production_companies.json`

**Example:**
```json
{
  "production_companies": [
    {
      "company_name": "Studio Dragon",
      "country": "South Korea",
      "specializations": ["Drama", "Thriller", "Romance"],
      "netflix_relationship": {
        "has_deal": true,
        "deal_type": "First-look deal",
        "deal_year": 2021,
        "primary_executive": "Don Kang",
        "secondary_executives": []
      },
      "notable_projects": [
        {
          "title": "Squid Game",
          "year": 2021,
          "genre": "Thriller"
        }
      ],
      "submission_info": {
        "accepts_unsolicited": false,
        "submission_method": "Through agent/manager only",
        "website": "https://www.studiodragon.net",
        "contact_email": ""
      },
      "notes": "Leading Korean drama producer"
    }
  ]
}
```

---

#### **📊 PRIORITY 3: Layer 5 (Pitch Requirements)**
**Target:** 20+ executive pitch processes

**Sources:**
- Industry blogs
- Showrunner interviews
- Agent/manager insights
- Industry panels

**What to Collect:**
- Executive name
- Content type
- Submission process (steps)
- Required materials (formats)
- Meeting format
- Decision timelines
- Preferences (loves/avoids)

**Save to:** `data/pitch_requirements.json`

---

#### **📊 PRIORITY 4: Layer 6 (Packaging Intelligence)**
**Target:** 15+ packaging patterns

**What to Collect:**
- Executive preferences for showrunners
- Director preferences
- Cast requirements
- Successful package examples

**Save to:** `data/packaging_intelligence.json`

---

#### **📊 PRIORITY 5: Layer 7 (Timing & Strategy)**
**Target:** 30+ events/schedules

**What to Collect:**
- Industry events (dates, attendees)
- Executive schedules
- Best times to pitch
- Seasonal patterns

**Save to:** `data/timing_strategy.json`

---

### **Step 3: Validate Your Data**

**Before importing**, validate your JSON files:

```bash
cd /home/ubuntu/mandate_wizard_web_app

# Validate JSON syntax
python3 -m json.tool data/recent_greenlights.json > /dev/null

# Validate data quality
python3 import_data.py
```

**Common Issues:**
- ❌ Trailing commas in JSON
- ❌ Executive names don't match database (use exact spelling)
- ❌ Dates not in YYYY-MM-DD format
- ❌ Missing required fields

**How to Check Executive Names:**
```bash
# Get list of all executives in database
# (Query Neo4j or check DATABASE_ARCHITECTURE.md)
```

**Critical:** Executive names must match EXACTLY:
- ✅ "Don Kang" (correct)
- ❌ "Don" (wrong - first name only)
- ❌ "Don Kong" (wrong - typo)

---

### **Step 4: Import to Databases**

**Run the bulk import scripts:**

#### **Layer 3: Production Companies**
```bash
cd /home/ubuntu/mandate_wizard_web_app
python3 scripts/bulk_import_layer3.py
```

**What it does:**
1. Loads `data/production_companies.json`
2. Generates embeddings for each company
3. Upserts vectors to Pinecone `production_companies` namespace
4. Creates `ProductionCompany` nodes in Neo4j
5. Creates `(Executive)-[:WORKS_WITH]->(ProductionCompany)` relationships

**Expected output:**
```
======================================================================
LAYER 3 BULK IMPORT: PRODUCTION COMPANIES
======================================================================

📂 Loading data from: .../production_companies.json
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

#### **Layer 4: Recent Greenlights**
```bash
python3 scripts/bulk_import_layer4.py
```

**What it does:**
1. Loads `data/recent_greenlights.json`
2. Generates embeddings for each greenlight
3. Upserts vectors to Pinecone `greenlights` namespace
4. Creates `Project` nodes in Neo4j
5. Creates `(Executive)-[:GREENLIT]->(Project)` relationships
6. Creates `(ProductionCompany)-[:PRODUCED]->(Project)` relationships

---

#### **Layers 5-7:**
Import scripts for these layers will be created as needed. The pattern is the same:
1. Load JSON
2. Generate embeddings
3. Upsert to Pinecone
4. Create nodes/relationships in Neo4j

---

### **Step 5: Verify Import**

#### **Check Pinecone:**

```python
import pinecone
import os

pc = pinecone.Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index("mandate-wizard")

# Check vector counts
stats = index.describe_index_stats()
print(stats)

# Should show:
# production_companies: 50 vectors
# greenlights: 100 vectors
# etc.
```

#### **Check Neo4j:**

```cypher
// Count production companies
MATCH (pc:ProductionCompany) RETURN count(pc)

// Count projects
MATCH (p:Project) RETURN count(p)

// Check relationships
MATCH (e:Executive)-[:WORKS_WITH]->(pc:ProductionCompany)
RETURN e.name, pc.name LIMIT 10

MATCH (e:Executive)-[:GREENLIT]->(p:Project)
RETURN e.name, p.title, p.greenlight_date
ORDER BY p.greenlight_date DESC
LIMIT 10
```

#### **Test in Web App:**

Go to the Mandate Wizard web app and ask:
- "What production companies work with Don Kang?"
- "What has Peter Friedlander greenlit recently?"
- "How do I pitch to Brandon Riegg?"

Verify answers use your new data.

---

## 📊 Progress Tracking

### **Current Status**

| Layer | Description | Status | Target | Priority |
|-------|-------------|--------|--------|----------|
| 1 | Executive Routing | ✅ Complete | 266 | N/A |
| 2 | Executive Mandates | ✅ Complete | 147 | N/A |
| 3 | Production Companies | 🔧 0 | 50+ | HIGH |
| 4 | Recent Greenlights | 🔧 0 | 100+ | CRITICAL |
| 5 | Pitch Requirements | 🔧 0 | 20+ | MEDIUM |
| 6 | Packaging Intelligence | 🔧 0 | 15+ | LOW |
| 7 | Timing & Strategy | 🔧 0 | 30+ | LOW |

### **Update This As You Go**

```
Layer 3: [          ] 0/50 (0%)
Layer 4: [          ] 0/100 (0%)
Layer 5: [          ] 0/20 (0%)
Layer 6: [          ] 0/15 (0%)
Layer 7: [          ] 0/30 (0%)
```

---

## 🎯 Success Criteria

### **Minimum Viable (MVP)**
- ✅ 50+ production companies (Layer 3)
- ✅ 100+ recent greenlights (Layer 4)
- ✅ 20+ pitch requirements (Layer 5)
- ✅ All imports successful
- ✅ 0 validation errors

### **Ideal Complete**
- ✅ 100+ production companies
- ✅ 200+ recent greenlights
- ✅ 50+ pitch requirements
- ✅ 15+ packaging intelligence entries
- ✅ 30+ timing/strategy entries

### **Quality Metrics**
- 0 JSON syntax errors
- <5% missing required fields
- 100% valid source URLs
- 100% executive name matches
- All imports successful

---

## 🆘 Troubleshooting

### **Issue: Import script fails with "Executive not found"**

**Cause:** Executive name doesn't match database exactly

**Solution:**
1. Query Neo4j for correct name:
   ```cypher
   MATCH (e:Executive) WHERE e.name CONTAINS "Don" RETURN e.name
   ```
2. Update your JSON with exact spelling
3. Re-run import

---

### **Issue: JSON syntax error**

**Cause:** Trailing comma, missing quote, etc.

**Solution:**
```bash
python3 -m json.tool data/your_file.json
```

Fix the error it reports, then re-validate.

---

### **Issue: Pinecone API error**

**Cause:** API key not set or invalid

**Solution:**
```bash
echo $PINECONE_API_KEY
# Should output your API key
# If empty, set it:
export PINECONE_API_KEY="your-key-here"
```

---

### **Issue: Neo4j connection error**

**Cause:** Neo4j not running or wrong credentials

**Solution:**
```bash
# Check Neo4j status
sudo systemctl status neo4j

# Restart if needed
sudo systemctl restart neo4j

# Check password
echo $NEO4J_PASSWORD
```

---

### **Issue: Embedding generation slow**

**Cause:** OpenAI API rate limits (normal)

**Solution:** Be patient. The script handles retries automatically. Each embedding takes 1-2 seconds, so 100 items = 2-3 minutes.

---

## 📞 Coordination

### **Your Responsibilities**
- ✅ Data collection (research)
- ✅ Data validation (quality checks)
- ✅ Database population (running import scripts)
- ✅ Data maintenance (updates, corrections)

### **Web App Developer's Responsibilities**
- ✅ Query logic (already built)
- ✅ Answer generation (GPT-5 integration done)
- ✅ User interface (working)
- ✅ Pathway navigation (LangGraph complete)

### **Communication Protocol**

**When you add new data:**
1. Run import scripts
2. Verify in Pinecone/Neo4j
3. Test queries in web app
4. Report completion with stats

**When you find issues:**
1. Document the problem clearly
2. Check if it's data or code
3. If data: Fix and re-import
4. If code: Report to web app developer

---

## 📚 Reference Documents

### **DATABASE_ARCHITECTURE.md**
- Complete Pinecone and Neo4j schemas
- Metadata structure for each layer
- Node and relationship types
- Query patterns
- 70+ pages of technical specifications

### **DATA_COLLECTION_PLAYBOOK.md**
- Detailed collection guidelines for each layer
- Research sources
- Quality validation criteria
- Field-by-field requirements
- 60+ pages of collection guidance

### **DATABASE_HANDOFF.md**
- Operational procedures
- Step-by-step workflows
- Verification queries
- Troubleshooting guide
- Progress tracking

### **data/README.md**
- Quick reference guide
- Copy-paste templates
- Validation commands
- Progress checklist

---

## 🚀 Getting Started (Right Now)

### **Immediate Actions:**

1. **Read DATABASE_ARCHITECTURE.md** (30 min)
   - Understand Pinecone and Neo4j structure
   - See what goes in each layer

2. **Read DATA_COLLECTION_PLAYBOOK.md** (30 min)
   - Learn what data to collect
   - Understand quality standards

3. **Start Collecting Layer 4 Data** (2-3 hours)
   - Go to Deadline Hollywood
   - Search "Netflix greenlight 2024"
   - Fill `data/recent_greenlights.json` with 10 entries

4. **Validate Your Data** (5 min)
   ```bash
   python3 import_data.py
   ```

5. **Import to Databases** (5 min)
   ```bash
   python3 scripts/bulk_import_layer4.py
   ```

6. **Verify Import** (10 min)
   - Check Pinecone dashboard
   - Query Neo4j
   - Test in web app

7. **Scale Up** (ongoing)
   - Collect 100+ greenlights
   - Move to Layer 3 (production companies)
   - Continue through Layers 5-7

---

## 💡 Pro Tips

### **Data Collection**

1. **Use multiple sources** - Cross-reference for accuracy
2. **Save source URLs** - Essential for verification
3. **Batch collect** - Gather 10-20 entries, then validate/import
4. **Start recent** - Focus on 2024 data first
5. **Be consistent** - Use same format for all entries

### **Quality Control**

1. **Validate early** - Run `import_data.py` after every 10 entries
2. **Check executive names** - Query Neo4j to verify spelling
3. **Test queries** - After each import, test in web app
4. **Document issues** - Keep a log of problems and solutions
5. **Iterate quickly** - Small batches = faster feedback

### **Efficiency**

1. **Use templates** - Copy-paste from EXAMPLE files
2. **Automate where possible** - Scripts handle complexity
3. **Focus on high-value data** - Layer 4 first, then 3
4. **Don't perfect early** - Get MVP done, then improve
5. **Track progress** - Update progress tracker daily

---

## 🎯 Your Mission

**The Mandate Wizard technical system is 95% complete and working beautifully. It just needs data.**

Your job is to populate Layers 3-8 with high-quality intelligence that will make the system genuinely useful for industry professionals trying to navigate the Netflix pitch process.

**Start with Layer 4 (Recent Greenlights)** - this is the most requested data and has the highest impact. Collect 100+ greenlights from 2024, import them, and watch the system come alive.

**You've got all the tools you need. The databases are ready. Let's fill them with intelligence!** 🚀

---

## ✅ Quick Start Checklist

- [ ] Read DATABASE_ARCHITECTURE.md
- [ ] Read DATA_COLLECTION_PLAYBOOK.md
- [ ] Collect 10 greenlights (Layer 4)
- [ ] Validate with `python3 import_data.py`
- [ ] Import with `python3 scripts/bulk_import_layer4.py`
- [ ] Verify in Pinecone and Neo4j
- [ ] Test queries in web app
- [ ] Scale to 100+ greenlights
- [ ] Move to Layer 3 (production companies)
- [ ] Continue through Layers 5-7

---

**END OF BRIEFING - YOU'RE READY TO GO!**

