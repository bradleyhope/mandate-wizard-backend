# Mandate Wizard - Quick Reference Card

## Access

**Web Interface:** https://5000-iy1gh94d7s437eutwzpcu-aa64bff1.manusvm.computer

**Server Location:** `/home/ubuntu/mandate_wizard_web_app/`

**Logs:** `/tmp/mandate_wizard.log`

---

## Quick Commands

### Start Server
```bash
cd /home/ubuntu/mandate_wizard_web_app
nohup python3 app.py > /tmp/mandate_wizard.log 2>&1 &
```

### Stop Server
```bash
pkill -f "python3 app.py"
```

### View Logs
```bash
tail -f /tmp/mandate_wizard.log
```

### Check Status
```bash
curl http://localhost:5000/stats
```

---

## Database Info

**Pinecone:**
- Index: `netflix-mandate-wizard`
- Vectors: 1,044 embeddings
- API Key: In `app.py`

**Neo4j:**
- URI: `neo4j+s://0dd3462a.databases.neo4j.io`
- Executives: 154 loaded
- Regions: 25 indexed
- Credentials: In `app.py`

---

## API Endpoints

### POST /ask
Query the system:
```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who handles Korean content?"}'
```

### GET /stats
Get database statistics:
```bash
curl http://localhost:5000/stats
```

---

## System Architecture

```
User Question
    ↓
Intent Classification (ROUTING/STRATEGIC/COMPARATIVE)
    ↓
Attribute Extraction (region, format, genre)
    ↓
Parallel Retrieval:
    ├─ Neo4j Graph Search → Executives
    └─ Pinecone Vector Search → Context
    ↓
Fusion & Ranking
    ↓
GPT-4.1-mini Answer Generation
    ↓
Structured Answer
```

---

## Key Files

- `app.py` - Flask web server
- `hybridrag_engine_pinecone.py` - Query engine
- `templates/index.html` - Web interface
- `requirements.txt` - Dependencies
- `DEPLOYMENT_GUIDE.md` - Full documentation

---

## Performance

- Query time: 3-5 seconds
- Success rate: 72-76%
- Executives: 154 loaded
- Vectors: 1,044 chunks

---

## Dependencies

- pinecone-client==3.0.0
- neo4j==5.14.0
- sentence-transformers==5.1.2
- openai==2.6.0
- flask==3.0.0
- numpy==1.26.4
- pandas==2.0.3

---

## Troubleshooting

**Server not responding?**
```bash
ps aux | grep app.py  # Check if running
tail -50 /tmp/mandate_wizard.log  # Check logs
```

**Database connection issues?**
- Check credentials in `app.py`
- Verify network connectivity
- Check logs for specific errors

**Slow queries?**
- Normal: 3-5 seconds per query
- Check Pinecone connection
- Monitor LLM API rate limits

---

**Status:** ✓ Production Ready  
**Version:** 1.0  
**Date:** October 23, 2025

