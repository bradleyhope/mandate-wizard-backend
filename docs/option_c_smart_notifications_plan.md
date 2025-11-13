# Option C: Smart Notification System - Design & Implementation Plan

**Date:** November 12, 2025  
**Status:** Planning Phase  
**Foundation:** Pro Architecture + Automated Updates + Analytics Dashboard

---

## Executive Summary

Build an intelligent notification system that:
1. **Alerts when entities become critical** - Proactive monitoring
2. **Notifies about trending topics** - Stay ahead of trends
3. **Reports update completion** - Track automated updates
4. **Sends personalized insights** - Tailored to user interests
5. **Delivers daily/weekly digests** - Summarized intelligence

**Goal:** Keep users informed without overwhelming them with **smart, contextual notifications**.

---

## Notification Architecture

```
┌──────────────────────────────────────────────────────────┐
│              NOTIFICATION TRIGGERS                        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Critical   │  │  Trending   │  │   Update    │     │
│  │   Entity    │  │   Topics    │  │  Complete   │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
│         │                 │                 │             │
└─────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │
          ↓                 ↓                 ↓
┌──────────────────────────────────────────────────────────┐
│           NOTIFICATION ENGINE                             │
│                                                           │
│  ┌────────────────────────────────────────────────┐     │
│  │  Event Detection & Filtering                   │     │
│  │  - Deduplicate events                          │     │
│  │  - Apply user preferences                      │     │
│  │  - Rate limiting                               │     │
│  └────────────────────────────────────────────────┘     │
│                                                           │
│  ┌────────────────────────────────────────────────┐     │
│  │  Personalization Engine                        │     │
│  │  - User interest matching                      │     │
│  │  - Relevance scoring                           │     │
│  │  - Content customization                       │     │
│  └────────────────────────────────────────────────┘     │
│                                                           │
│  ┌────────────────────────────────────────────────┐     │
│  │  Delivery Manager                              │     │
│  │  - Channel selection (email, webhook, in-app)  │     │
│  │  - Template rendering                          │     │
│  │  - Delivery scheduling                         │     │
│  └────────────────────────────────────────────────┘     │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ↓
┌──────────────────────────────────────────────────────────┐
│              DELIVERY CHANNELS                            │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Email     │  │   Webhook    │  │   In-App     │  │
│  │  (SendGrid)  │  │   (Slack)    │  │  (Browser)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Notification Types

### 1. Critical Entity Alerts

**Trigger:** Entity becomes critical (high demand + stale data)

**Purpose:** Alert admins to update high-priority entities

**Example:**
```
Subject: 🚨 Critical Entity Alert: Chris Mansolillo

Entity: Chris Mansolillo (Person)
Status: CRITICAL
Reason: High demand (score: 45) + Stale data (last updated: 62 days ago)

Action Required:
- Update entity data from newsletters
- Verify current position/projects
- Refresh relationships

[Update Now] [View Details] [Snooze 24h]

---
Mandate Wizard Analytics
```

**Frequency:** Immediate (real-time)

**Channels:** Email, Slack webhook

---

### 2. Trending Topic Notifications

**Trigger:** Entity shows significant query spike

**Purpose:** Inform users about emerging trends

**Example:**
```
Subject: 🔥 Trending Now: Netflix

Netflix is trending!
↑ 320% increase in queries (last 24 hours)

Why it's trending:
- Quarterly earnings report released
- New show announcement
- 98 user queries today

Related Entities:
- Ted Sarandos (CEO)
- Stranger Things (Show)
- Reed Hastings (Co-founder)

[View Trending Dashboard] [Learn More]

---
Mandate Wizard Analytics
```

**Frequency:** Hourly digest (batched)

**Channels:** Email, In-app notification

---

### 3. Update Completion Reports

**Trigger:** Automated update completes

**Purpose:** Track automated update success/failure

**Example:**
```
Subject: ✅ Daily Update Report - 45 entities updated

Update Summary (Nov 12, 2025)

Successful: 43 entities (96%)
Failed: 2 entities (4%)

Top Updates:
1. Chris Mansolillo - New project added
2. Netflix - Quarterly results updated
3. HBO Max - Leadership change

