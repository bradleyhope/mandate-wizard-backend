# Mandate Wizard - User Personas

**Purpose:** Deep testing and engine optimization  
**Date:** October 28, 2025

---

## Persona 1: Sarah Chen - Independent Producer

### Background
- **Age:** 34
- **Location:** Los Angeles, CA
- **Company:** Chen Productions (independent)
- **Experience:** 8 years in development
- **Credits:** 2 indie films, 3 TV pilots (unproduced)
- **Goal:** Get first major studio/streamer deal

### Pain Points
- Spends 15+ hours/week researching what streamers are buying
- Misses opportunities because she hears about mandates too late
- Doesn't have relationships with most executives
- Needs to know which executives to target with which projects

### Use Cases
1. Finding mandates that match her slate
2. Researching executives before pitch meetings
3. Tracking competitive greenlights
4. Identifying emerging trends
5. Building target lists for projects

### Query Patterns
- Specific mandate searches ("What is Netflix looking for in limited series?")
- Executive research ("Tell me about Jinny Howe's taste")
- Competitive intelligence ("What rom-coms got greenlit this quarter?")
- Trend analysis ("Are streamers still buying true crime?")
- Strategic planning ("Which executives should I pitch my thriller to?")

---

## Persona 2: Marcus Williams - Literary Manager

### Background
- **Age:** 41
- **Location:** New York, NY
- **Company:** Elevation Management
- **Clients:** 12 writers (TV and film)
- **Experience:** 15 years in representation
- **Goal:** Get clients staffed and projects sold

### Pain Points
- Managing 12 different careers with different needs
- Needs to stay ahead of market trends for client guidance
- Must identify opportunities quickly before competitors
- Needs ammunition for negotiations

