# Migration Guide: JSON-Based to Database-Only Architecture

**Version:** 1.0 → 1.1  
**Date:** October 23, 2025  
**Type:** Architecture Update

---

## Overview

The Mandate Wizard has been updated from a **hybrid architecture** (local JSON files + databases) to a **database-only architecture** (Pinecone + Neo4j only).

---

## What Changed

### Before (v1.0)

**Architecture:**
```
User Query
    ↓
HybridRAG Engine
    ↓
┌─────────────────────────────────────┐
│ Load JSON files from disk           │
│ /home/ubuntu/graphrag/json_entities │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Query Pinecone (optional)           │
│ Query Neo4j (optional)              │
└─────────────────────────────────────┘
    ↓
Answer Generation
```

**Data Flow:**
- JSON files loaded into memory at startup
- Databases used as supplementary sources
- Required `/home/ubuntu/graphrag/json_entities/` directory

### After (v1.1)

**Architecture:**
```
User Query
    ↓
HybridRAG Engine
    ↓
┌─────────────────────────────────────┐
│ Query Pinecone (required)           │
│ Query Neo4j (required)              │
└─────────────────────────────────────┘
    ↓
Answer Generation
```

**Data Flow:**
- No JSON files loaded at runtime
- Databases are primary and only data sources
- No local directory dependencies

---

## Why This Change?

### Benefits

1. **Scalability**
   - Databases handle millions of entities
   - No memory constraints from loading JSON files
   - Easier to scale horizontally

2. **Consistency**
   - Single source of truth (databases)
   - No sync issues between JSON files and databases
   - Easier to update data (just update databases)

3. **Deployment Simplicity**
   - No need to sync JSON files to servers
   - Smaller deployment package
   - Easier to manage in production

4. **Performance**
   - Optimized database queries
   - No startup time loading JSON files
   - Faster cold starts

### Trade-offs

1. **Network Dependency**
   - Requires database connectivity
   - Cannot run offline
   - Database outages affect service

2. **Latency**
   - ~500ms for Pinecone queries
   - Acceptable for this use case

---

## Migration Steps

### If You're Running v1.0

**Step 1: Verify Database Uploads**

Ensure all entities are uploaded to databases:

```bash
cd /home/ubuntu/mandate_wizard_starter_package
python3 utils/sync_all_entities.py
```

**Step 2: Update Application Code**

Replace `hybridrag_engine_pinecone.py` with the new version (v1.1).

**Step 3: Remove JSON Directory Dependency**

The application no longer requires `/home/ubuntu/graphrag/json_entities/`. You can keep it for backup, but it won't be used at runtime.

**Step 4: Restart Application**

```bash
# Stop old version
pkill -f "python3 app.py"

# Start new version
cd /home/ubuntu/mandate_wizard_web_app
nohup python3 app.py > /tmp/mandate_wizard.log 2>&1 &
```

**Step 5: Verify**

Check logs to confirm database connections:

```bash
tail -30 /tmp/mandate_wizard.log | grep "✓"
```

You should see:
```
✓ Connected to Neo4j
✓ HybridRAG V3 (Pinecone + Neo4j) initialized
✓ Vector DB: 1044 vectors in Pinecone
✓ Loaded 165 persons from Neo4j
```

---

## Code Changes

### Removed Features

**1. JSON Entity Loading**

Removed from `hybridrag_engine_pinecone.py`:
```python
# OLD CODE (removed)
def _load_entities_from_json(self, json_entities_dir: str):
    """Load entities from JSON files"""
    for json_file in Path(json_entities_dir).glob("*.json"):
        with open(json_file) as f:
            entity = json.load(f)
            if entity['entity_type'] == 'person':
                self.persons.append(entity)
```

**2. Local File Dependencies**

Removed parameter from `__init__`:
```python
# OLD CODE (removed)
def __init__(self, json_entities_dir: str, pinecone_api_key: str, ...):
    self.json_entities_dir = json_entities_dir
    self._load_entities_from_json(json_entities_dir)
```

**NEW CODE:**
```python
def __init__(self, pinecone_api_key: str, pinecone_index_name: str = "netflix-mandate-wizard",
             neo4j_uri: str = None, neo4j_user: str = None, neo4j_password: str = None):
    # No json_entities_dir parameter
    # Load persons from Neo4j instead
```