Failed Updates:
1. Jane Doe - No recent mentions found
2. ABC Studios - Scraping error

[View Full Report] [Retry Failed]

---
Mandate Wizard Automation
```

**Frequency:** Daily digest

**Channels:** Email

---

### 4. Personalized Insights

**Trigger:** User-specific patterns detected

**Purpose:** Provide tailored intelligence based on user interests

**Example:**
```
Subject: 💡 Your Weekly Insights - Film Industry

Hi [User],

Based on your recent queries, here are this week's insights:

Entities You Follow:
- Chris Mansolillo: New project announced
- Netflix: Hiring for new positions
- Succession: Season finale trending

Recommended Entities:
- Jane Doe: Similar profile to your interests
- New Show XYZ: Related to your queries

Your Activity:
- 23 queries this week
- Top interest: Streaming executives
- Most active: Tuesday afternoons

[View Full Dashboard] [Update Preferences]

---
Mandate Wizard Insights
```

**Frequency:** Weekly digest

**Channels:** Email

---

### 5. System Health Alerts

**Trigger:** System performance degradation

**Purpose:** Alert admins to technical issues

**Example:**
```
Subject: ⚠️ System Alert: High Error Rate

Alert: API error rate elevated
Current: 5.2% (threshold: 1%)
Duration: 15 minutes

Affected Endpoints:
- /api/answer (3.2% errors)
- /api/priority/batch (8.1% errors)

Possible Causes:
- Database connection issues
- High query volume
- External API timeout

[View Logs] [Check Status Page]

---
Mandate Wizard Monitoring
```

**Frequency:** Immediate (real-time)

**Channels:** Email, Slack webhook

---

## User Preferences

### Notification Settings

Users can control:
- **Frequency:** Real-time, Hourly, Daily, Weekly
- **Channels:** Email, Webhook, In-app
- **Types:** Critical, Trending, Updates, Insights
- **Entities:** Follow specific entities
- **Quiet Hours:** No notifications during specified times

### Preference Schema

```json
{
  "user_id": "uuid",
  "preferences": {
    "critical_alerts": {
      "enabled": true,
      "channel": "email",
      "frequency": "realtime"
    },
    "trending_topics": {
      "enabled": true,
      "channel": "email",
      "frequency": "daily"
    },
    "update_reports": {
      "enabled": true,
      "channel": "email",
      "frequency": "daily"
    },
    "personalized_insights": {
      "enabled": true,
      "channel": "email",
      "frequency": "weekly"
    },
    "followed_entities": [
      "entity-uuid-1",
      "entity-uuid-2"
    ],
    "quiet_hours": {
      "enabled": true,
      "start": "22:00",
      "end": "08:00",
      "timezone": "America/Los_Angeles"
    }
  }
}
```

---

## Technical Implementation

### Backend Components

**File Structure:**
```
pro_architecture/
├── notifications/
│   ├── __init__.py
│   ├── notification_engine.py
│   ├── triggers/
│   │   ├── critical_entity_trigger.py
│   │   ├── trending_trigger.py
│   │   ├── update_complete_trigger.py
│   │   └── __init__.py
│   ├── channels/
│   │   ├── email_channel.py
│   │   ├── webhook_channel.py
│   │   ├── inapp_channel.py
│   │   └── __init__.py
│   ├── templates/
│   │   ├── critical_entity.html
│   │   ├── trending_topic.html
│   │   ├── update_report.html
│   │   └── personalized_insights.html
│   └── preferences.py
```

### Notification Engine

**File:** `pro_architecture/notifications/notification_engine.py`

```python
class NotificationEngine:
    """
    Central notification engine.
    
    Responsibilities:
    - Detect events
    - Filter by user preferences
    - Personalize content
    - Deliver via appropriate channels
    """
    
    def __init__(self):
        self.triggers = [
            CriticalEntityTrigger(),
            TrendingTrigger(),
            UpdateCompleteTrigger()
        ]
        self.channels = {
            'email': EmailChannel(),
            'webhook': WebhookChannel(),
            'inapp': InAppChannel()
        }
        self.preference_manager = PreferenceManager()
    
    def check_triggers(self):
        """Check all triggers for events"""
        events = []
        for trigger in self.triggers:
            events.extend(trigger.check())
        return events
    
    def process_event(self, event: Dict):
        """Process a single event"""
        # Get affected users
        users = self.get_affected_users(event)
        
        for user in users:
            # Check user preferences
            prefs = self.preference_manager.get(user['id'])
            
            if self.should_notify(event, prefs):
                # Personalize content
                content = self.personalize(event, user)
                
                # Deliver via preferred channel
                channel = self.channels[prefs['channel']]
                channel.send(user, content)
    
    def should_notify(self, event: Dict, prefs: Dict) -> bool:
        """Check if user should be notified"""
        # Check if notification type is enabled
        if not prefs.get(event['type'], {}).get('enabled', False):
            return False
        
        # Check quiet hours
        if self.in_quiet_hours(prefs):
            return False
        
        # Check rate limits
        if self.rate_limited(event['user_id'], event['type']):
            return False
        
        return True
    
    def personalize(self, event: Dict, user: Dict) -> Dict:
        """Personalize notification content"""
        # Add user-specific context
        # Customize based on user interests
        # Format for user's preferred style
        pass
