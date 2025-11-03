# Railway Deployment Walkthrough - Step by Step

**Status:** Ready to deploy! All code is committed and pushed.

---

## 🎯 WHAT WE'RE DOING

1. ✅ Verify Railway is deploying your latest code
2. ✅ Set up environment variables
3. ✅ Add Redis service (2 minutes)
4. ✅ Test the live site
5. ✅ Verify all new features work

**Time Required:** 10-15 minutes

---

## 📋 PRE-DEPLOYMENT CHECKLIST

Before we start, verify you have:

- [ ] Railway account (railway.app)
- [ ] Railway project connected to your GitHub repo
- [ ] Pinecone account and API key
- [ ] Neo4j Aura instance and credentials
- [ ] OpenAI API key
- [ ] (Optional) Ghost CMS credentials

**If you don't have Railway set up yet, see the "First Time Setup" section below.**

---

## 🚀 STEP 1: VERIFY RAILWAY CONNECTION

### Check if Railway is Already Connected

1. Go to https://railway.app/dashboard
2. Look for your project: `mandate-wizard-backend`
3. Check if it's connected to GitHub

**If connected:**
- ✅ You'll see "Connected to GitHub" badge
- ✅ Shows your repo: `bradleyhope/mandate-wizard-backend`
- ✅ Branch: `claude/film-industry-rag-011CUm4RiSWYksshL2kNa7DB`

**If NOT connected, do First Time Setup below.**

---

## 🆕 FIRST TIME SETUP (Skip if already connected)

### Option A: Connect Existing Project

```bash
# Install Railway CLI
npm i -g @railway/cli
# or
brew install railway

# Login
railway login

# Link to your project
cd mandate-wizard-backend
railway link

# Select your project from the list
```

### Option B: Create New Project

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select: `bradleyhope/mandate-wizard-backend`
4. Choose branch: `claude/film-industry-rag-011CUm4RiSWYksshL2kNa7DB`
5. Click "Deploy"

Railway will:
- ✅ Detect Dockerfile
- ✅ Build your container
- ✅ Expose on public URL
- ✅ Auto-deploy on git push

---

## 🚀 STEP 2: CHECK DEPLOYMENT STATUS

### In Railway Dashboard

1. Click on your `mandate-wizard-backend` service
2. Go to **"Deployments"** tab
3. Look for latest deployment

**What to look for:**
- Status: "Building" or "Deploying" or "Success"
- Commit: Should show `ee9f230` or `d75821e` (your latest)
- Time: Should be recent (within last few minutes)

### If Deployment is Running:

✅ **Great!** Skip to Step 3 while it deploys.

### If No Recent Deployment:

**Trigger Manual Deployment:**

```bash
# In your terminal
cd mandate-wizard-backend

# Push again to trigger deployment
git commit --allow-empty -m "Trigger Railway deployment"
git push

# Or use Railway CLI
railway up
```

Railway should start deploying within 30 seconds.

---

## 🚀 STEP 3: SET ENVIRONMENT VARIABLES

**CRITICAL:** Your app won't work without these!

### In Railway Dashboard:

1. Click your service
2. Go to **"Variables"** tab
3. Click **"+ New Variable"**
4. Add each variable below:

### Required Variables:

```bash
# Neo4j (Graph Database)
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Pinecone (Vector Database)
PINECONE_API_KEY=pcsk_xxxxx
PINECONE_INDEX_NAME=mandate-wizard
PINECONE_ENVIRONMENT=gcp-starter

# OpenAI (LLM)
OPENAI_API_KEY=sk-xxxxx

# Flask
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### Optional Variables (for auth features):

```bash
# Ghost CMS (if using authentication)
GHOST_ADMIN_API_KEY=your-ghost-admin-key
GHOST_API_URL=https://your-ghost-site.com
GHOST_CONTENT_API_KEY=your-ghost-content-key

# Rate Limiting
ENABLE_RATE_LIMITING=true
DEFAULT_RATE_LIMIT_TIER=standard

