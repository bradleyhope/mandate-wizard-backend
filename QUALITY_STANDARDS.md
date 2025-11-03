# Mandate Wizard Quality Standards & Completeness Criteria

**Author:** Manus AI  
**Date:** October 31, 2025  
**Version:** 1.0

---

## Purpose

This document establishes measurable quality standards for all data entities in Mandate Wizard, defines completeness scoring methodology, and provides operational guidelines for maintaining high-quality data at scale.

---

## Quality Framework

### Quality Dimensions

Data quality in Mandate Wizard is assessed across five dimensions:

**1. Completeness** - Percentage of required and recommended fields populated  
**2. Accuracy** - Correctness of information against authoritative sources  
**3. Freshness** - Recency of data relative to real-world events  
**4. Consistency** - Uniformity of formatting and naming conventions  
**5. Linkage** - Presence of relationships to other entities

---

## Completeness Scoring

### Greenlight Completeness

**Formula:**
```
Completeness Score = (Σ(field_weight × field_populated)) / 100
```

**Field Weights:**

| Field | Weight | Tier | Rationale |
|-------|--------|------|-----------|
| `title` | 20% | Required | Core identifier, essential for all queries |
| `executive` | 20% | Required | Enables executive profiling and pitch targeting |
| `genre` | 15% | Required | Essential for categorization and filtering |
| `format` | 15% | Required | Essential for market analysis |
| `talent` | 15% | Recommended | Enables relationship mapping and warm introductions |
| `production_company` | 10% | Recommended | Industry network insights |
| `date` | 5% | Recommended | Temporal trend analysis |
| **Subtotal** | **100%** | - | - |
| `logline` | +10% | Bonus | Narrative context for pitch development |
| `description` | +10% | Bonus | Detailed understanding of project scope |
| `episode_count` | +5% | Bonus | Format preference analysis |

**Scoring Tiers:**

| Score Range | Tier | Status | Action Required |
|-------------|------|--------|-----------------|
| 0-49% | 🔴 Critical | Unusable | Immediate healing or deletion |
| 50-79% | ⚠️ Incomplete | Limited utility | Healing recommended within 7 days |
| 80-94% | 🟢 Complete | Functional | Monitor for staleness |
| 95-100% | ✅ High-Quality | Optimal | Maintain and update as needed |
| 100%+ | ⭐ Exceptional | Best-in-class | Showcase example |

**Example Calculation:**

```
Greenlight: "3 Body Problem"
- title: "3 Body Problem" → 20%
- executive: "Peter Friedlander" → 20%
- genre: "Sci-Fi, Mystery" → 15%
- format: "Limited Series" → 15%
- talent: "Benedict Wong, Jovan Adepo" → 15%
- production_company: "Plan B Entertainment" → 10%
- date: "2020-09-01" → 5%
- logline: (present) → +10%
- description: (present) → +10%
- episode_count: 8 → +5%

Total Score: 125% (Exceptional)
```

---

### Quote Completeness

**Field Weights:**

| Field | Weight | Tier | Rationale |
|-------|--------|------|-----------|
| `quote` | 40% | Required | The actual strategic statement |
| `executive` | 30% | Required | Attribution and credibility |
| `context` | 20% | Recommended | Understanding intent and implications |
| `source` | 10% | Recommended | Verification and provenance |
| **Subtotal** | **100%** | - | - |
| `title` | +10% | Bonus | Executive role context |
| `company` | +10% | Bonus | Organizational context |
| `topic` | +5% | Bonus | Thematic categorization |

**Scoring Tiers:** Same as Greenlights

---

### Production Deal Completeness

**Field Weights:**

| Field | Weight | Tier | Rationale |
|-------|--------|------|-----------|
| `company` | 25% | Required | Deal participant |
| `deal_type` | 20% | Required | Nature of agreement |
| `platform` | 15% | Required | Greenlighting entity |
| `year` | 10% | Recommended | Temporal context |
| `genre_focus` | 15% | Recommended | Strategic alignment |
| `notable_projects` | 15% | Recommended | Track record |
| **Subtotal** | **100%** | - | - |
| `duration` | +10% | Bonus | Deal scope |
| `source` | +10% | Bonus | Verification |

**Scoring Tiers:** Same as Greenlights

---

### Person Completeness

**Field Weights:**

| Field | Weight | Tier | Rationale |
|-------|--------|------|-----------|
| `name` | 30% | Required | Core identifier |
| `title` | 25% | Required | Role and authority level |
| `company` | 25% | Required | Organizational affiliation |
| `role` | 20% | Recommended | Functional category |
| **Subtotal** | **100%** | - | - |
| `bio` | +15% | Bonus | Professional background |
| `linkedin_url` | +10% | Bonus | Relationship building |
| `greenlights` (relationship count) | +10% | Bonus | Track record |

