# 🚂 Railway.app Deployment Guide

Complete guide to deploying Mandate Wizard Backend on Railway.app.

## Overview

This backend requires:
1. **Railway** - Flask app + optional Redis
2. **Neo4j Aura** - Managed Neo4j database (external)
3. **Pinecone** - Vector database (external)
4. **OpenAI API** - LLM access (external)

**Estimated Cost:**
- Railway: $20-50/month (depends on usage)
- Neo4j Aura: Free tier available (or $65+/month)
- Pinecone: Free tier available (or $70+/month)
- OpenAI: Pay-per-use (~$50-200/month depending on queries)

---

## Step 1: Set Up External Services

### 1.1 Neo4j Aura (Graph Database)

1. Go to https://console.neo4j.io/
2. Create a new instance:
   - **Name:** mandate-wizard-neo4j
   - **Region:** Choose closest to your users
   - **Tier:** Free tier OK for testing, Professional for production
3. Save the credentials:
   ```
   NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=<generated-password>
   ```
4. Import your data (executives, greenlights, etc.)

### 1.2 Pinecone (Vector Database)

1. Go to https://www.pinecone.io/
2. Create a project and index:
   - **Index name:** mandate-wizard
   - **Dimensions:** 384 (for sentence-transformers)
   - **Metric:** cosine
3. Save API key:
   ```
   PINECONE_API_KEY=pcsk_xxxxx
   PINECONE_INDEX_NAME=mandate-wizard
   PINECONE_ENVIRONMENT=gcp-starter (or your environment)
   ```

### 1.3 OpenAI API

1. Go to https://platform.openai.com/
2. Create API key
3. Save:
   ```
   OPENAI_API_KEY=sk-xxxxx
   ```

---

## Step 2: Deploy to Railway

### 2.1 Connect GitHub Repository

1. Go to https://railway.app/
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose: `bradleyhope/mandate-wizard-backend`
5. Railway will auto-detect the Dockerfile

### 2.2 Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

#### Required Variables

```bash
# Neo4j Configuration
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Pinecone Configuration
PINECONE_API_KEY=pcsk_xxxxx
PINECONE_INDEX_NAME=mandate-wizard
PINECONE_ENVIRONMENT=gcp-starter

# OpenAI Configuration
OPENAI_API_KEY=sk-xxxxx

# Ghost CMS (if using authentication)
GHOST_ADMIN_API_KEY=your-ghost-admin-key
GHOST_API_URL=https://your-ghost-site.com
GHOST_CONTENT_API_KEY=your-ghost-content-key

# Application Settings
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

#### Optional Variables (Advanced Features)

```bash
# Redis (for distributed caching - add Redis service first)
REDIS_URL=redis://redis.railway.internal:6379

# Rate Limiting (for production)
ENABLE_RATE_LIMITING=true
DEFAULT_RATE_LIMIT_TIER=standard

# Monitoring
ENABLE_PROMETHEUS_METRICS=true
```

### 2.3 Add Redis Service (Optional but Recommended)

For distributed caching across multiple instances:

1. In Railway project, click **"+ New"**
2. Select **"Database" → "Add Redis"**
3. Railway will automatically set `REDIS_URL` variable
4. The app will auto-detect and use Redis for caching

**Note:** App works without Redis using in-memory cache fallback.

### 2.4 Configure Deployment Settings

Railway automatically uses `railway.json` config:
- ✅ Health check at `/health`
- ✅ Auto-restart on failure
- ✅ 4 Gunicorn workers with 2 threads each
- ✅ 120s timeout for long RAG queries

**Port:** Railway automatically sets `PORT` env var (handled in code).

---

## Step 3: Deploy and Test

### 3.1 Initial Deployment

1. Push your code to GitHub (if not already)
2. Railway auto-deploys on push to `main` or your branch
3. Wait for build to complete (~3-5 minutes first time)

### 3.2 View Deployment

1. Check **"Deployments"** tab for build logs
2. Once deployed, Railway provides a URL:
   ```
   https://mandate-wizard-backend-production.up.railway.app
   ```

### 3.3 Test Health Endpoint

```bash
curl https://your-railway-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "service": "mandate-wizard-backend",
  "version": "1.0.0",
  "neo4j": "connected"
}
```

### 3.4 Test Query Endpoint

```bash
curl -X POST https://your-railway-url.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who should I pitch rom-coms to in the UK?",
    "session_id": "test-session-123",
    "history": []
  }'
