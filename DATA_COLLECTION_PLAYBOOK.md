# Mandate Wizard: Data Collection Playbook

**Version:** 1.0  
**Last Updated:** October 26, 2025  
**Purpose:** Complete guide for collecting and formatting data for Layers 3-8

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Layer 3: Production Company Database](#layer-3-production-company-database)
3. [Layer 4: Recent Greenlights Database](#layer-4-recent-greenlights-database)
4. [Layer 5: Pitch Requirements](#layer-5-pitch-requirements)
5. [Layer 6: Packaging Intelligence](#layer-6-packaging-intelligence)
6. [Layer 7: Timing & Strategy](#layer-7-timing--strategy)
7. [Data Import Instructions](#data-import-instructions)
8. [Quality Validation](#quality-validation)

---

## Overview

### What We Have (Layers 1-2)
✅ **Layer 1: Executive Routing** - 266 executives in Neo4j  
✅ **Layer 2: Executive Mandates** - 147 quotes in data_integration system

### What We Need (Layers 3-8)
❌ **Layer 3:** Production company relationships and contact info  
❌ **Layer 4:** Recent greenlights (last 6-12 months)  
❌ **Layer 5:** Pitch format requirements and processes  
❌ **Layer 6:** Talent/packaging preferences  
❌ **Layer 7:** Executive schedules and industry events  
❌ **Layer 8:** Success rates and timelines (optional)

### Priority Order
1. **Layer 4** (Recent Greenlights) - Most requested, highest impact
2. **Layer 3** (Production Companies) - Critical for access pathway
3. **Layer 5** (Pitch Requirements) - High value for users
4. **Layer 6** (Packaging Intelligence) - Nice to have
5. **Layer 7** (Timing & Strategy) - Nice to have

---

## Layer 3: Production Company Database

### Purpose
Help users understand which production companies work with which Netflix executives, and how to access them.

### Data Structure

**File Format:** JSON  
**File Location:** `/home/ubuntu/mandate_wizard_web_app/data/production_companies.json`

**Schema:**
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
          "genre": "Thriller",
          "success_level": "Massive hit"
        },
        {
          "title": "Kingdom",
          "year": 2019,
          "genre": "Horror",
          "success_level": "Critical acclaim"
        }
      ],
      "submission_info": {
        "accepts_unsolicited": false,
        "submission_method": "Through agent/manager only",
        "contact_email": "",
        "contact_phone": "",
        "website": "https://www.studiodragon.net"
      },
      "notes": "Major Korean production company with exclusive Netflix partnership. Focus on high-concept, genre-defining content."
    }
  ]
}
```

### Data Collection Guidelines

**For Each Production Company:**

1. **Company Name** (required)
   - Official company name
   - Check company website or LinkedIn

2. **Country** (required)
   - Primary country of operation
   - Use full country name (not abbreviations)

3. **Specializations** (required, array)
   - List 2-5 genres/formats they specialize in
   - Use standard genres: Drama, Comedy, Thriller, Horror, Documentary, Unscripted, Animation, etc.

4. **Netflix Relationship** (required)
   - **has_deal**: true/false - Do they have an active Netflix deal?
   - **deal_type**: "First-look deal", "Overall deal", "Project-based", "None"
   - **deal_year**: Year the deal was signed (if known)
   - **primary_executive**: Which Netflix executive they work with most
   - **secondary_executives**: Array of other executives they've worked with

5. **Notable Projects** (required, minimum 2)
   - **title**: Project name
   - **year**: Release year
   - **genre**: Primary genre
   - **success_level**: "Massive hit", "Hit", "Moderate success", "Critical acclaim", "Underperformed"

6. **Submission Info** (best effort)
   - **accepts_unsolicited**: true/false - Do they accept unsolicited submissions?
   - **submission_method**: How to submit (agent only, open submissions, etc.)
   - **contact_email**: Public submission email (if available)
   - **contact_phone**: Public phone (if available)
   - **website**: Company website URL

7. **Notes** (optional)
   - 1-2 sentences about the company's focus or strategy
   - Any relevant context for pitching

### Research Sources

- **Deadline Hollywood** - Production company deals
- **Variety** - Netflix partnerships
- **Company websites** - Submission policies
- **LinkedIn** - Company profiles and contacts
- **IMDb Pro** - Production credits and relationships
- **The Hollywood Reporter** - Deal announcements

### How Many to Collect

**Minimum Target:** 50 production companies  
**Ideal Target:** 100+ production companies

**Priority Regions:**
1. United States (20-30 companies)
2. United Kingdom (10-15 companies)
3. South Korea (10-15 companies)
4. Latin America (10-15 companies)
5. Europe (10-15 companies)
6. Other regions (10-15 companies)

### Example Entry

```json
{
  "company_name": "21 Laps Entertainment",
  "country": "United States",
  "specializations": ["Sci-Fi", "Horror", "Thriller", "Young Adult"],
  "netflix_relationship": {
    "has_deal": true,
    "deal_type": "Overall deal",
    "deal_year": 2019,
    "primary_executive": "Peter Friedlander",
    "secondary_executives": ["Bela Bajaria"]
  },
  "notable_projects": [
    {
      "title": "Stranger Things",
      "year": 2016,
      "genre": "Sci-Fi Horror",
      "success_level": "Massive hit"
    },
    {
      "title": "Shadow and Bone",
      "year": 2021,
      "genre": "Fantasy",
      "success_level": "Hit"
    }
  ],
  "submission_info": {
    "accepts_unsolicited": false,
    "submission_method": "Through agent/manager only",
    "contact_email": "",
    "contact_phone": "",
    "website": "https://www.21laps.com"
  },
  "notes": "Shawn Levy's company. Focus on high-concept genre content with broad appeal. Strong track record with Netflix originals."
}
```

---

## Layer 4: Recent Greenlights Database

### Purpose
Show users what executives have recently greenlit to understand current priorities and whether the slate is full.

### Data Structure

**File Format:** JSON  
**File Location:** `/home/ubuntu/mandate_wizard_web_app/data/recent_greenlights.json`

**Schema:**
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
      "notes": "Renewal after strong Season 1 performance. Focus on political intrigue."
    }
  ]
}
```

### Data Collection Guidelines

**For Each Greenlight:**

1. **Project Title** (required)
   - Official project name
   - Include season number if applicable

2. **Executive Name** (required)
   - Netflix executive who greenlit it
   - Use full name matching our database (Don Kang, Peter Friedlander, etc.)

3. **Greenlight Date** (required)
   - Date the project was officially greenlit (YYYY-MM-DD)
   - If exact date unknown, use first day of month

4. **Announcement Date** (required)
   - Date publicly announced (YYYY-MM-DD)
   - This is usually easier to find than greenlight date

5. **Genre** (required)
   - Primary genre: Drama, Comedy, Thriller, Horror, Documentary, Unscripted, etc.
   - Can use compound genres: "Political Drama", "Romantic Comedy", etc.

6. **Format** (required)
   - "Series", "Limited Series", "Film", "Documentary Series", "Documentary Film", "Special", "Unscripted Series"

7. **Season Number** (if applicable)
   - 1 for new series, 2+ for renewals
   - null for films

8. **Episode Count** (if known)
   - Number of episodes ordered
   - null if not announced

9. **Production Company** (required)
   - Company producing the project
   - Should match Layer 3 data when possible

10. **Showrunner** (if applicable)
    - Showrunner name for series
    - Director name for films
    - null if not announced

11. **Cast** (optional, array)
    - Key cast members (if announced)
    - List 2-5 most notable names

12. **Budget Range** (if known)
    - Estimated budget per episode or total budget
    - Format: "$5-8M per episode" or "$50-80M total"
    - null if not available

13. **Target Release** (if known)
    - Expected release quarter/year
    - Format: "Q2 2024", "2024", "TBD"

14. **Source URL** (required)
    - URL to announcement article
    - Prefer Deadline, Variety, THR

15. **Notes** (optional)
    - 1-2 sentences about why it was greenlit
    - Any relevant context

### Research Sources

- **Deadline Hollywood** - Primary source for greenlights
- **Variety** - Industry announcements
- **The Hollywood Reporter** - Deal coverage
- **Netflix Press Site** - Official announcements
- **What's on Netflix** - Tracking new projects

### Time Range

**Collect greenlights from:** January 2024 - Present  
**Update frequency:** Monthly

### How Many to Collect

**Minimum Target:** 100 greenlights  
**Ideal Target:** 200+ greenlights

**Per Executive (if available):**
- Aim for 5-10 recent greenlights per major executive
- Focus on last 6-12 months

### Example Entry

```json
{
  "project_title": "Physical: 100 Season 2",
  "executive_name": "Don Kang",
  "greenlight_date": "2023-03-15",
  "announcement_date": "2023-03-20",
  "genre": "Unscripted Competition",
  "format": "Unscripted Series",
  "season_number": 2,
  "episode_count": 9,
  "production_company": "The Mediaplex",
  "showrunner": "Jang Ho-gi",
  "cast": [],
  "budget_range": "$2-3M per episode",
  "target_release": "Q1 2024",
  "source_url": "https://deadline.com/physical-100-season-2-renewal",
  "notes": "Renewal after massive global success of Season 1. Focus on physical competition format with high production value."
}
```

---

## Layer 5: Pitch Requirements

### Purpose
Tell users exactly how to format their pitch for specific executives or content types.

### Data Structure

**File Format:** JSON  
**File Location:** `/home/ubuntu/mandate_wizard_web_app/data/pitch_requirements.json`

**Schema:**
```json
{
  "pitch_requirements": [
    {
      "executive_name": "Peter Friedlander",
      "content_type": "Scripted Series",
      "submission_process": {
        "step_1": "Secure representation (agent or manager)",
        "step_2": "Agent submits logline and one-pager to executive's office",
        "step_3": "If interested, request for series bible and pilot script",
        "step_4": "Pitch meeting scheduled (30-45 minutes)",
        "step_5": "Follow-up materials requested if interested"
      },
      "required_materials": {
        "logline": {
          "required": true,
          "format": "1-2 sentences, under 50 words",
          "focus": "Hook, protagonist, conflict"
        },
        "one_pager": {
          "required": true,
          "format": "1 page PDF, single-spaced",
          "sections": ["Logline", "Synopsis", "Tone/Comparisons", "Why Now"]
        },
        "series_bible": {
          "required": true,
          "format": "10-20 pages",
          "sections": ["Series Overview", "Characters", "World", "Season Arcs", "Episode Breakdowns"]
        },
        "pilot_script": {
          "required": true,
          "format": "Standard screenplay format, 50-65 pages",
          "notes": "Must be polished, production-ready"
        }
      },
      "pitch_meeting_format": {
        "duration": "30-45 minutes",
        "attendees": "Executive + 1-2 development execs",
        "presentation_style": "Conversational, not formal presentation",
        "leave_behind": "One-pager only (they already have materials)"
      },
      "decision_timeline": {
        "initial_response": "1-2 weeks",
        "development_decision": "4-8 weeks",
        "greenlight_decision": "3-6 months"
      },
      "preferences": {
        "loves": ["Character-driven", "Elevated genre", "International appeal"],
        "avoids": ["Procedurals", "Anthology", "Overly niche"]
      },
      "source_url": "https://...",
      "last_updated": "2024-10-01"
    }
  ]
}
```

### Data Collection Guidelines

**For Each Executive/Content Type:**

1. **Executive Name** (required)
   - Full name matching our database

2. **Content Type** (required)
   - "Scripted Series", "Limited Series", "Film", "Documentary", "Unscripted", etc.

3. **Submission Process** (required)
   - Step-by-step process from first contact to pitch meeting
   - Use step_1, step_2, etc.
   - Be specific about who submits what

4. **Required Materials** (required)
   - For each material type:
     - **required**: true/false
     - **format**: Specific formatting requirements
     - **sections** or **focus**: What to include
     - **notes**: Any special instructions

5. **Pitch Meeting Format** (if known)
   - **duration**: How long the meeting is
   - **attendees**: Who will be in the room
   - **presentation_style**: Formal vs. conversational
   - **leave_behind**: What materials to leave

6. **Decision Timeline** (if known)
   - **initial_response**: How long for first response
   - **development_decision**: How long for development decision
   - **greenlight_decision**: How long from pitch to greenlight

7. **Preferences** (optional)
   - **loves**: Array of things this executive loves
   - **avoids**: Array of things to avoid

8. **Source URL** (required)
   - Where you found this information

9. **Last Updated** (required)
   - Date you collected this data (YYYY-MM-DD)

### Research Sources

- **Industry interviews** - Executives discussing their process
- **Producer testimonials** - People who've pitched successfully
- **Industry blogs** - Screenwriting/producing blogs
- **Panel discussions** - Industry events and conferences
- **Trade publications** - Deadline, Variety articles about pitch processes

### How Many to Collect

**Minimum Target:** 20 entries  
**Ideal Target:** 50+ entries

**Priority:**
1. Top 10 Netflix executives (1 entry per content type they handle)
2. General Netflix pitch requirements (if executive-specific not available)

### Example Entry

```json
{
  "executive_name": "Don Kang",
  "content_type": "Unscripted Series",
  "submission_process": {
    "step_1": "Production company with Netflix relationship submits sizzle reel",
    "step_2": "If interested, request for full pitch deck",
    "step_3": "Pitch meeting scheduled (45-60 minutes)",
    "step_4": "Pilot episode greenlit if strong interest"
  },
  "required_materials": {
    "sizzle_reel": {
      "required": true,
      "format": "3-5 minute video, high production value",
      "focus": "Show format, energy, unique hook"
    },
    "pitch_deck": {
      "required": true,
      "format": "15-25 slides, PDF or Keynote",
      "sections": ["Format Overview", "Sample Episodes", "Casting Strategy", "Production Plan", "Budget"]
    }
  },
  "pitch_meeting_format": {
    "duration": "45-60 minutes",
    "attendees": "Executive + unscripted development team",
    "presentation_style": "Formal presentation with deck",
    "leave_behind": "Pitch deck PDF"
  },
  "decision_timeline": {
    "initial_response": "1-2 weeks",
    "development_decision": "2-4 weeks",
    "greenlight_decision": "1-3 months"
  },
  "preferences": {
    "loves": ["High-concept formats", "Global appeal", "Spectacle", "Fresh twists on competition"],
    "avoids": ["Low-budget reality", "Dating shows", "Copycat formats"]
  },
  "source_url": "https://variety.com/don-kang-unscripted-strategy",
  "last_updated": "2024-10-15"
}
```

---

## Layer 6: Packaging Intelligence

### Purpose
Help users understand what talent/packaging makes projects more attractive to specific executives.

### Data Structure

**File Format:** JSON  
**File Location:** `/home/ubuntu/mandate_wizard_web_app/data/packaging_intelligence.json`

**Schema:**
```json
{
  "packaging_intelligence": [
    {
      "executive_name": "Peter Friedlander",
      "content_type": "Scripted Drama",
      "talent_preferences": {
        "showrunners": {
          "tier_1": ["Shonda Rhimes", "Ryan Murphy", "Jenji Kohan"],
          "tier_2": ["Emerging showrunners with 1-2 successful series"],
          "notes": "Values proven track record or unique voice"
        },
        "directors": {
          "tier_1": ["Film directors transitioning to TV"],
          "tier_2": ["TV directors with distinctive visual style"],
          "notes": "Prefers cinematic approach"
        },
        "cast": {
          "lead_actor_importance": "High",
          "ensemble_vs_star": "Star-driven preferred",
          "international_appeal": "Critical",
          "notes": "Needs at least one recognizable name for marketing"
        },
        "producers": {
          "production_company_importance": "High",
          "preferred_partners": ["21 Laps", "Shondaland", "Tomorrow Studios"],
          "notes": "Prefers established production companies with Netflix relationships"
        }
      },
      "successful_packages": [
        {
          "project": "The Diplomat",
          "package": "Debora Cahn (showrunner) + Keri Russell (star) + Janice Williams (producer)",
          "why_it_worked": "Proven showrunner + Emmy-winning star + experienced producer"
        }
      ],
      "packaging_tips": [
        "Attach showrunner before pitching if possible",
        "Star attachment significantly increases greenlight chances",
        "International cast member helps with global appeal"
      ],
      "source_url": "https://...",
      "last_updated": "2024-10-01"
    }
  ]
}
```

### Data Collection Guidelines

**For Each Executive/Content Type:**

1. **Executive Name** (required)
2. **Content Type** (required)

3. **Talent Preferences** (required)
   - For each role type (showrunners, directors, cast, producers):
     - **tier_1**: Top-tier talent this executive loves
     - **tier_2**: Mid-tier talent that works
     - **notes**: Specific preferences or patterns

4. **Successful Packages** (optional, array)
   - Examples of packages that got greenlit
   - **project**: Project name
   - **package**: Who was attached
   - **why_it_worked**: Analysis of why this package succeeded

5. **Packaging Tips** (required, array)
   - 3-5 actionable tips for packaging projects for this executive

6. **Source URL** (required)
7. **Last Updated** (required)

### Research Sources

- **IMDb Pro** - Credits and attachments
- **Deadline Hollywood** - Deal announcements
- **Variety** - Talent attachments
- **Industry interviews** - Executives discussing what they look for

### How Many to Collect

**Minimum Target:** 15 entries  
**Ideal Target:** 30+ entries

---

## Layer 7: Timing & Strategy

### Purpose
Help users understand when to pitch (industry events, executive schedules, seasonal patterns).

### Data Structure

**File Format:** JSON  
**File Location:** `/home/ubuntu/mandate_wizard_web_app/data/timing_strategy.json`

**Schema:**
```json
{
  "timing_strategy": {
    "industry_events": [
      {
        "event_name": "Busan International Film Festival",
        "dates": "2024-10-02 to 2024-10-11",
        "location": "Busan, South Korea",
        "relevant_executives": ["Don Kang", "Kaata Sakamoto"],
        "opportunity_type": "In-person meetings",
        "notes": "Major Asian content market. Don Kang typically attends."
      }
    ],
    "seasonal_patterns": {
      "best_months_to_pitch": ["September", "October", "January", "February"],
      "avoid_months": ["December", "July", "August"],
      "reasons": "Avoid year-end holidays and summer vacation periods. Fall and early year are budget planning seasons."
    },
    "executive_schedules": [
      {
        "executive_name": "Peter Friedlander",
        "typical_availability": "Tuesdays-Thursdays",
        "busy_periods": ["May (Upfronts)", "December (Holidays)"],
        "best_time_to_pitch": "September-November",
        "notes": "Most responsive in fall during development season"
      }
    ]
  }
}
```

### Data Collection Guidelines

**Industry Events:**
- Major film festivals (Sundance, Cannes, Toronto, Busan, etc.)
- Industry conferences (MIPCOM, Content London, etc.)
- Netflix-specific events

**Seasonal Patterns:**
- When Netflix typically greenlights projects
- Budget cycle timing
- Development season patterns

**Executive Schedules:**
- When specific executives are most available
- Recurring busy periods
- Best times to pitch

### Research Sources

- **Festival websites** - Event dates and attendees
- **Industry calendars** - Conference schedules
- **Trade publications** - Coverage of executive appearances
- **Producer testimonials** - When they successfully pitched

### How Many to Collect

**Minimum Target:** 20 industry events + 10 executive schedules  
**Ideal Target:** 50+ events + 20+ executive schedules

---

## Data Import Instructions

### Step 1: Validate JSON Files

Before importing, validate each JSON file:

```bash
cd /home/ubuntu/mandate_wizard_web_app/data
python3 -m json.tool production_companies.json > /dev/null && echo "✅ Valid JSON" || echo "❌ Invalid JSON"
```

### Step 2: Run Import Scripts

I've created import scripts for each layer:

```bash
cd /home/ubuntu/mandate_wizard_web_app
python3 import_layer3_data.py
python3 import_layer4_data.py
python3 import_layer5_data.py
python3 import_layer6_data.py
python3 import_layer7_data.py
```

### Step 3: Verify Import

```bash
python3 verify_data_import.py
```

---

## Quality Validation

### Checklist for Each Data Entry

**Layer 3 (Production Companies):**
- [ ] Company name is official and correct
- [ ] At least 2 notable projects listed
- [ ] Netflix relationship status is accurate
- [ ] Primary executive name matches our database
- [ ] Website URL is valid (if provided)

**Layer 4 (Recent Greenlights):**
- [ ] Project title is official
- [ ] Executive name matches our database exactly
- [ ] Date is in YYYY-MM-DD format
- [ ] Source URL is valid and accessible
- [ ] Genre and format are from standard list

**Layer 5 (Pitch Requirements):**
- [ ] Executive name matches our database
- [ ] At least 3 steps in submission process
- [ ] At least 2 required materials specified
- [ ] Source URL provided
- [ ] Last updated date is recent (within 6 months)

**Layer 6 (Packaging Intelligence):**
- [ ] Executive name matches our database
- [ ] At least 3 packaging tips provided
- [ ] Talent preferences are specific, not generic
- [ ] At least 1 successful package example

**Layer 7 (Timing & Strategy):**
- [ ] Event dates are current year or next year
- [ ] Executive names match our database
- [ ] Locations are specific
- [ ] Opportunity types are clear

---

## Contact for Questions

If you have questions while collecting data:
1. Check this playbook first
2. Look at the example entries
3. Use your best judgment - we can refine later
4. Document any uncertainties in the "notes" field

---

**END OF PLAYBOOK**