# Monitoring
ENABLE_PROMETHEUS_METRICS=true
```

### After Adding Variables:

Railway will **automatically redeploy** your app with the new variables.

**Wait for deployment to complete** (~2-3 minutes for first deploy).

---

## 🚀 STEP 4: GET YOUR APP URL

### Find Your Public URL:

1. In Railway dashboard, click your service
2. Go to **"Settings"** tab
3. Scroll to **"Networking"** section
4. You'll see a URL like:
   ```
   https://mandate-wizard-backend-production.up.railway.app
   ```
5. **Copy this URL** - you'll need it!

### Test Basic Connectivity:

```bash
# Replace with your actual URL
curl https://your-app.railway.app/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "service": "mandate-wizard-backend",
  "version": "1.0.0",
  "neo4j": "connected",
  "redis": "disconnected"  ← This is expected (we'll fix next)
}
```

**If you see errors:**
- Check deployment logs: Railway dashboard → "Deployments" → Click latest → "View Logs"
- Verify environment variables are set
- Check Neo4j/Pinecone credentials are correct

---

## 🚀 STEP 5: ADD REDIS SERVICE (60x FASTER CACHE!)

**This is the magic step for performance.**

### In Railway Dashboard:

1. Click **"+ New"** button (top right)
2. Select **"Database"**
3. Choose **"Add Redis"**
4. Railway creates Redis instance automatically

**What happens:**
- ✅ Redis instance provisioned (~30 seconds)
- ✅ `REDIS_URL` variable automatically added to your service
- ✅ Your app auto-redeploys with Redis

### Verify Redis is Working:

Wait 1-2 minutes for redeployment, then:

```bash
curl https://your-app.railway.app/health
```

**Now you should see:**
```json
{
  "status": "healthy",
  "neo4j": "connected",
  "redis": "connected"  ← Changed from "disconnected"!
}
```

**If Redis still shows "disconnected":**
1. Check Railway logs for errors
2. Verify `REDIS_URL` variable exists (should be automatic)
3. Try manual redeploy: Railway dashboard → "..." menu → "Redeploy"

---

## 🚀 STEP 6: TEST YOUR LIVE SITE

### Open Your App:

```
https://your-app.railway.app
```

### ✅ FEATURE TESTING CHECKLIST:

#### 1. Homepage (Main Chat Interface)

**Visual Check:**
- [ ] Sidebar appears on left with "New Chat" button
- [ ] Header shows "Mandate Wizard" with "Executives" and "Filters" buttons
- [ ] Example questions at bottom
- [ ] Input box at bottom with "Ask" button

**Try it:**
- [ ] Click example question → should submit
- [ ] Type "Who handles drama?" and press Enter → should work
- [ ] See progress indicator with stages
- [ ] Answer appears with formatting

---

#### 2. Conversation History

**Test:**
- [ ] Ask a question and get answer
- [ ] Refresh page (F5)
- [ ] Sidebar shows conversation with auto-title
- [ ] Click "New Chat" button
- [ ] Previous conversation still in sidebar
- [ ] Click old conversation → switches back

**Expected:**
✅ Conversations persist across refreshes
✅ Can switch between conversations
✅ Timestamps show relative time ("5m ago")

---

#### 3. Executive Cards

**Test:**
- [ ] Ask: "Tell me about Bela Bajaria"
- [ ] Look for executive card in response
- [ ] Card has avatar, name, title, stats
- [ ] Hover over card → lifts up
- [ ] Click "Ask About" button → pre-fills question
- [ ] Click "View Profile" → navigates (or shows coming soon)

**Expected:**
✅ Beautiful gradient-bordered card
✅ Stats badges with icons (📊 🌍 🎬)
✅ Smooth hover animation
✅ Buttons are clickable

---

#### 4. Progress Indicators

**Test:**
- [ ] Ask any question
- [ ] Watch status box appear (purple gradient)
- [ ] See stages: "Analyzing" → "Searching" → "Ranking" → "Generating"
- [ ] Progress bar fills from 0% → 100%
- [ ] Status disappears when answer starts

**Expected:**
✅ Smooth animations
✅ Clear status messages
✅ Progress bar updates

---

#### 5. Clickable Entities

**Test:**
- [ ] Ask: "Who greenlit The Diplomat?"
- [ ] Executive names should be red with underline
- [ ] Hover over name → tooltip appears after 500ms
- [ ] Tooltip shows preview info
- [ ] Click name → navigates or triggers action

**Expected:**
✅ Names are red/clickable
✅ Hover previews work
✅ Smooth tooltip animations

---

#### 6. Copy/Share/Regenerate

**Test:**
- [ ] After getting answer, look for action buttons
- [ ] Click "📋 Copy" → button changes to "✓ Copied"
- [ ] Paste somewhere → answer text appears
- [ ] Click "🔗 Share" → share dialog or link copied
- [ ] Click "🔄 Regenerate" → re-asks same question

**Expected:**
✅ All buttons work
✅ Visual feedback on actions
✅ Copy actually copies text

---

#### 7. Keyboard Shortcuts

**Test:**
- [ ] Press Cmd+K (Mac) or Ctrl+K (Windows) → input focuses
- [ ] Type question and press Enter → submits
- [ ] Press Cmd+N → new conversation starts
- [ ] Type in input and press Escape → input clears

**Expected:**
✅ All shortcuts work from anywhere
✅ Input focuses properly
✅ New conversation clears screen

---

#### 8. Executive Directory

**Test:**
- [ ] Navigate to: `https://your-app.railway.app/executives_directory`
- [ ] Should see grid of executive cards
- [ ] Search box at top
- [ ] Three filter dropdowns
- [ ] Type in search → results filter instantly
- [ ] Select region filter → results update
- [ ] Click "Ask About" on any card → goes to chat with question