```

### Email Channel

**File:** `pro_architecture/notifications/channels/email_channel.py`

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

class EmailChannel:
    """
    Email notification channel using SendGrid.
    """
    
    def __init__(self):
        self.client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = 'notifications@mandatewizard.com'
    
    def send(self, user: Dict, content: Dict):
        """Send email notification"""
        message = Mail(
            from_email=self.from_email,
            to_emails=user['email'],
            subject=content['subject'],
            html_content=content['html']
        )
        
        try:
            response = self.client.send(message)
            self.log_delivery(user['id'], 'email', 'success')
        except Exception as e:
            self.log_delivery(user['id'], 'email', 'failed', str(e))
```

### Webhook Channel

**File:** `pro_architecture/notifications/channels/webhook_channel.py`

```python
import requests

class WebhookChannel:
    """
    Webhook notification channel (Slack, Discord, etc.)
    """
    
    def send(self, user: Dict, content: Dict):
        """Send webhook notification"""
        webhook_url = user.get('webhook_url')
        
        if not webhook_url:
            return
        
        # Format for Slack
        payload = {
            'text': content['title'],
            'blocks': [
                {
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': content['message']
                    }
                }
            ]
        }
        
        try:
            response = requests.post(webhook_url, json=payload)
            self.log_delivery(user['id'], 'webhook', 'success')
        except Exception as e:
            self.log_delivery(user['id'], 'webhook', 'failed', str(e))
```

### Critical Entity Trigger

**File:** `pro_architecture/notifications/triggers/critical_entity_trigger.py`

```python
class CriticalEntityTrigger:
    """
    Triggers notifications for critical entities.
    """
    
    def check(self) -> List[Dict]:
        """Check for critical entities"""
        # Call /api/priority/critical
        response = requests.get(
            'http://localhost:5000/api/priority/critical'
        )
        
        critical_entities = response.json()['critical_entities']
        
        events = []
        for entity in critical_entities:
            # Check if already notified recently
            if not self.recently_notified(entity['id']):
                events.append({
                    'type': 'critical_entity',
                    'entity_id': entity['id'],
                    'entity_name': entity['name'],
                    'demand_score': entity['demand_score'],
                    'days_since_update': entity.get('days_since_update', 0),
                    'priority_score': entity['priority_score']
                })
        
        return events
```

---

## API Endpoints

### Notification Preferences

```http
# Get user preferences
GET /api/notifications/preferences

# Update user preferences
PUT /api/notifications/preferences
{
  "critical_alerts": {
    "enabled": true,
    "channel": "email",
    "frequency": "realtime"
  }
}

# Follow entity
POST /api/notifications/follow
{
  "entity_id": "uuid"
}

# Unfollow entity
DELETE /api/notifications/follow/{entity_id}
```

### Notification History

```http
# Get notification history
GET /api/notifications/history?limit=50

# Mark as read
PUT /api/notifications/{notification_id}/read

# Delete notification
DELETE /api/notifications/{notification_id}
```

---

## Database Schema

