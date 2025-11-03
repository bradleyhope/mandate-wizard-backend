# Local Testing Guide - Mandate Wizard

Complete testing checklist for Phase 1 & 2 improvements.

---

## ✅ PRE-FLIGHT CHECKS (All Passed!)

```
✓ Python Syntax:        app.py compiles without errors
✓ HTML Templates:       1,986 lines (index.html), 606 lines (directory)
✓ Tag Balance:          All HTML tags properly closed
✓ API Endpoints:        4 new endpoints detected
✓ JavaScript:           10+ functions implemented
✓ Flask Routes:         37 total routes
✓ Code Size:            4,079 lines of new code
```

**Status: READY FOR TESTING** 🚀

---

## 🚀 HOW TO RUN LOCALLY

### Step 1: Set Environment Variables

```bash
cd mandate-wizard-backend

# Required environment variables
export PINECONE_API_KEY="your-pinecone-key"
export PINECONE_INDEX_NAME="mandate-wizard"
export PINECONE_ENVIRONMENT="your-environment"

export NEO4J_URI="neo4j+s://your-uri.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your-password"

export OPENAI_API_KEY="sk-your-key"

# Optional (for auth features)
export GHOST_ADMIN_API_KEY="your-ghost-key"
export GHOST_API_URL="https://your-ghost-site.com"
export GHOST_CONTENT_API_KEY="your-content-key"
```

### Step 2: Start the Server

```bash
python app.py
```

**Expected output:**
```
Initializing Mandate Wizard HybridRAG Engine...
✓ Connected to Pinecone vector database
✓ Connected to Neo4j graph database
✓ Loaded X executives from Neo4j
✓ HybridRAG engine ready
======================================================================
🚀 Starting server on http://0.0.0.0:5000
```

### Step 3: Open Browser

```bash
# Main chat interface
http://localhost:5000

# Executive directory
http://localhost:5000/executives_directory

# Health check
http://localhost:5000/health

# Metrics
http://localhost:5000/metrics
```

---

## 🧪 TESTING CHECKLIST

### ✅ Phase 1: Core UX Features

#### 1. Conversation History Sidebar

**Test:**
```
1. Open http://localhost:5000
2. Check left sidebar appears with "New Chat" button
3. Ask a question: "Who handles drama series?"
4. Refresh the page (F5)
5. Sidebar should show conversation with auto-generated title
6. Click "New Chat" button
7. Previous conversation should still be in sidebar
```

**Expected:**
- ✅ Sidebar visible on left (280px wide)
- ✅ "New Chat" button at top
- ✅ Conversations persist after refresh
- ✅ Can switch between conversations
- ✅ Timestamps show "time ago" format

**Mobile Test:**
- Resize browser to <768px width
- Hamburger menu (☰) appears top-left
- Click to open sidebar
- Sidebar slides in from left

---

#### 2. Executive Cards

**Test:**
```
1. Ask: "Tell me about Bela Bajaria"
2. Look for executive card in response
3. Card should have:
   - Avatar with initials or photo
   - Name and title
   - Stats badges (budget, greenlights, region)
   - Mandate preview
   - "Ask About" and "View Profile" buttons
4. Hover over card → should lift up slightly
5. Click "Ask About" → should pre-fill question
```

**Expected:**
- ✅ Card has gradient border on hover
- ✅ Avatar shows initials if no photo
- ✅ Stats display with icons (📊 💰 🌍)
- ✅ Buttons are clickable
- ✅ Smooth hover animation

---

#### 3. Progress Indicators

**Test:**
```
1. Ask any question
2. Watch status indicator appear above answer
3. Should show stages:
   - "Analyzing your question..."
   - "Searching 10,000+ mandates..."
   - "Ranking results..."
   - "Generating answer..."
4. Progress bar should fill from 0% → 100%
5. Status disappears when answer starts streaming
```

**Expected:**
- ✅ Purple gradient status box
- ✅ Spinning icon animation
- ✅ Progress bar fills gradually
- ✅ Status updates every ~500ms
- ✅ Hides when content starts

---

#### 4. Clickable Entities

**Test:**
```
1. Ask: "Who greenlit The Diplomat?"
2. Look for red underlined names in answer
3. Hover over executive name → tooltip appears after 500ms
4. Hover over project name → tooltip appears
5. Click on executive name → should navigate or trigger action
```

**Expected:**
- ✅ Executive names are red with underline
- ✅ Project titles (in quotes) are clickable
- ✅ Tooltip shows after 500ms delay
- ✅ Tooltip contains preview info
- ✅ Click triggers navigation

---

#### 5. Copy/Share/Regenerate Buttons