```

---

## Step 4: Production Configuration

### 4.1 Custom Domain (Optional)

1. In Railway project settings → **"Domains"**
2. Click **"Add Domain"**
3. Enter your domain: `api.mandatewizard.com`
4. Add CNAME record to your DNS:
   ```
   api.mandatewizard.com → CNAME → your-app.up.railway.app
   ```

### 4.2 Enable Metrics (Recommended)

Add Prometheus metrics endpoint for monitoring:

```bash
# In Railway variables:
ENABLE_PROMETHEUS_METRICS=true
```

Access metrics at:
```
https://your-railway-url.railway.app/metrics
```

Integrate with Grafana Cloud or other monitoring tools.

### 4.3 Scale Workers

For high traffic, increase Gunicorn workers:

1. Edit `Dockerfile` or `railway.json`
2. Change `--workers 4` to `--workers 8` (or more)
3. Redeploy

**Formula:** workers = (2 × CPU cores) + 1

### 4.4 Enable Auto-Scaling (Railway Pro)

1. Upgrade to Railway Pro plan
2. Go to **"Settings" → "Deployments"**
3. Enable horizontal auto-scaling
4. Set min/max replicas (e.g., 2-10)

---

## Step 5: Monitoring and Logs

### 5.1 View Application Logs

```bash
# In Railway dashboard:
1. Go to your service
2. Click "Logs" tab
3. Real-time logs streaming
```

Or use Railway CLI:
```bash
railway logs
```

### 5.2 Monitor Performance

**Built-in Railway Metrics:**
- CPU usage
- Memory usage
- Network traffic
- Response times

**Custom Prometheus Metrics:**
```bash
# Add to Grafana or other tools
curl https://your-railway-url.railway.app/metrics
```

Tracks:
- Query counts by intent
- LLM token usage and costs
- Cache hit rates
- Response time histograms
- Neo4j/Pinecone operation metrics

### 5.3 Set Up Alerts

1. Railway Pro: Built-in alerting for CPU/memory
2. External: Use UptimeRobot or Pingdom for `/health` endpoint

---

## Step 6: CI/CD Setup

Railway automatically deploys on git push. Configure branch deployments:

### 6.1 Production Environment

```yaml
# In Railway:
Branch: main
Environment: production
Auto-deploy: ON
```

### 6.2 Staging Environment (Recommended)

1. Create new Railway service
2. Point to `staging` branch
3. Use separate environment variables
4. Test before merging to `main`

---

## Troubleshooting

### Issue: Build Fails

**Check:**
1. `requirements.txt` has all dependencies
2. Python version matches (3.11)
3. View build logs in Railway dashboard

### Issue: App Crashes on Start

**Check:**
1. Environment variables are set correctly
2. Neo4j connection is valid
3. Pinecone API key is valid
4. View logs: `railway logs`

### Issue: Health Check Fails

**Check:**
1. `/health` endpoint returns 200
2. Neo4j connection (optional check)
3. PORT is set correctly (Railway auto-sets this)

### Issue: Slow Queries

**Solutions:**
1. Add Redis service for distributed caching
2. Increase Gunicorn workers
3. Enable query result caching
4. Check Neo4j indexes are created (`setup_neo4j_indexes.py`)

### Issue: Out of Memory

**Solutions:**
1. Reduce `--workers` count in Gunicorn
2. Upgrade Railway plan (more RAM)
3. Optimize embedding batch size in `request_batcher.py`

---

## Cost Optimization

### Reduce Costs

1. **LLM Costs:** Use tiered system (already implemented)
   - Fast queries → gpt-4o-mini ($0.15/1M tokens)
   - Complex queries → gpt-4o ($2.50/1M tokens)

2. **Vector DB:** Use Pinecone free tier for testing
   - Free: 1 index, 100K vectors
   - Paid: $70+/month for production

3. **Graph DB:** Use Neo4j Aura free tier
   - Free: 200K nodes, 400K relationships
   - Paid: $65+/month for production

4. **Railway:** Start small, scale as needed
   - Starter: $5/month (500 hours)
   - Pro: $20+/month (unlimited hours)

5. **Enable Caching:** Add Redis for 40-50% cache hit rate
   - Saves LLM API calls
   - Faster response times

---

## Security Checklist

- ✅ All credentials in environment variables (not in code)
- ✅ CORS configured for specific origins only
- ✅ Rate limiting enabled (4-tier system)
- ✅ HTTPS enforced (Railway default)
- ✅ Health check doesn't expose sensitive data
- ✅ Ghost CMS authentication integrated
- ✅ Input validation on all endpoints
- ✅ No debug mode in production

---

## Performance Benchmarks

Expected performance with Railway deployment:

| Metric | Without Cache | With Redis Cache |
|--------|--------------|------------------|
| Cold query | 2-3 seconds | 2-3 seconds |
| Cached query | 1.5 seconds | 50-100ms |
| Cache hit rate | 10% (exact) | 40-50% (semantic) |
| LLM cost/query | $0.015 | $0.0075 (50% cached) |
| Concurrent users | 10-20 | 50-100 |

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Test health endpoint
3. ✅ Run test queries
4. ⏭️ Add Redis service
5. ⏭️ Set up monitoring/alerts
6. ⏭️ Configure custom domain
7. ⏭️ Load production data
8. ⏭️ Performance testing
9. ⏭️ Set up staging environment

---

## Support

**Railway Documentation:**
- https://docs.railway.app/

**This Project:**
- See `COMPLETE_OPTIMIZATION_SUMMARY.md` for feature details
- See `.env.example` for all environment variables
- Check `/health` endpoint for system status

**Need Help?**
1. Check Railway logs: `railway logs`
2. Test Neo4j connection: `setup_neo4j_indexes.py`
3. Verify Pinecone: Check index name and API key
4. Review CORS settings in `app.py:30-36`

---

## Quick Reference

```bash
# Railway CLI commands
railway login
railway link
railway logs
railway up  # Deploy
railway open  # Open in browser
railway variables  # View env vars

# Local testing (mimics Railway)
export PORT=5000
export FLASK_ENV=production
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app

# Health check
curl http://localhost:5000/health

# Test query
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Test query", "session_id": "test", "history": []}'
```

---

**Ready to deploy!** 🚀

All configuration files are in place:
- ✅ `Dockerfile` - Container build
- ✅ `railway.json` - Railway config
- ✅ `Procfile` - Process definition
- ✅ `.env.example` - Environment template
- ✅ `requirements.txt` - Python dependencies

Just push to GitHub and Railway will auto-deploy!