### Added Features

**1. Neo4j Person Loading**

Added to `hybridrag_engine_pinecone.py`:
```python
def _load_persons_from_neo4j(self):
    """Load all person entities from Neo4j and build indexes"""
    with self.neo4j_driver.session() as session:
        result = session.run("""
            MATCH (p:Person)
            RETURN p.entity_id, p.name, p.current_title, 
                   p.region, p.bio, p.mandate, p.reports_to
        """)
        for record in result:
            person = {...}
            self.persons_cache.append(person)
```

**2. Regional Indexing**

Added regional indexing for faster queries:
```python
# Index by region
region = person.get('region', 'global')
if region:
    region = region.lower()
    if region not in self.persons_by_region:
        self.persons_by_region[region] = []
    self.persons_by_region[region].append(person)
```

---

## Updated Workflow

### Entity Extraction & Upload (Offline)

This workflow is **unchanged**:

```
1. Research executives
    ↓
2. Extract entities using LLM
    ↓
3. Save to JSON files (local, temporary)
    ↓
4. Upload to databases using sync_all_entities.py
    ↓
5. JSON files can be archived (no longer needed at runtime)
```

### Query Processing (Runtime)

This workflow is **changed**:

**OLD:**
```
1. Load JSON files at startup
2. Query databases (optional)
3. Combine results
4. Generate answer
```

**NEW:**
```
1. Query Pinecone (required)
2. Query Neo4j (required)
3. Combine results
4. Generate answer
```

---

## Testing the Migration

### Test 1: Database Connectivity

```bash
curl https://5000-iy1gh94d7s437eutwzpcu-aa64bff1.manusvm.computer/stats
```

Expected output:
```json
{
  "persons": 165,
  "regions": 27,
  "pinecone_vectors": 1044,
  "success": true
}
```

### Test 2: Query Processing

```bash
curl -X POST https://5000-iy1gh94d7s437eutwzpcu-aa64bff1.manusvm.computer/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who handles Korean content at Netflix?"}'
```

Expected: Answer mentioning Korean executives

### Test 3: Regional Routing

```bash
curl -X POST https://5000-iy1gh94d7s437eutwzpcu-aa64bff1.manusvm.computer/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "i have a true crime story set in saudi arabia, what should i do"}'
```

Expected: Answer routing to MENA regional director (Nuha El Tayeb)

---

## Rollback Plan

If you need to rollback to v1.0:

**Step 1: Restore Old Code**

```bash
# Restore old hybridrag_engine_pinecone.py from backup
cp hybridrag_engine_pinecone.py.backup hybridrag_engine_pinecone.py
```

**Step 2: Ensure JSON Files Exist**

```bash
# Verify JSON files are present
ls -la /home/ubuntu/graphrag/json_entities/
```

**Step 3: Restart Application**

```bash
pkill -f "python3 app.py"
cd /home/ubuntu/mandate_wizard_web_app
nohup python3 app.py > /tmp/mandate_wizard.log 2>&1 &
```

---

## FAQ

### Q: Do I need to keep the JSON files?

**A:** No, not for runtime. JSON files are only needed during the extraction/upload pipeline. Once entities are uploaded to databases, JSON files can be archived or deleted.

**Recommendation:** Keep JSON files as backup in case you need to re-upload or migrate to a different database.

### Q: What happens if Neo4j is down?

**A:** The application will fall back to Pinecone-only mode. You'll see a warning in logs:

```
⚠ Neo4j connection failed: ...
  Continuing with Pinecone only...
```

Queries will still work, but regional routing may be less accurate.

### Q: Can I still use local JSON files?

**A:** Not with v1.1. If you need local JSON file support, use v1.0 or modify the code to add JSON loading back.

### Q: How do I update entity data?

**A:** Update the JSON files, then re-run `sync_all_entities.py` to upload to databases. Changes will be reflected immediately (no application restart needed).

---

## Support

For questions or issues with the migration:

1. Check logs: `tail -f /tmp/mandate_wizard.log`
2. Review `ARCHITECTURE.md` for detailed architecture documentation
3. Review `FIX_SUMMARY.md` for recent fixes and improvements
4. Test with sample queries to verify functionality

---

**Migration Status:** ✓ Complete  
**Current Version:** 1.1 (Database-Only Architecture)  
**Production Ready:** Yes