### Use Cases
1. Matching clients to open writing assignments
2. Researching which shows are hiring writers
3. Tracking executive moves (who's buying what now)
4. Identifying pitch opportunities for client projects
5. Market intelligence for career guidance

### Query Patterns
- Opportunity searches ("What shows are hiring writers right now?")
- Executive tracking ("Where did [executive name] move to?")
- Genre trends ("Is sci-fi selling better than last year?")
- Company mandates ("What is Apple TV+ looking for?")
- Competitive analysis ("Who else is developing [similar project]?")

---

## Persona 3: Jennifer Park - Development Executive

### Background
- **Age:** 29
- **Location:** Los Angeles, CA
- **Company:** Mid-size production company (50 employees)
- **Role:** VP of Development
- **Experience:** 6 years in development
- **Goal:** Find projects that match company's deals

### Pain Points
- Needs to stay on top of what competitors are doing
- Must understand what buyers are looking for
- Pressure to find the next big thing
- Needs to justify pass/pursue decisions to bosses

### Use Cases
1. Competitive intelligence (what are rivals developing)
2. Understanding buyer mandates (what will sell)
3. Tracking talent availability
4. Researching comps for projects in development
5. Market timing decisions

### Query Patterns
- Competitive tracking ("What is [competitor company] developing?")
- Buyer research ("What did Netflix buy from [company] recently?")
- Talent tracking ("Who is [showrunner] working with now?")
- Market analysis ("Are anthology series still selling?")
- Strategic planning ("Should we develop this as limited or ongoing?")

---

## Persona 4: David Rodriguez - Entertainment Consultant

### Background
- **Age:** 52
- **Location:** Santa Monica, CA
- **Company:** Rodriguez Advisory (solo consultant)
- **Clients:** 5-8 production companies, 2 agencies
- **Experience:** 25 years (former studio exec)
- **Goal:** Provide valuable strategic intelligence to clients

### Pain Points
- Clients expect deep, actionable insights
- Needs to synthesize information from many sources
- Must stay current despite not being inside a company
- Needs to produce reports and deliverables

### Use Cases
1. Producing market intelligence reports for clients
2. Strategic advisory on what to develop
3. Competitive landscape analysis
4. Executive briefings before big meetings
5. Trend forecasting and analysis

### Query Patterns
- Deep analysis ("Give me a comprehensive analysis of Netflix's drama strategy")
- Trend forecasting ("What genres will be hot in 2026?")
- Competitive positioning ("How does [company] compare to competitors?")
- Executive intelligence ("What are the top 10 executives buying drama?")
- Market sizing ("How many limited series got greenlit this year?")

---

## Persona 5: Amy Thompson - Showrunner

### Background
- **Age:** 45
- **Location:** Los Angeles, CA
- **Credits:** 2 successful series, 1 in production
- **Experience:** 20 years (writer → showrunner)
- **Current:** Developing next project
- **Goal:** Set up next show at best possible home

### Pain Points
- Needs to understand which streamers/networks are right fit
- Must know what's already in development (avoid redundancy)
- Wants to pitch to executives who will champion her work
- Needs leverage in negotiations

### Use Cases
1. Finding the right home for her next project
2. Researching executives who might champion her work
3. Understanding what's already in development
4. Tracking where similar shows have sold
5. Preparing for pitch meetings

### Query Patterns
- Strategic fit ("Which streamer is the best fit for [project description]?")
- Executive research ("Who are the top drama executives at HBO?")
- Competitive landscape ("What shows like mine are in development?")
- Deal intelligence ("What kind of deals is [streamer] making?")
- Timing ("Is now a good time to pitch [genre] to [streamer]?")

---

## Persona 6: Michael Zhang - Talent Agent (CAA)

### Background
- **Age:** 36
- **Location:** Los Angeles, CA
- **Company:** CAA (packaging agent)
- **Clients:** 20 actors, 5 directors
- **Experience:** 10 years in talent representation
- **Goal:** Package projects and get clients hired

### Pain Points
- Needs to know about projects before they're announced
- Must match clients to right opportunities
- Competitive intelligence on what other agencies are doing
- Needs to move fast when opportunities arise

### Use Cases
1. Finding roles for actor clients
2. Identifying directing opportunities
3. Packaging intelligence (who's attached to what)
4. Tracking production starts
5. Executive relationships (who's hiring)

### Query Patterns
- Opportunity searches ("What projects are casting lead roles?")
- Packaging intelligence ("Who's attached to [project]?")
- Production tracking ("What's going into production next quarter?")
- Executive relationships ("Who should I call about [project]?")
- Competitive intel ("What is [competing agency] packaging?")

---

## Persona 7: Lisa Martinez - Investment Analyst

### Background
- **Age:** 31
- **Location:** New York, NY
- **Company:** Entertainment-focused investment fund
- **Role:** Senior Analyst
- **Experience:** 7 years in entertainment finance
- **Goal:** Identify investment opportunities in content/production

### Pain Points
- Needs data-driven insights on market trends
- Must understand which content strategies are working
- Needs to evaluate production company performance
- Must forecast future market movements

### Use Cases
1. Market trend analysis for investment thesis
2. Evaluating production company performance
3. Understanding streamer strategies
4. Identifying emerging opportunities
5. Risk assessment for investments

### Query Patterns
- Market analysis ("What percentage of greenlights are limited series vs ongoing?")
- Company performance ("How many projects has [company] sold this year?")
- Strategic analysis ("Is Netflix shifting away from [genre]?")
- Trend forecasting ("What content categories are growing?")
- Risk assessment ("Are streamers cutting back on [type] of content?")

---

## Testing Methodology

For each persona, I will:

1. **Run 10-15 representative queries**
2. **Evaluate response quality** (relevance, accuracy, completeness)
3. **Identify gaps** (missing data, poor synthesis, irrelevant answers)
4. **Track response times**
5. **Note failure modes** (errors, timeouts, poor quality)
6. **Suggest improvements** (data needs, algorithm changes, prompt engineering)

---

## Success Criteria

**Good Response:**
- ✅ Directly answers the question
- ✅ Provides specific, actionable information
- ✅ Includes relevant examples and context
- ✅ Suggests follow-up queries
- ✅ Response time < 5 seconds

**Poor Response:**
- ❌ Generic or vague answer
- ❌ Missing key information
- ❌ Irrelevant context
- ❌ No actionable insights
- ❌ Response time > 10 seconds

---

## Next Steps

1. Run testing sessions for each persona
2. Document all queries and responses
3. Analyze patterns and failure modes
4. Create optimization recommendations
5. Implement improvements
6. Re-test to validate improvements