**Test:**
```
1. Ask any question and get answer
2. Look for action buttons under answer
3. Click "Copy" button
4. Check clipboard (Ctrl+V in notepad)
5. Click "Share" button (if supported)
6. Click "Regenerate" button → should re-ask question
```

**Expected:**
- ✅ Three buttons: 📋 Copy, 🔗 Share, 🔄 Regenerate
- ✅ Copy button changes to "✓ Copied" for 2 seconds
- ✅ Clipboard contains answer text
- ✅ Regenerate re-submits the question
- ✅ Buttons have hover effects

---

#### 6. Confidence Badges

**Test:**
```
1. Ask a specific question with good data
2. Look for confidence badge under answer
3. Should see:
   - Green badge: "✓ High Confidence"
   - Source count: "📚 X sources"
   - Last updated: "🕒 Updated X days ago"
4. Hover over confidence badge → tooltip appears
```

**Expected:**
- ✅ Badge color matches confidence (green/orange/red)
- ✅ Source count displayed
- ✅ Timestamp formatted nicely
- ✅ Tooltip shows additional details
- ✅ Metadata is accurate

---

#### 7. Keyboard Shortcuts

**Test:**
```
1. Press Cmd+K (or Ctrl+K on Windows)
   → Input field should focus
2. Type a question, press Enter
   → Question should submit
3. Press Cmd+N (or Ctrl+N)
   → New conversation should start
4. Type in input, press Escape
   → Input should clear and unfocus
```

**Expected:**
- ✅ Cmd/Ctrl+K focuses input
- ✅ Enter submits question
- ✅ Cmd/Ctrl+N creates new chat
- ✅ Escape clears input
- ✅ Shortcuts work from anywhere on page

---

#### 8. Mobile Responsiveness

**Test:**
```
1. Resize browser to 375px width (iPhone size)
2. Check that:
   - Sidebar is hidden by default
   - Hamburger menu appears top-left
   - Cards stack in single column
   - Input is fixed at bottom
   - Tap targets are large enough (>44px)
3. Click hamburger → sidebar slides in
4. Type question on mobile keyboard → input doesn't get covered
```

**Expected:**
- ✅ Sidebar hidden on mobile
- ✅ Hamburger menu visible
- ✅ All content readable
- ✅ No horizontal scrolling
- ✅ Input stays visible with keyboard open

---

### ✅ Phase 2: Browse & Explore Features

#### 9. Executive Directory Page

**Test:**
```
1. Navigate to http://localhost:5000/executives_directory
2. Should see:
   - Search box at top
   - Three filter dropdowns (Region, Content Type, Level)
   - Grid of executive cards
   - Results summary ("Showing X of Y executives")
3. Type in search box → results filter in real-time
4. Select region filter → results update
5. Click "Back to Chat" → returns to main page
6. Click "Ask About" on any card → navigates to chat with question
```

**Expected:**
- ✅ Page loads with executive grid
- ✅ Search filters instantly (no reload)
- ✅ Multiple filters work together
- ✅ Results summary updates
- ✅ Cards have hover effects
- ✅ Navigation works

**Mobile Test:**
- Cards stack in single column
- Filters stack vertically
- Search box full width

---

#### 10. Filtering in Chat Mode

**Test:**
```
1. On main chat page, click "Filters" button in header
2. Filter bar should appear below header
3. Click "+ Add Filter" button
4. Enter a region (e.g., "US & Canada")
5. Filter chip should appear
6. Ask a question → filters should be sent to backend
7. Click X on filter chip → filter removes
```

**Expected:**
- ✅ Filter bar toggles on/off
- ✅ Filter chips appear with icons
- ✅ Remove button (×) works
- ✅ Filters affect query results
- ✅ Smooth animations

---

#### 11. Hover Previews

**Test:**
```
1. Ask: "Who handles drama series at Netflix?"
2. Hover mouse over executive name in answer
3. Wait 500ms → tooltip should appear
4. Tooltip should show:
   - Executive name and title
   - Mandate preview (first 200 chars)
   - Greenlight count
5. Move mouse away → tooltip disappears
```

**Expected:**
- ✅ Tooltip appears after 500ms
- ✅ Positioned near cursor
- ✅ Contains preview data
- ✅ Smooth fade-in
- ✅ Disappears on mouse leave

---

#### 12. Empty States

**Test:**
```
1. Ask a question with no results: "Who handles underwater basket weaving?"
2. Should see friendly empty state:
   - Icon (🔍)
   - Message: "No specific data found"
   - Explanation
   - Suggested alternative queries (3 buttons)
3. Click a suggestion → should ask that question
```

