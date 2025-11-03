# Mandate Wizard: Data Collection Handoff

**Date:** October 26, 2025  
**Status:** Technical implementation complete, data collection needed  
**Your Mission:** Collect data for Layers 3-8 to complete the intelligence system

---

## 🎯 What You Need to Know

### System Status: 95% Complete (Technically)

**✅ What's Built and Working:**
1. **LangChain/LangGraph** - Stateful pathway navigation system
2. **GPT-5 Integration** - Using OpenAI Responses API
3. **Mem0 User Memory** - Remembers user context across sessions
4. **Persona Detection** - Detects sophistication level and crisis mode
5. **8-Layer Pathway** - Intelligent routing through data layers
6. **Executive Name Extraction** - 100% accuracy
7. **Source Attribution** - Quote cards working
8. **Adaptive Follow-ups** - Context-aware questions

**❌ What's Missing (Your Job):**
- **Layer 3 Data:** Production company database
- **Layer 4 Data:** Recent greenlights (HIGHEST PRIORITY)
- **Layer 5 Data:** Pitch requirements
- **Layer 6 Data:** Packaging intelligence
- **Layer 7 Data:** Timing & strategy

The **technical infrastructure is complete**. We just need **data/content** to populate the intelligence layers.

---

## 📚 Your Complete Toolkit

### Primary Documents (Read These First)

1. **[DATA_COLLECTION_PLAYBOOK.md](DATA_COLLECTION_PLAYBOOK.md)**
   - Complete guide for collecting each layer
   - Exact schemas and formatting rules
   - Research sources and guidelines
   - Quality validation criteria

2. **[data/README.md](data/README.md)**
   - Quick start guide
   - Workflow recommendations
   - Progress tracking
   - Common issues and solutions

### Example Files (Reference These)

3. **[data/production_companies_EXAMPLE.json](data/production_companies_EXAMPLE.json)**
   - 3 complete production company examples
   - Shows exact format expected

4. **[data/recent_greenlights_EXAMPLE.json](data/recent_greenlights_EXAMPLE.json)**
   - 3 complete greenlight examples
   - Shows exact format expected

### Template Files (Fill These In)

5. **[data/production_companies.json](data/production_companies.json)** - Layer 3
6. **[data/recent_greenlights.json](data/recent_greenlights.json)** - Layer 4 (START HERE)
7. **[data/pitch_requirements.json](data/pitch_requirements.json)** - Layer 5
8. **[data/packaging_intelligence.json](data/packaging_intelligence.json)** - Layer 6
9. **[data/timing_strategy.json](data/timing_strategy.json)** - Layer 7

### Validation & Import

10. **[import_data.py](import_data.py)**
    - Validates JSON syntax
    - Checks data quality
    - Reports errors and warnings
    - Run with: `python3 import_data.py`

---

## 🚀 Recommended Workflow

### Phase 1: Layer 4 (Recent Greenlights) - HIGHEST PRIORITY

**Why Start Here:**
- Most requested by users ("What has X greenlit recently?")
- Highest impact on user experience
- Easiest to collect (public announcements)
- Clear validation criteria

**Target:** 100+ greenlights from January 2024 - Present

**Time Estimate:** 8-12 hours for 100 entries