**Expected:**
✅ Grid loads with executives
✅ Search filters real-time (no reload)
✅ Filters work together
✅ Clean, professional design

---

#### 9. Mobile Responsive

**Test:**
- [ ] Resize browser to <768px (or use phone)
- [ ] Sidebar should hide
- [ ] Hamburger menu (☰) appears top-left
- [ ] Click hamburger → sidebar slides in
- [ ] Cards stack in single column
- [ ] Input stays fixed at bottom
- [ ] Everything is readable and tappable

**Expected:**
✅ Mobile-friendly layout
✅ No horizontal scrolling
✅ Large tap targets
✅ Sidebar slides smoothly

---

#### 10. Redis Cache Performance

**Test:**
```bash
# First query (cold)
time curl -X POST https://your-app.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who handles drama?", "session_id": "test"}'
# Note the time (should be ~2-3 seconds)

# Second query (should hit cache)
time curl -X POST https://your-app.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who handles drama?", "session_id": "test"}'
# Note the time (should be ~50-100ms - much faster!)

# Similar query (semantic cache)
time curl -X POST https://your-app.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Who do I pitch drama shows to?", "session_id": "test"}'
# Should also be fast (~50-100ms) despite different wording!
```

**Expected:**
✅ First query: ~2-3 seconds
✅ Repeat query: ~50-100ms (60x faster!)
✅ Similar query: ~50-100ms (semantic match!)

---

## 🚀 STEP 7: MONITOR PERFORMANCE

### Check Metrics Endpoint:

```bash
curl https://your-app.railway.app/metrics | grep cache
```

**Look for:**
- `cache_hits_total` - Should increase with repeat queries
- `cache_misses_total` - First-time queries
- `cache_hit_rate` - Aim for 40-50% over time

### Check Railway Dashboard:

1. Go to "Metrics" tab in Railway
2. Monitor:
   - CPU usage
   - Memory usage
   - Network traffic
   - Response times

**Expected Performance:**
- CPU: <30% under normal load
- Memory: ~500MB-1GB
- Response time: <3 seconds (cold), <100ms (cached)

---

## 🎉 SUCCESS CRITERIA

Your deployment is successful if:

- [x] `/health` returns `{"status": "healthy", "redis": "connected"}`
- [x] Main page loads with sidebar and examples
- [x] Can ask questions and get answers
- [x] Conversation history persists after refresh
- [x] Executive directory page loads
- [x] Search and filters work
- [x] Mobile responsive design works
- [x] Redis cache shows performance improvement
- [x] No errors in Railway logs