**Scoring Tiers:** Same as Greenlights

---

## Freshness Standards

### Staleness Thresholds

| Entity Type | Fresh | Aging | Stale | Critical |
|-------------|-------|-------|-------|----------|
| **Greenlight** | <30 days | 30-90 days | 90-180 days | >180 days |
| **Quote** | <60 days | 60-180 days | 180-365 days | >365 days |
| **Deal** | <90 days | 90-180 days | 180-365 days | >365 days |
| **Person** | <90 days | 90-180 days | 180-365 days | >365 days |

### Update Triggers

**Greenlight Updates:**
- Production start date announced
- Cast additions
- Premiere date set
- Cancellation or renewal
- Awards/critical reception

**Quote Updates:**
- New quote from same executive on same topic
- Executive job change (invalidates old title)
- Company strategy shift (context change)

**Deal Updates:**
- Deal renewal announced
- First project under deal greenlit
- Deal expiration or termination
- Company acquisition/merger

**Person Updates:**
- Job title change
- Company change
- New greenlight attributed
- Major career milestone

---

## Accuracy Standards

### Source Authority Hierarchy

| Tier | Sources | Trust Level | Use Case |
|------|---------|-------------|----------|
| **Tier 1** | Deadline, Variety, THR | 95-100% | Primary citation |
| **Tier 2** | Netflix Tudum, Puck, Vulture | 85-94% | Secondary citation |
| **Tier 3** | Entertainment Weekly, IndieWire | 75-84% | Tertiary citation |
| **Tier 4** | Wikipedia, IMDb | 60-74% | Placeholder only, verify |
| **Tier 5** | Blogs, Reddit | <60% | Do not use |

### Verification Rules

**Executive Names:**
- Must appear in source article
- Must match LinkedIn profile format (if available)
- No generic titles ("Netflix executive" → invalid)
- No inference from context (must be explicitly stated)

**Dates:**
- Prefer exact dates over month/year
- Use article publication date if greenlight date not stated
- Format: YYYY-MM-DD (ISO 8601)

**Genres:**
- Use Netflix/platform official categorization when available
- Maximum 3 genres per project
- Use standardized genre names (see Genre Taxonomy)

---

## Consistency Standards

### Naming Conventions

**Person Names:**
- Format: "First Last" or "First Middle Last"
- No titles (Dr., Mr., Ms.)
- No suffixes unless disambiguating (Jr., Sr., III)
- Examples: "Peter Friedlander", "Bela Bajaria"

**Company Names:**
- Use official legal name or common brand name
- No "Inc.", "LLC" unless necessary for disambiguation
- Examples: "Netflix" (not "Netflix, Inc."), "Plan B Entertainment"

**Platform Names:**
- Use consumer-facing brand name
- Examples: "Netflix", "Amazon Prime Video", "Apple TV+", "Disney+"

### Genre Taxonomy

**Standardized Genres:**
- Action
- Comedy
- Crime
- Documentary
- Drama
- Fantasy
- Horror
- Mystery
- Romance
- Sci-Fi
- Thriller
- Unscripted

**Format Taxonomy:**
- Series (ongoing, multi-season)
- Limited Series (single season, 4-10 episodes)
- Miniseries (single season, 2-3 episodes)
- Film (feature-length)
- Documentary Series
- Documentary Film
- Unscripted Series

---

## Linkage Standards

### Required Relationships

**Greenlight:**
- Must have at least 1 `GREENLIT_BY` relationship (to Executive)
- Should have 1+ `PRODUCED_BY` relationships (to Producer)
- Should have 1+ `MADE_BY` relationships (to Production Company)

**Quote:**
- Must have 1 `SAID_BY` relationship (to Person)
- Should have 1 `REPORTED_IN` relationship (to NewsletterSource)

**Deal:**
- Must have 1 `SIGNED_BY` relationship (to Person or Company)
- Must have 1 `WITH_PLATFORM` relationship (to Platform Company)

**Person:**
- Should have 1+ `GREENLIT` relationships (if Executive)
- Should have 1 `WORKS_FOR` relationship (to Company)

### Orphan Detection

**Orphan Criteria:**
- Greenlight with 0 `GREENLIT_BY` relationships
- Quote with 0 `SAID_BY` relationships
- Person with 0 outgoing relationships
- Deal with 0 `SIGNED_BY` relationships