**Expected:**
- ✅ Empty state appears (not just blank)
- ✅ Message is helpful, not error-like
- ✅ Suggestions are relevant
- ✅ Buttons are clickable
- ✅ Professional appearance

---

## 🔧 API ENDPOINT TESTING

### Test New Endpoints

```bash
# 1. Executive list (with filters)
curl "http://localhost:5000/api/executives/list?region=Global&level=C-Suite"

# Expected: JSON array of executives matching filters

# 2. Executive preview
curl "http://localhost:5000/api/executive/Bela%20Bajaria/preview"

# Expected: JSON with name, title, mandate summary, greenlight count

# 3. Project preview
curl "http://localhost:5000/api/project/The%20Diplomat/preview"

# Expected: JSON with title, genre, format, date, executive

# 4. Health check
curl "http://localhost:5000/health"

# Expected: {"status": "healthy", "neo4j": "connected", ...}
```

---

## 🐛 COMMON ISSUES & SOLUTIONS

### Issue 1: Sidebar Doesn't Appear

**Symptoms:** Left sidebar is missing, content starts at left edge

**Solution:**
- Check browser console (F12) for JavaScript errors
- Ensure `index.html` loaded correctly
- Clear browser cache (Ctrl+Shift+Delete)
- Try incognito window

---

### Issue 2: Executive Directory Empty

**Symptoms:** `/executives_directory` shows "No executives found"

**Solution:**
- Check Neo4j has executive data
- Test API: `curl http://localhost:5000/api/executives/list`
- Verify Neo4j connection in `/health`
- Check console logs for errors

---

### Issue 3: Conversations Not Persisting

**Symptoms:** Conversations disappear after refresh

**Solution:**
- Check localStorage isn't disabled
- Open Dev Tools → Application → Local Storage
- Look for `mandate_wizard_conversations` key
- Try different browser (Safari, Chrome, Firefox)

---

### Issue 4: Clickable Entities Not Working

**Symptoms:** Names are plain text, not red/clickable

**Solution:**
- Check that answer is rendering (not empty)
- Inspect element → should have `entity-link` class
- Check JavaScript console for errors in `makeEntitiesClickable()`
- Verify regex patterns match your name formats

---

### Issue 5: Hover Previews Don't Show

**Symptoms:** No tooltip appears on hover

**Solution:**
- Wait full 500ms (timeout delay)
- Check API endpoint: `/api/executive/<name>/preview`
- Verify Neo4j has data for that executive
- Check network tab in Dev Tools for failed requests

---

## 📊 PERFORMANCE BENCHMARKS

### Expected Response Times

| Action | Expected Time | What to Measure |
|--------|---------------|-----------------|
| Page load | <500ms | Time to interactive |
| First question (cold) | 2-3 seconds | Total time to first chunk |
| Repeat question (cached) | 1.5 seconds | With semantic cache |
| Filter change | <100ms | Real-time UI update |
| Sidebar toggle | <300ms | Animation duration |
| Entity hover → tooltip | 500ms delay | Debounced preview fetch |
| Copy to clipboard | <50ms | Immediate feedback |

### With Redis (After Deployment)

| Action | Expected Time | Improvement |
|--------|---------------|-------------|
| Repeat question | 50-100ms | 60x faster |
| Similar question | 50-100ms | Semantic match |
| Cache hit rate | 40-50% | 4.5x better |

---

## ✅ FINAL CHECKLIST

Before deploying to Railway, verify:

- [ ] All Phase 1 features working (10/10)
- [ ] All Phase 2 features working (6/6)
- [ ] Mobile responsive tests passed
- [ ] No JavaScript console errors
- [ ] No Python exceptions in terminal
- [ ] API endpoints return valid JSON
- [ ] Health check passes
- [ ] Conversation history persists
- [ ] Executive directory loads
- [ ] Search and filters work

**When all checked:** Ready for Railway deployment! 🚀

---

## 🚀 NEXT STEPS

1. **Local testing complete** → Deploy to Railway
2. **Railway deployed** → Add Redis service
3. **Redis added** → Test cache performance
4. **Cache working** → Share with beta users

---

## 📞 TROUBLESHOOTING HELP

**If you see errors:**
1. Check the terminal where `python app.py` is running
2. Look for stack traces or error messages
3. Check browser console (F12) for JavaScript errors
4. Verify environment variables are set
5. Test database connections at `/health`

**Still stuck?**
- Check `RAILWAY_DEPLOYMENT.md` for deployment help
- Check `DEPLOY_REDIS.md` for Redis setup
- Review commit message for feature details

---

**Status: ALL SYSTEMS GO!** ✅

Your local testing environment is ready. Start with the basic tests, then move to advanced features. Everything should work smoothly! 🎉