**If all checked:** 🎉 **CONGRATULATIONS! You're live!**

---

## 🐛 TROUBLESHOOTING

### Issue 1: App Won't Deploy

**Check:**
- Railway logs: Dashboard → Deployments → View Logs
- Look for build errors or missing dependencies
- Verify Dockerfile is present

**Solution:**
```bash
# Trigger rebuild
railway redeploy
```

---

### Issue 2: Health Check Fails

**Symptoms:** `/health` returns 503 or error

**Check:**
- Environment variables are set
- Neo4j credentials are correct
- Pinecone API key is valid
- Railway logs for connection errors

**Solution:**
- Re-enter environment variables
- Test Neo4j connection separately
- Check Pinecone index name matches

---

### Issue 3: Redis Not Connecting

**Symptoms:** `/health` shows `redis: "disconnected"`

**Check:**
- Redis service exists in Railway project
- `REDIS_URL` variable is set (should be automatic)
- App has redeployed after adding Redis

**Solution:**
```bash
# Verify Redis variable exists
railway variables

# If missing, add Redis service again
# Railway dashboard → + New → Database → Redis

# Force redeploy
railway redeploy
```

---

### Issue 4: Frontend Looks Broken

**Symptoms:** No sidebar, plain styling, buttons don't work

**Check:**
- Browser console (F12) for JavaScript errors
- Network tab for failed requests
- Check if templates are loading

**Solution:**
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito window
- Check Railway logs for template errors
- Verify `templates/index.html` was deployed

---

### Issue 5: Executive Directory Empty

**Symptoms:** `/executives_directory` shows no results

**Check:**
- Neo4j has executive data
- API endpoint: `/api/executives/list`
- Check Railway logs for Neo4j query errors

**Solution:**
```bash
# Test API directly
curl https://your-app.railway.app/api/executives/list

# Check Neo4j has Person nodes
# Should return JSON array of executives
```

---

## 📊 EXPECTED COSTS

### Railway:
- Hobby Plan: $5/month (500 hours)
- Pro Plan: $20/month (unlimited hours)
- Redis: Included in plan

### External Services:
- Neo4j Aura: Free tier or $65+/month
- Pinecone: Free tier or $70+/month
- OpenAI: $50-200/month (usage-based)

**Total: $55-355/month** depending on tier and usage

---

## 🎯 NEXT STEPS AFTER DEPLOYMENT

1. **Share with Beta Users**
   - Send them your Railway URL
   - Collect feedback on new UX

2. **Monitor Usage**
   - Check Railway metrics daily
   - Watch cache hit rates improve
   - Monitor API costs

3. **Custom Domain (Optional)**
   - Railway Settings → Domains
   - Add CNAME: `api.yourdomain.com`

4. **Set Up Monitoring**
   - Grafana Cloud (free tier)
   - Point to `/metrics` endpoint
   - Set up alerts

5. **Optimize Based on Data**
   - Review which features users love
   - Check which queries are most common
   - Adjust cache TTL if needed

---

## ✅ DEPLOYMENT COMPLETE!

**What You've Achieved:**

🎨 **Professional UI** - Netflix-inspired design live
📱 **Mobile-First** - Responsive across all devices
🔍 **Browse Mode** - Executive directory accessible
💾 **Conversation History** - Persistent storage working
⚡ **Performance** - Redis caching 60x faster
🎯 **User-Friendly** - All 16 UX improvements live
📊 **Production-Ready** - Monitoring enabled
🚀 **Live on Railway** - Public URL accessible

**Your Mandate Wizard is now live and ready for users!** 🎉

---

## 📞 SUPPORT

**Need Help?**
- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Check `LOCAL_TESTING_GUIDE.md` for feature testing
- Check `DEPLOY_REDIS.md` for Redis details

**Railway CLI Commands:**
```bash
railway login        # Login to Railway
railway link         # Link to project
railway logs         # View logs
railway open         # Open in browser
railway redeploy     # Force redeploy
railway variables    # View env vars
```

---

**Status: READY TO DEPLOY** 🚀

Follow the steps above, and you'll be live in 15 minutes!