**Orphan Resolution:**
- Priority 1: Add missing relationships via web search
- Priority 2: Enrich with additional data to enable linking
- Priority 3: Flag for manual review
- Priority 4: Delete if unverifiable after 30 days

---

## Quality Metrics Dashboard

### Daily Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| % High-Quality Greenlights | >60% | <50% |
| % Complete Greenlights | >80% | <70% |
| % Critical Greenlights | <5% | >10% |
| % Fresh Greenlights (<30 days) | >40% | <30% |
| % Stale Greenlights (>90 days) | <20% | >30% |
| % Orphaned Greenlights | <10% | >15% |
| Avg Executive Relationships per Greenlight | >1.5 | <1.0 |

### Weekly Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| New Greenlights Added | >10 | <5 |
| Greenlights Enriched | >20 | <10 |
| Relationships Created | >30 | <15 |
| Source URLs Fixed | >15 | <5 |

### Monthly Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Overall Completeness Score | >85% | <80% |
| Data Freshness Score | >75% | <70% |
| Relationship Density | >2.5 edges/node | <2.0 |
| Source Authority Score | >85% Tier 1-2 | <75% |

---

## Operational Guidelines

### Data Entry Checklist

Before inserting a new Greenlight:
- ✅ Verify title matches official announcement
- ✅ Confirm platform/streamer from Tier 1-2 source
- ✅ Extract genre from official description
- ✅ Identify format (series vs limited series vs film)
- ✅ Find at least 1 executive name in source
- ✅ Record source URL (must be Tier 1-3)
- ✅ Extract date from article or use publication date
- ✅ Check for duplicate entries (fuzzy title match)

### Data Enrichment Checklist

When enriching existing Greenlights:
- ✅ Prioritize records with <80% completeness
- ✅ Use GPT-5 web search for missing fields
- ✅ Verify extracted data against source
- ✅ Don't overwrite existing good data
- ✅ Create relationships (GREENLIT_BY, PRODUCED_BY)
- ✅ Update `updated_at` timestamp
- ✅ Sync to Pinecone after Neo4j update

### Quality Audit Checklist

Monthly quality audits should verify:
- ✅ No greenlights with missing required fields
- ✅ All source URLs are valid (HTTP 200)
- ✅ All dates are in YYYY-MM-DD format
- ✅ All executive names match Person nodes
- ✅ All genres are in standardized taxonomy
- ✅ No duplicate greenlights (same title + platform)
- ✅ Pinecone vector count matches Neo4j node count

---

## Appendix: Quality Score Examples

### Example 1: Critical Quality (45%)

```json
{
  "title": "Untitled Project",  // 20%
  "genre": "Unknown",           // 0% (invalid value)
  "format": "Series",           // 15%
  "streamer": "Netflix",        // 10% (partial credit, no verification)
  "source": "Wikipedia",        // 0% (Tier 4 source)
  "date": "",                   // 0%
  "executive": "",              // 0%
  "talent": "",                 // 0%
  "production_company": ""      // 0%
}
```
**Score: 45%** → 🔴 Critical - Immediate healing required

---

### Example 2: Incomplete Quality (70%)

```json
{
  "title": "The Night Agent",        // 20%
  "genre": "Thriller",               // 15%
  "format": "Series",                // 15%
  "streamer": "Netflix",             // Full credit with source
  "source": "https://deadline.com/...", // Full credit (Tier 1)
  "date": "2021-03-15",              // 5%
  "executive": "Jinny Howe",         // 20%
  "talent": "",                      // 0%
  "production_company": ""           // 0%
}
```
**Score: 70%** → ⚠️ Incomplete - Healing recommended

---

### Example 3: High-Quality (110%)

```json
{
  "title": "3 Body Problem",                    // 20%
  "genre": "Sci-Fi, Mystery",                   // 15%
  "format": "Limited Series",                   // 15%
  "streamer": "Netflix",                        // Full credit
  "source": "https://deadline.com/...",         // Full credit (Tier 1)
  "date": "2020-09-01",                         // 5%
  "executive": "Peter Friedlander",             // 20%
  "talent": "Benedict Wong, Jovan Adepo",       // 15%
  "production_company": "Plan B Entertainment", // 10%
  "logline": "Humanity's first contact...",     // +10%
  "description": "Based on Liu Cixin's...",     // +10%
  "episode_count": 8                            // +5%
}
```
**Score: 110%** → ⭐ Exceptional - Showcase example

---

**Document Version:** 1.0  
**Last Updated:** October 31, 2025  
**Maintained By:** Manus AI

