"""
Recent Mandates Module - Pinecone Version
Surfaces breaking news and recent intelligence from Pinecone vector database
Replaces Neo4j queries with Pinecone namespace queries
"""

from pinecone import Pinecone
from datetime import datetime, timedelta
import json
import os

class RecentMandatesTrackerPinecone:
    def __init__(self, pinecone_api_key, pinecone_index_name):
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(pinecone_index_name)
        self.dimension = 384  # Embedding dimension for this index
    
    def _create_dummy_vector(self):
        """Create a dummy query vector for fetching recent records"""
        return [0.0] * self.dimension
    
    def get_recent_greenlights(self, days=30, limit=100):
        """
        Get most recent greenlights from Pinecone
        Queries BOTH 'greenlights' and '(default)' namespaces
        Returns ALL metadata fields including streamer, status, etc.
        """
        dummy_vector = self._create_dummy_vector()
        all_greenlights = []
        
        # Query "greenlights" namespace
        # Query MORE than requested limit to get better coverage
        try:
            query_limit = max(limit * 5, 200)  # Query 5x the limit or 200
            results_greenlights = self.index.query(
                vector=dummy_vector,
                top_k=query_limit,
                include_metadata=True,
                namespace="greenlights"
            )
            
            for match in results_greenlights.matches:
                metadata = match.metadata
                if metadata.get("type") == "greenlight":
                    all_greenlights.append(metadata)
        except Exception as e:
            print(f"Error querying greenlights namespace: {e}")
        
        # Query "(default)" namespace for additional greenlights
        try:
            results_default = self.index.query(
                vector=dummy_vector,
                top_k=query_limit,
                include_metadata=True,
                namespace=""  # Empty string for default namespace
            )
            
            for match in results_default.matches:
                metadata = match.metadata
                if metadata.get("type") == "greenlight":
                    all_greenlights.append(metadata)
        except Exception as e:
            print(f"Error querying default namespace: {e}")
        
        # Remove duplicates (by title)
        seen_titles = set()
        unique_greenlights = []
        for greenlight in all_greenlights:
            title = greenlight.get("title", "")
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_greenlights.append(greenlight)
        
        # Sort by greenlight_date (most recent first)
        unique_greenlights.sort(
            key=lambda x: x.get("greenlight_date", x.get("date", "1900-01-01")),
            reverse=True
        )
        
        # Format for API response
        formatted_greenlights = []
        for g in unique_greenlights[:limit]:
            formatted_greenlights.append({
                'title': g.get('title', 'Unknown'),
                'streamer': g.get('streamer', ''),  # ← NOW POPULATED!
                'genre': g.get('genre', 'Unknown'),
                'format': g.get('format', 'Unknown'),
                'year': g.get('year', 'Unknown'),
                'greenlight_date': g.get('greenlight_date', g.get('date', 'Unknown')),
                'status': g.get('status', ''),
                'description': g.get('description', ''),
                'logline': g.get('logline', ''),
                'executive': g.get('executive', ''),
                'production_company': g.get('production_company', ''),
                'talent': g.get('talent', ''),
                'showrunner': g.get('showrunner', ''),
                'creator': g.get('creator', ''),
                'is_limited_series': g.get('is_limited_series', False),
                'type': 'greenlight'
            })
        
        return formatted_greenlights
    
    def get_recent_quotes(self, limit=100):
        """
        Get most recent executive quotes from Pinecone
        Queries 'quotes' namespace
        Returns ALL metadata fields including executive, quote text, streamer, title
        """
        dummy_vector = self._create_dummy_vector()
        
        # Query "quotes" namespace
        # Query MORE than requested limit to ensure we get quotes with executive attribution
        # (dummy vector queries return semi-random results)
        try:
            query_limit = max(limit * 10, 200)  # Query 10x the limit or 200, whichever is larger
            results = self.index.query(
                vector=dummy_vector,
                top_k=query_limit,
                include_metadata=True,
                namespace="quotes"
            )
            
            quotes = []
            for match in results.matches:
                metadata = match.metadata
                # Filter for actual quotes (not other content types)
                if metadata.get("content_type") == "quote" or metadata.get("type") == "quote":
                    quotes.append(metadata)
            
            # Sort by date (most recent first)
            quotes.sort(
                key=lambda x: x.get("date", "1900-01-01"),
                reverse=True
            )
            
            # Format for API response
            formatted_quotes = []
            for q in quotes[:limit]:
                formatted_quotes.append({
                    'executive': q.get('executive', ''),  # ← NOW POPULATED!
                    'title': q.get('title', ''),  # Executive title
                    'quote': q.get('quote', q.get('text', '')),  # ← NOW POPULATED!
                    'context': q.get('context', ''),
                    'date': q.get('date', 'Unknown'),
                    'source': q.get('source', 'Unknown'),
                    'streamer': q.get('streamer', ''),  # ← NOW POPULATED!
                    'topic': q.get('topic', ''),
                    'category': q.get('category', ''),
                    'content_type': q.get('content_type', 'quote'),
                    'type': 'quote'
                })
            
            return formatted_quotes
            
        except Exception as e:
            print(f"Error querying quotes namespace: {e}")
            return []
    
    def get_recent_deals(self, limit=100):
        """
        Get most recent production company deals from Pinecone
        Queries 'production_companies' and '(default)' namespaces
        """
        dummy_vector = self._create_dummy_vector()
        all_deals = []
        
        # Query "production_companies" namespace
        # Query MORE than requested limit
        try:
            query_limit = max(limit * 5, 100)
            results_pc = self.index.query(
                vector=dummy_vector,
                top_k=query_limit,
                include_metadata=True,
                namespace="production_companies"
            )
            
            for match in results_pc.matches:
                metadata = match.metadata
                if metadata.get("type") == "production_company":
                    all_deals.append(metadata)
        except Exception as e:
            print(f"Error querying production_companies namespace: {e}")
        
        # Query "(default)" namespace for deals
        try:
            results_default = self.index.query(
                vector=dummy_vector,
                top_k=query_limit,
                include_metadata=True,
                namespace=""
            )
            
            for match in results_default.matches:
                metadata = match.metadata
                deal_types = ["deal", "production_deal", "overall_deal_major"]
                if metadata.get("type") in deal_types:
                    all_deals.append(metadata)
        except Exception as e:
            print(f"Error querying default namespace for deals: {e}")
        
        # Remove duplicates
        seen = set()
        unique_deals = []
        for deal in all_deals:
            key = (deal.get("name", ""), deal.get("company", ""), deal.get("streamer", ""))
            if key not in seen:
                seen.add(key)
                unique_deals.append(deal)
        
        # Format for API response
        formatted_deals = []
        for d in unique_deals[:limit]:
            formatted_deals.append({
                'name': d.get('name', 'Unknown'),
                'company': d.get('company', d.get('name', 'Unknown')),
                'deal_type': d.get('deal_type', 'Unknown'),
                'deal_value': d.get('deal_value', ''),
                'year': d.get('year', 'Unknown'),
                'genre_focus': d.get('genre_focus', ''),
                'notable_projects': d.get('notable_projects', d.get('notes', '')),
                'streamer': d.get('streamer', ''),  # ← NOW POPULATED!
                'executives': d.get('executives', ''),
                'notes': d.get('notes', ''),
                'type': 'deal'
            })
        
        return formatted_deals
    
    def get_trending_executives(self, limit=5):
        """
        Get executives with most recent activity
        Queries 'executives' namespace
        """
        dummy_vector = self._create_dummy_vector()
        
        try:
            results = self.index.query(
                vector=dummy_vector,
                top_k=50,  # Get more to analyze
                include_metadata=True,
                namespace="executives"
            )
            
            # Count greenlights per executive
            exec_counts = {}
            for match in results.matches:
                metadata = match.metadata
                exec_name = metadata.get("executive_name", metadata.get("executive", ""))
                if exec_name:
                    if exec_name not in exec_counts:
                        exec_counts[exec_name] = {
                            'name': exec_name,
                            'title': metadata.get("title", metadata.get("previous_title", "")),
                            'count': 0
                        }
                    exec_counts[exec_name]['count'] += 1
            
            # Sort by count
            trending = sorted(exec_counts.values(), key=lambda x: x['count'], reverse=True)
            
            return [{
                'name': e['name'],
                'title': e['title'],
                'recent_greenlights': e['count'],
                'type': 'executive'
            } for e in trending[:limit]]
            
        except Exception as e:
            print(f"Error querying executives namespace: {e}")
            return []
    
    def get_hot_genres(self, limit=5):
        """
        Get trending genres based on recent greenlights
        """
        # Get recent greenlights
        greenlights = self.get_recent_greenlights(limit=200)
        
        # Count genres
        genre_counts = {}
        for g in greenlights:
            genre = g.get('genre', 'Unknown')
            if genre and genre != 'Unknown':
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort by count
        sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{
            'genre': genre,
            'greenlight_count': count,
            'type': 'genre_trend'
        } for genre, count in sorted_genres[:limit]]
    
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
            # Use streamer if available, otherwise default to Netflix
            streamer = gl.get('streamer', 'Netflix')
            
            card = {
                'type': 'greenlight',
                'title': gl['title'],
                'subtitle': f"{gl['format']} • {gl['genre']}",
                'description': gl.get('description') or gl.get('logline') or f"{streamer} greenlights {gl['format'].lower()} from {gl.get('production_company') or 'undisclosed prodco'}",
                'metadata': {
                    'streamer': streamer,  # ← NOW INCLUDED!
                    'executive': gl.get('executive', ''),
                    'talent': gl.get('talent', ''),
                    'year': gl.get('year', '')
                },
                'date': gl.get('greenlight_date', gl.get('date', '1900-01-01')),
                'icon': '🎬',
                'color': 'green'
            }
            cards.append(card)
        
        # Quote cards
        for quote in recent_quotes:
            # Handle executive name
            executive_name = quote.get('executive') or 'Industry Executive'
            
            # Handle quote text
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
                    'streamer': quote.get('streamer', ''),  # ← NOW INCLUDED!
                    'title': quote.get('title', ''),  # Executive title
                    'context': quote.get('context', 'N/A'),
                    'source': quote.get('source', 'Unknown')
                },
                'date': quote.get('date', '1900-01-01'),
                'icon': '💬',
                'color': 'blue'
            }
            cards.append(card)
        
        # Deal cards
        for deal in recent_deals:
            streamer = deal.get('streamer', 'Netflix')
            
            card = {
                'type': 'deal',
                'title': deal['name'],
                'subtitle': f"{deal['deal_type']} • {deal.get('year', 'Unknown')}",
                'description': f"{deal.get('company') or deal['name']} signs {deal['deal_type'].lower()} with {streamer} for {deal.get('genre_focus') or 'multiple genres'}",
                'metadata': {
                    'streamer': streamer,  # ← NOW INCLUDED!
                    'notable_projects': deal.get('notable_projects', ''),
                    'deal_value': deal.get('deal_value', '')
                },
                'date': deal.get('year', '1900'),
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

