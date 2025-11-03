# Mandate Wizard: Data Collection Guide

## 🎯 Quick Start

You are collecting data to populate Layers 3-8 of the Mandate Wizard intelligence system.

**What you need to do:**
1. Read the [DATA_COLLECTION_PLAYBOOK.md](../DATA_COLLECTION_PLAYBOOK.md) (one level up)
2. Look at the EXAMPLE files in this directory to see the format
3. Add entries to the corresponding JSON files in this directory
4. Validate and import when ready

---

## 📁 Files in This Directory

### Template Files (Fill These In)
- `production_companies.json` - Layer 3 data (PRIORITY #2)
- `recent_greenlights.json` - Layer 4 data (PRIORITY #1 - START HERE)
- `pitch_requirements.json` - Layer 5 data (PRIORITY #3)
- `packaging_intelligence.json` - Layer 6 data (PRIORITY #4)
- `timing_strategy.json` - Layer 7 data (PRIORITY #5)

### Example Files (Reference These)
- `production_companies_EXAMPLE.json` - See 3 complete examples
- `recent_greenlights_EXAMPLE.json` - See 3 complete examples

---

## 🚀 Recommended Workflow

### Step 1: Start with Layer 4 (Recent Greenlights)
**Why:** Most requested by users, highest impact

**Target:** 100+ greenlights from January 2024 - Present

**Process:**
1. Go to Deadline Hollywood, search "Netflix greenlight"
2. For each greenlight, copy the template below
3. Fill in all fields
4. Add to `recent_greenlights.json`

**Template to copy:**
```json
{
  "project_title": "",
  "executive_name": "",
  "greenlight_date": "YYYY-MM-DD",
  "announcement_date": "YYYY-MM-DD",
  "genre": "",
  "format": "",
  "season_number": null,
  "episode_count": null,
  "production_company": "",
  "showrunner": "",
  "cast": [],
  "budget_range": "",
  "target_release": "",
  "source_url": "",
  "notes": ""
}
```

### Step 2: Layer 3 (Production Companies)
**Why:** Critical for access pathway

**Target:** 50+ production companies with Netflix deals

**Process:**
1. Search "Netflix production company deal"
2. For each company, copy the template below
3. Fill in all fields
4. Add to `production_companies.json`

**Template to copy:**
```json
{
  "company_name": "",
  "country": "",
  "specializations": [],
  "netflix_relationship": {
    "has_deal": true,
    "deal_type": "",
    "deal_year": 2024,
    "primary_executive": "",
    "secondary_executives": []
  },
  "notable_projects": [
    {
      "title": "",
      "year": 2024,
      "genre": "",
      "success_level": ""
    }
  ],
  "submission_info": {
    "accepts_unsolicited": false,
    "submission_method": "",
    "contact_email": "",
    "contact_phone": "",
    "website": ""
  },
  "notes": ""
}
```

### Step 3: Layer 5 (Pitch Requirements)
**Why:** High value for users preparing pitches

**Target:** 20+ entries (one per major executive/content type)

**Process:**
1. Search "[Executive Name] pitch process Netflix"
2. Look for interviews, panel discussions, producer testimonials
3. Fill in template
4. Add to `pitch_requirements.json`

**Template to copy:**
```json
{
  "executive_name": "",
  "content_type": "",
  "submission_process": {
    "step_1": "",
    "step_2": "",
    "step_3": ""
  },
  "required_materials": {
    "logline": {
      "required": true,
      "format": "",
      "focus": ""
    }
  },
  "pitch_meeting_format": {
    "duration": "",
    "attendees": "",
    "presentation_style": "",
    "leave_behind": ""
  },
  "decision_timeline": {
    "initial_response": "",
    "development_decision": "",
    "greenlight_decision": ""
  },
  "preferences": {
    "loves": [],
    "avoids": []
  },
  "source_url": "",
  "last_updated": "2024-10-26"
}
```

---

## ✅ Quality Checklist

Before submitting data, verify:

**For ALL entries:**
- [ ] All required fields are filled in
- [ ] Dates are in YYYY-MM-DD format
- [ ] Executive names match exactly (Don Kang, Peter Friedlander, etc.)
- [ ] Source URLs are valid
- [ ] JSON syntax is valid (no trailing commas, proper quotes)

**For Layer 4 (Greenlights):**
- [ ] Project title is official
- [ ] Announcement date is verifiable
- [ ] Genre is from standard list (Drama, Comedy, Thriller, etc.)
- [ ] Format is from standard list (Series, Limited Series, Film, etc.)

**For Layer 3 (Production Companies):**
- [ ] Company name is official
- [ ] At least 2 notable projects listed
- [ ] Netflix relationship status is accurate

---

## 🔧 Validation & Import

### Validate JSON Syntax
```bash
cd /home/ubuntu/mandate_wizard_web_app/data
python3 -m json.tool recent_greenlights.json > /dev/null && echo "✅ Valid" || echo "❌ Invalid"
```

### Import Data (when ready)
```bash
cd /home/ubuntu/mandate_wizard_web_app
python3 import_data.py
```

---

## 📊 Progress Tracking

Track your progress here:

**Layer 4 (Recent Greenlights):**
- Target: 100+ entries
- Current: _____ entries
- Status: [ ] Not Started [ ] In Progress [ ] Complete

**Layer 3 (Production Companies):**
- Target: 50+ entries
- Current: _____ entries
- Status: [ ] Not Started [ ] In Progress [ ] Complete

**Layer 5 (Pitch Requirements):**
- Target: 20+ entries
- Current: _____ entries
- Status: [ ] Not Started [ ] In Progress [ ] Complete

**Layer 6 (Packaging Intelligence):**
- Target: 15+ entries
- Current: _____ entries
- Status: [ ] Not Started [ ] In Progress [ ] Complete

**Layer 7 (Timing & Strategy):**
- Target: 20 events + 10 schedules
- Current: _____ entries
- Status: [ ] Not Started [ ] In Progress [ ] Complete

---

## 🆘 Common Issues

**Issue:** JSON syntax error  
**Solution:** Check for trailing commas, missing quotes, unclosed brackets

**Issue:** Executive name doesn't match  
**Solution:** Use exact names from our database (see list in playbook)

**Issue:** Can't find information  
**Solution:** Document what you couldn't find in "notes" field, move on

**Issue:** Unsure about a field  
**Solution:** Use your best judgment, add note explaining uncertainty

---

## 📞 Questions?

If you're stuck:
1. Check the [DATA_COLLECTION_PLAYBOOK.md](../DATA_COLLECTION_PLAYBOOK.md)
2. Look at EXAMPLE files
3. Use your best judgment
4. Document uncertainties in "notes" field

---

**Good luck! Start with Layer 4 (Recent Greenlights) - it's the highest priority!**

