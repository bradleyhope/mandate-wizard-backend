"""
Recent Mandates Module
Surfaces breaking news and recent intelligence for landing page cards
"""

from neo4j import GraphDatabase
from datetime import datetime, timedelta
import json

class RecentMandatesTracker:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        self.driver.close()
    
    def get_recent_greenlights(self, days=30, limit=10):
        """Get most recent greenlights"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.greenlight_date IS NOT NULL
                RETURN g.title as title, g.genre as genre, g.format as format,
                       g.year as year, g.executive as executive,
                       g.talent_attached as talent, g.production_company as production_company,
                       g.greenlight_date as date, g.description as description
                ORDER BY g.greenlight_date DESC
                LIMIT $limit
            """, limit=limit)
            
            greenlights = []
            for record in result:
                greenlights.append({
                    'title': record['title'],
                    'genre': record['genre'],
                    'format': record['format'],
                    'year': record['year'],
                    'executive': record['executive'],
                    'talent': record['talent'],
                    'production_company': record['production_company'],
                    'date': record['date'],
                    'description': record['description'],
                    'type': 'greenlight'
                })
            
            return greenlights
    
    def get_recent_quotes(self, limit=10):
        """Get most recent executive quotes"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (q:Quote)
                WHERE q.date IS NOT NULL
                  AND q.context IS NOT NULL
                  AND size(q.context) > 20
                RETURN q.person_name as executive, q.quote as quote,
                       q.context as context, q.date as date, q.source as source,
                       q.topic as topic
                ORDER BY q.date DESC
                LIMIT $limit
            """, limit=limit)
            
            quotes = []
            for record in result:
                quotes.append({
                    'executive': record['executive'],
                    'quote': record['quote'],
                    'context': record['context'],
                    'date': record['date'],
                    'source': record['source'],
                    'topic': record['topic'],
                    'type': 'quote'
                })
            
            return quotes
    
    def get_recent_deals(self, limit=10):
        """Get most recent production company deals"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (pc:ProductionCompany)
                WHERE pc.deal_year IS NOT NULL
                  AND toInteger(pc.deal_year) >= 2024
                RETURN pc.name as name, pc.production_company as company,
                       pc.deal_type as deal_type, pc.deal_year as year,
                       pc.genre_focus as genre_focus, pc.notable_projects as projects
                ORDER BY pc.deal_year DESC
                LIMIT $limit
            """, limit=limit)
            
            deals = []
            for record in result:
                deals.append({
                    'name': record['name'],
                    'company': record['company'],
                    'deal_type': record['deal_type'],
                    'year': record['year'],
                    'genre_focus': record['genre_focus'],
                    'notable_projects': record['projects'],
                    'type': 'deal'
                })
            
            return deals
    
    def get_trending_executives(self, limit=5):
        """Get executives with most recent activity"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.executive IS NOT NULL
                  AND g.year IN ['2024', '2025']
                WITH g.executive as executive, count(*) as greenlight_count
                ORDER BY greenlight_count DESC
                LIMIT $limit
                MATCH (p:Person)
                WHERE toLower(p.name) = toLower(executive)
                RETURN p.name as name, p.title as title, greenlight_count
            """, limit=limit)
            
            executives = []
            for record in result:
                executives.append({
                    'name': record['name'],
                    'title': record['title'],
                    'recent_greenlights': record['greenlight_count'],
                    'type': 'executive'
                })
            
            return executives
    
    def get_hot_genres(self, limit=5):
        """Get trending genres based on recent greenlights"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.year IN ['2024', '2025']
                  AND g.genre IS NOT NULL
                RETURN g.genre as genre, count(*) as count
                ORDER BY count DESC
                LIMIT $limit
            """, limit=limit)
            
            genres = []
            for record in result:
                genres.append({
                    'genre': record['genre'],
                    'greenlight_count': record['count'],
                    'type': 'genre_trend'
                })
            
            return genres
    
    def get_landing_page_cards(self):
        """Get all recent intelligence for landing page cards"""
        
        # Get top 3 recent greenlights
        recent_greenlights = self.get_recent_greenlights(limit=3)
        
        # Get top 2 recent quotes
        recent_quotes = self.get_recent_quotes(limit=2)
        
        # Get top 2 recent deals
        recent_deals = self.get_recent_deals(limit=2)
        
        # Get trending executives
        trending_execs = self.get_trending_executives(limit=3)
        
        # Get hot genres
        hot_genres = self.get_hot_genres(limit=3)
        
        # Combine and format for cards
        cards = []
        
        # Greenlight cards
        for gl in recent_greenlights:
            card = {
                'type': 'greenlight',
                'title': gl['title'],
                'subtitle': f"{gl['format']} • {gl['genre']}",
                'description': gl['description'] or f"Netflix greenlights {gl['format'].lower()} from {gl['production_company'] or 'undisclosed prodco'}",
                'metadata': {
                    'executive': gl['executive'],
                    'talent': gl['talent'],
                    'year': gl['year']
                },
                'date': gl['date'],
                'icon': '🎬',
                'color': 'green'
            }
            cards.append(card)
        
        # Quote cards
        for quote in recent_quotes:
            # Handle null executive name
            executive_name = quote.get('executive') or 'Industry Executive'
            
            # Handle null quote - use context as fallback
            quote_text = quote.get('quote')
            if not quote_text or quote_text == 'None':
                # Use context as the quote if actual quote is missing
                quote_text = quote.get('context', 'No quote available')
            
            # Format description
            if len(quote_text) > 150:
                description = f'"{quote_text[:150]}..."'
            else:
                description = f'"{quote_text}"'
            
            card = {
                'type': 'quote',
                'title': executive_name,
                'subtitle': quote.get('topic') or 'Executive Statement',
                'description': description,
                'metadata': {
                    'context': quote.get('context', 'N/A'),
                    'source': quote.get('source', 'Unknown')
                },
                'date': quote['date'],
                'icon': '💬',
                'color': 'blue'
            }
            cards.append(card)
        
        # Deal cards
        for deal in recent_deals:
            card = {
                'type': 'deal',
                'title': deal['name'],
                'subtitle': f"{deal['deal_type']} • {deal['year']}",
                'description': f"{deal['company'] or deal['name']} signs {deal['deal_type'].lower()} with Netflix for {deal['genre_focus'] or 'multiple genres'}",
                'metadata': {
                    'notable_projects': deal['notable_projects']
                },
                'date': deal['year'],
                'icon': '🤝',
                'color': 'purple'
            }
            cards.append(card)
        
        # Sort all cards by date (most recent first)
        cards.sort(key=lambda x: x['date'] if x['date'] else '1900-01-01', reverse=True)
        
        return {
            'cards': cards[:8],  # Top 8 most recent
            'trending_executives': trending_execs,
            'hot_genres': hot_genres
        }
    
    def add_breaking_news(self, title, description, source, news_type='executive_move'):
        """Manually add breaking news (like Taylor Sheridan leaving Paramount)"""
        # This would be called by admin/automation when breaking news happens
        # For now, return a template for how breaking news cards should look
        
        breaking_news_card = {
            'type': 'breaking',
            'title': title,
            'subtitle': 'BREAKING NEWS',
            'description': description,
            'metadata': {
                'source': source,
                'news_type': news_type
            },
            'date': datetime.now().isoformat(),
            'icon': '🚨',
            'color': 'red'
        }
        
        return breaking_news_card