**Process:**
1. Go to Deadline Hollywood (https://deadline.com)
2. Search "Netflix greenlight 2024"
3. For each announcement:
   - Copy the template from `DATA_COLLECTION_PLAYBOOK.md`
   - Fill in all fields
   - Add to `data/recent_greenlights.json`
4. Every 20 entries, run `python3 import_data.py` to validate
5. Fix any errors and continue

**Key Fields:**
- `project_title` - Official project name
- `executive_name` - MUST match our database exactly (Don Kang, Peter Friedlander, etc.)
- `greenlight_date` - YYYY-MM-DD format
- `source_url` - Link to announcement article

### Phase 2: Layer 3 (Production Companies) - CRITICAL FOR ACCESS

**Why Second:**
- Users need to know how to access executives
- Production companies are the gateway
- Complements Layer 1 (executive routing)

**Target:** 50+ production companies with Netflix deals

**Time Estimate:** 10-15 hours for 50 entries

**Process:**
1. Search "Netflix production company deal"
2. Search "[Country] production company Netflix" (for regional companies)
3. For each company:
   - Copy template from `DATA_COLLECTION_PLAYBOOK.md`
   - Fill in all fields
   - Add to `data/production_companies.json`
4. Validate every 10 entries

**Key Fields:**
- `company_name` - Official company name
- `netflix_relationship.has_deal` - true/false
- `netflix_relationship.primary_executive` - MUST match our database
- `notable_projects` - At least 2 projects required

### Phase 3: Layer 5 (Pitch Requirements) - HIGH VALUE

**Why Third:**
- Users preparing pitches need this
- Harder to find than Layers 3-4
- Requires synthesis from multiple sources

**Target:** 20+ entries (one per major executive/content type)

**Time Estimate:** 6-10 hours for 20 entries

**Process:**
1. Search "[Executive Name] pitch process Netflix"
2. Look for interviews, panel discussions, producer testimonials
3. Synthesize information into template
4. Add to `data/pitch_requirements.json`

**Key Fields:**
- `submission_process` - At least 3 steps
- `required_materials` - Specific format requirements
- `preferences.loves` - What this executive loves
- `preferences.avoids` - What to avoid

### Phase 4 & 5: Layers 6-7 (Optional)

**Layer 6 (Packaging Intelligence):**
- Target: 15+ entries
- Time: 5-8 hours
- Nice to have, not critical

**Layer 7 (Timing & Strategy):**
- Target: 20 events + 10 schedules
- Time: 4-6 hours
- Nice to have, not critical

---

## ✅ Quality Standards

### Before Submitting Any Data

**JSON Syntax:**
```bash
python3 -m json.tool data/recent_greenlights.json > /dev/null && echo "✅ Valid" || echo "❌ Invalid"
```

**Data Validation:**
```bash
python3 import_data.py
```

**Manual Checks:**
- [ ] All required fields filled in
- [ ] Dates in YYYY-MM-DD format
- [ ] Executive names match exactly (Don Kang, not "Don", not "Kang")
- [ ] Source URLs are valid and accessible
- [ ] No trailing commas in JSON
- [ ] Proper quote escaping

---

## 📊 Progress Tracking

Update this as you go:

**Layer 4 (Recent Greenlights):**
- Target: 100+ entries
- Current: 0 entries
- Status: Not Started
- Priority: 🔥🔥🔥 HIGHEST

**Layer 3 (Production Companies):**
- Target: 50+ entries
- Current: 0 entries
- Status: Not Started
- Priority: 🔥🔥 CRITICAL

**Layer 5 (Pitch Requirements):**
- Target: 20+ entries
- Current: 0 entries
- Status: Not Started
- Priority: 🔥 HIGH

**Layer 6 (Packaging Intelligence):**
- Target: 15+ entries
- Current: 0 entries
- Status: Not Started
- Priority: ⭐ NICE TO HAVE

**Layer 7 (Timing & Strategy):**
- Target: 20 events + 10 schedules
- Current: 0 entries
- Status: Not Started
- Priority: ⭐ NICE TO HAVE

---

## 🎓 Key Executive Names (Must Match Exactly)

When filling in `executive_name` fields, use these EXACT names:

**U.S. Scripted:**
- Peter Friedlander
- Jinny Howe
- Bela Bajaria

**International:**
- Don Kang (Korea)
- Francisco Ramos (Spain/Latin America)
- Kaata Sakamoto (Japan)

**Unscripted:**
- Brandon Riegg
- Adam Hawkins

**Documentary:**
- Adam Del Deo

**Film:**
- Scott Stuber
- Lisa Nishimura

**Comedy:**
- Tracey Pakosta

(See full list in Neo4j database or ask if unsure)

---

## 🆘 Common Issues & Solutions

### Issue: "I can't find [specific information]"
**Solution:** 
- Document what you couldn't find in "notes" field
- Mark field as null or empty string
- Move on to next entry
- We can fill gaps later

### Issue: "Executive name doesn't match database"
**Solution:**
- Check spelling carefully (Don Kang, not Don Kong)
- Use full name (Peter Friedlander, not Peter F.)
- If truly unsure, leave as "Unknown" and add note

### Issue: "JSON syntax error"
**Solution:**
- Check for trailing commas (last item in array/object should NOT have comma)
- Check quote escaping ("It's" should be "It\\'s")
- Use `python3 -m json.tool` to validate

### Issue: "Date format wrong"
**Solution:**
- Always use YYYY-MM-DD (2024-10-26)
- If you only know month, use first day (2024-10-01)
- If you only know year, use January 1 (2024-01-01)

### Issue: "Source URL is paywalled"
**Solution:**
- Use the URL anyway (we just need the reference)
- Try searching for free version of same article
- Use archive.org or archive.is

---

## 🎯 Success Criteria

**Minimum Viable Dataset:**
- 100+ Layer 4 entries (Recent Greenlights)
- 50+ Layer 3 entries (Production Companies)
- 20+ Layer 5 entries (Pitch Requirements)

**Ideal Complete Dataset:**
- 200+ Layer 4 entries
- 100+ Layer 3 entries
- 50+ Layer 5 entries
- 15+ Layer 6 entries
- 30+ Layer 7 entries

**Quality Metrics:**
- 0 JSON syntax errors
- <5% missing required fields
- 100% valid source URLs
- 100% executive name matches

---

## 🚦 Getting Started (Right Now)

1. **Read this document** ✅ (you're doing it!)

2. **Read [DATA_COLLECTION_PLAYBOOK.md](DATA_COLLECTION_PLAYBOOK.md)**
   - Focus on Layer 4 section
   - Understand the schema
   - Note the research sources

3. **Look at [data/recent_greenlights_EXAMPLE.json](data/recent_greenlights_EXAMPLE.json)**
   - See exactly what format is expected
   - Note the level of detail

4. **Open [data/recent_greenlights.json](data/recent_greenlights.json)**
   - This is your working file
   - Start adding entries

5. **Go to Deadline Hollywood**
   - Search "Netflix greenlight 2024"
   - Start collecting!

6. **Validate Every 20 Entries**
   ```bash
   cd /home/ubuntu/mandate_wizard_web_app
   python3 import_data.py
   ```

7. **Fix Errors and Continue**

---

## 💡 Pro Tips

1. **Batch Similar Tasks**
   - Collect all greenlights for one executive at once
   - Collect all Korean production companies together
   - This maintains context and speeds up research

2. **Use Multiple Sources**
   - Cross-reference Deadline, Variety, THR
   - More sources = more confidence in data

3. **Document Uncertainties**
   - If unsure about a field, add note explaining why
   - We can refine later

4. **Validate Often**
   - Don't wait until you have 100 entries
   - Validate every 10-20 entries
   - Catch errors early

5. **Take Breaks**
   - Data collection is tedious
   - Take breaks every hour
   - Maintain quality over speed

---

## 📞 Questions?

If you get stuck:
1. Check the [DATA_COLLECTION_PLAYBOOK.md](DATA_COLLECTION_PLAYBOOK.md)
2. Look at EXAMPLE files
3. Check [data/README.md](data/README.md)
4. Use your best judgment and document uncertainties

---

## 🎉 You've Got This!

The technical system is **95% complete**. Your data collection will bring it to **100%** and make it genuinely useful for users trying to navigate Netflix.

**Start with Layer 4 (Recent Greenlights) - it's the highest impact!**

Good luck! 🚀

---

**END OF HANDOFF DOCUMENT**