### Notifications Table

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    entity_id UUID,
    metadata JSONB,
    channel VARCHAR(20),
    status VARCHAR(20),
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
```

### User Preferences Table

```sql
CREATE TABLE notification_preferences (
    user_id VARCHAR(255) PRIMARY KEY,
    preferences JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Followed Entities Table

```sql
CREATE TABLE followed_entities (
    user_id VARCHAR(255) NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, entity_id)
);

CREATE INDEX idx_followed_user ON followed_entities(user_id);
CREATE INDEX idx_followed_entity ON followed_entities(entity_id);
```

---

## Implementation Phases

### Phase 1: Core Notifications (Week 1-2)

**Goal:** Basic notification system with email

**Tasks:**
1. Build notification engine
2. Implement email channel (SendGrid)
3. Create critical entity trigger
4. Build email templates
5. Test with admins

**Deliverables:**
- Email notifications working
- Critical entity alerts
- Basic templates

### Phase 2: User Preferences (Week 3-4)

**Goal:** User-controlled notifications

**Tasks:**
1. Build preference management
2. Create preference UI
3. Implement quiet hours
4. Add entity following
5. Build notification history

**Deliverables:**
- User preference system
- Notification history
- Follow/unfollow entities

### Phase 3: Advanced Features (Week 5-6)

**Goal:** Trending, updates, and personalization

**Tasks:**
1. Implement trending trigger
2. Build update completion reports
3. Add personalized insights
4. Implement webhook channel
5. Create digest emails

**Deliverables:**
- All notification types
- Multiple channels
- Personalized content

### Phase 4: Intelligence & Optimization (Week 7-8)

**Goal:** Smart, ML-powered notifications

**Tasks:**
1. Implement relevance scoring
2. Add ML-based personalization
3. Optimize delivery timing
4. A/B test templates
5. Performance tuning

**Deliverables:**
- Intelligent notifications
- Optimized delivery
- High engagement rates

---

## Cost Estimate

### Infrastructure

| Component | Platform | Cost |
|-----------|----------|------|
| Email Service | SendGrid | $15/mo (40k emails) |
| Notification Engine | Render (existing) | $0 |
| Database (existing) | Render | $0 |
| **TOTAL** | | **$15/mo** |

### Email Volume Estimate

| Notification Type | Frequency | Volume/Month |
|-------------------|-----------|--------------|
| Critical Alerts | Real-time | ~500 |
| Trending Topics | Daily | ~3,000 |
| Update Reports | Daily | ~3,000 |
| Personalized Insights | Weekly | ~500 |
| **TOTAL** | | **~7,000** |

**Note:** Well within SendGrid free tier (100 emails/day = 3,000/month) initially.

---

## Success Metrics

### Engagement Metrics

- **Open Rate:** > 40%
- **Click Rate:** > 15%
- **Unsubscribe Rate:** < 2%

### Performance Metrics

- **Delivery Time:** < 1 minute
- **Delivery Success:** > 99%
- **False Positives:** < 5%

### Business Metrics

- **User Retention:** +20%
- **Active Users:** +30%
- **User Satisfaction:** > 85%

---

## Best Practices

### 1. Don't Overwhelm Users

- Batch similar notifications
- Respect quiet hours
- Allow granular control
- Provide easy unsubscribe

### 2. Make Notifications Actionable

- Clear call-to-action
- Direct links to relevant pages
- One-click actions when possible

### 3. Personalize Content

- Use user's name
- Reference their interests
- Tailor frequency to engagement

### 4. Test and Optimize

- A/B test subject lines
- Optimize send times
- Track engagement metrics
- Iterate based on data

---

## Next Steps

1. **Review notification designs** - Feedback on templates
2. **Choose email provider** - SendGrid, Mailgun, or AWS SES?
3. **Set up SendGrid account** - API keys and domains
4. **Prioritize notification types** - Which to build first?
5. **Start Phase 1** - Build core notification engine

---

## Conclusion

The Smart Notification System will keep users informed with:
- ✅ Timely alerts for critical entities
- ✅ Trending topic notifications
- ✅ Automated update reports
- ✅ Personalized insights
- ✅ Intelligent delivery

**Key Benefits:**
- Keep users engaged
- Proactive monitoring
- Reduced manual work
- Better user experience
- Data-driven insights

**Ready to implement?**
