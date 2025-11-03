"""
Recent Mandates Module - Pinecone Version with Filtering, Caching, and Pagination
Surfaces breaking news and recent intelligence from Pinecone vector database
Enhanced with filtering, caching, and pagination for optimal performance
"""

from pinecone import Pinecone
from datetime import datetime, timedelta
import json
import os
from query_cache import query_cache

class RecentMandatesTrackerPinecone:
    def __init__(self, pinecone_api_key, pinecone_index_name):
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(pinecone_index_name)
        self.dimension = 384  # Embedding dimension for this index
    
    def _create_dummy_vector(self):
        """Create a dummy query vector for fetching recent records"""
        return [0.0] * self.dimension
    
    def _apply_filters(self, items, filters):
        """
        Apply filters to a list of items
        
        Args:
            items: List of dictionaries to filter
            filters: Dict with filter criteria
                - platform: str or list of platforms
                - genre: str or list of genres
                - year: str or int
                - executive: str (partial match)
                - format: str (Series, Limited Series, Film)
        
        Returns:
            Filtered list of items
        """
        if not filters:
            return items
        
        filtered = items
        
        # Platform filter
        if filters.get('platform'):
            platforms = filters['platform'] if isinstance(filters['platform'], list) else [filters['platform']]
            filtered = [item for item in filtered if item.get('streamer', '').lower() in [p.lower() for p in platforms]]
        
        # Genre filter
        if filters.get('genre'):
            genres = filters['genre'] if isinstance(filters['genre'], list) else [filters['genre']]
            filtered = [item for item in filtered if any(g.lower() in item.get('genre', '').lower() for g in genres)]
        
        # Year filter
        if filters.get('year'):
            year_str = str(filters['year'])
            filtered = [item for item in filtered if year_str in str(item.get('year', ''))]
        
        # Executive filter (partial match)
        if filters.get('executive'):
            exec_name = filters['executive'].lower()
            filtered = [item for item in filtered if exec_name in item.get('executive', '').lower()]
        
        # Format filter
        if filters.get('format'):
            format_val = filters['format'].lower()
            filtered = [item for item in filtered if format_val in item.get('format', '').lower()]
        
        return filtered
    
    def _apply_pagination(self, items, offset=0, limit=100):
        """
        Apply pagination to results
        
        Args:
            items: List of items to paginate
            offset: Starting index (default: 0)
            limit: Maximum number of results (default: 100)
        
        Returns:
            Tuple of (paginated_items, pagination_info)
        """
        total = len(items)
        start = offset
        end = min(offset + limit, total)
        
        paginated = items[start:end]
        
        pagination_info = {
            'total': total,
            'offset': offset,
            'limit': limit,
            'returned': len(paginated),
            'has_more': end < total,
            'next_offset': end if end < total else None
        }
        
        return paginated, pagination_info
    
    def _fetch_greenlights_from_pinecone(self, query_limit=300):
        """
        Fetch greenlights from Pinecone (cached)
        This method is cached to avoid repeated Pinecone queries
        """
        dummy_vector = self._create_dummy_vector()
        all_greenlights = []
        
        # Query "greenlights" namespace
        try:
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
        
        return unique_greenlights
    
    def get_recent_greenlights(self, days=30, limit=100, filters=None, offset=0):
        """
        Get most recent greenlights from Pinecone with optional filtering and pagination
        
        Args:
            days: Number of days to look back (not strictly enforced due to Pinecone limitations)
            limit: Maximum number of results to return per page
            filters: Dict with filter criteria (platform, genre, year, executive, format)
            offset: Starting index for pagination (default: 0)
        
        Returns:
            Tuple of (formatted_greenlights, pagination_info)
        """
        # Fetch from cache or Pinecone
        unique_greenlights = self._fetch_greenlights_from_pinecone(query_limit=300)
        
        # Format for API response
        formatted_greenlights = []
        for g in unique_greenlights:
            formatted_greenlights.append({
                'title': g.get('title', 'Unknown'),
                'streamer': g.get('streamer', ''),
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
        
        # Apply filters
        if filters:
            formatted_greenlights = self._apply_filters(formatted_greenlights, filters)
        
        # Apply pagination
        paginated_results, pagination_info = self._apply_pagination(formatted_greenlights, offset, limit)
        
        return paginated_results, pagination_info
    
    def _fetch_quotes_from_pinecone(self, query_limit=300):
        """
        Fetch quotes from Pinecone (cached)
        This method is cached to avoid repeated Pinecone queries
        """
        dummy_vector = self._create_dummy_vector()
        
        try:
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
            
            return quotes
            
        except Exception as e:
            print(f"Error querying quotes namespace: {e}")
            return []
    
    def get_recent_quotes(self, limit=100, filters=None, offset=0):
        """
        Get most recent executive quotes from Pinecone with optional filtering and pagination
        
        Args:
            limit: Maximum number of results to return per page
            filters: Dict with filter criteria (platform, executive)
            offset: Starting index for pagination (default: 0)
        
        Returns:
            Tuple of (formatted_quotes, pagination_info)
        """
        # Fetch from cache or Pinecone
        quotes = self._fetch_quotes_from_pinecone(query_limit=300)
        
        # Format for API response
        formatted_quotes = []
        for q in quotes:
            formatted_quotes.append({
                'executive': q.get('executive', ''),
                'title': q.get('title', ''),  # Executive title
                'quote': q.get('quote', q.get('text', '')),
                'context': q.get('context', ''),
                'date': q.get('date', 'Unknown'),
                'source': q.get('source', 'Unknown'),
                'streamer': q.get('streamer', ''),
                'topic': q.get('topic', ''),
                'category': q.get('category', ''),
                'content_type': q.get('content_type', 'quote'),
                'type': 'quote'
            })
        
        # Apply filters
        if filters:
            formatted_quotes = self._apply_filters(formatted_quotes, filters)
        
        # Apply pagination
        paginated_results, pagination_info = self._apply_pagination(formatted_quotes, offset, limit)
        
        return paginated_results, pagination_info
    
    def _fetch_deals_from_pinecone(self, query_limit=200):
        """
        Fetch deals from Pinecone (cached)
        This method is cached to avoid repeated Pinecone queries
        """
        dummy_vector = self._create_dummy_vector()
        all_deals = []
        
        # Query "production_companies" namespace
        try:
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
        
        return unique_deals
    
    def get_recent_deals(self, limit=100, filters=None, offset=0):
        """
        Get most recent production company deals from Pinecone with optional filtering and pagination
        
        Args:
            limit: Maximum number of results to return per page
            filters: Dict with filter criteria (platform, year)
            offset: Starting index for pagination (default: 0)
        
        Returns:
            Tuple of (formatted_deals, pagination_info)
        """
        # Fetch from cache or Pinecone
        unique_deals = self._fetch_deals_from_pinecone(query_limit=200)
        
        # Format for API response
        formatted_deals = []
        for d in unique_deals:
            formatted_deals.append({
                'name': d.get('name', 'Unknown'),
                'company': d.get('company', d.get('name', 'Unknown')),
                'deal_type': d.get('deal_type', 'Unknown'),
                'deal_value': d.get('deal_value', ''),
                'year': d.get('year', 'Unknown'),
                'genre_focus': d.get('genre_focus', ''),
                'notable_projects': d.get('notable_projects', d.get('notes', '')),
                'streamer': d.get('streamer', ''),
                'executives': d.get('executives', ''),
                'notes': d.get('notes', ''),
                'type': 'deal'
            })
        
        # Apply filters
        if filters:
            formatted_deals = self._apply_filters(formatted_deals, filters)
        
        # Apply pagination
        paginated_results, pagination_info = self._apply_pagination(formatted_deals, offset, limit)
        
        return paginated_results, pagination_info
    
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
        # Get all recent greenlights (from cache)
        greenlights, _ = self.get_recent_greenlights(limit=200)
        
        # Count genres
        genre_counts = {}
        for g in greenlights:
            genre = g.get('genre', 'Unknown')
            if genre and genre != 'Unknown':
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        # Sort by count
        hot_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [{
            'genre': genre,
            'count': count,
            'type': 'genre'
        } for genre, count in hot_genres[:limit]]



    def get_landing_page_cards(self, limit=12):
        """
        Get mixed recent intelligence for landing page cards
        Returns a mix of greenlights, quotes, and deals
        
        Args:
            limit: Total number of cards to return (default: 12)
        
        Returns:
            Dict with 'cards' list containing mixed mandate types
        """
        try:
            # Get 4 of each type for a balanced mix
            cards_per_type = limit // 3
            
            # Fetch greenlights (unpack tuple)
            greenlights, _ = self.get_recent_greenlights(limit=cards_per_type)
            
            # Fetch quotes (unpack tuple)
            quotes, _ = self.get_recent_quotes(limit=cards_per_type)
            
            # Fetch deals (unpack tuple)
            deals, _ = self.get_recent_deals(limit=cards_per_type)
            
            # Combine and format as cards
            all_cards = []
            
            # Add greenlights as cards
            for gl in greenlights:
                metadata = {}
                if gl.get('streamer'):
                    metadata['Platform'] = gl.get('streamer')
                if gl.get('genre'):
                    metadata['Genre'] = gl.get('genre')
                if gl.get('format'):
                    metadata['Format'] = gl.get('format')
                if gl.get('executive'):
                    metadata['Executive'] = gl.get('executive')
                if gl.get('production_company'):
                    metadata['Production'] = gl.get('production_company')
                
                all_cards.append({
                    'type': 'greenlight',
                    'title': gl.get('title', 'Untitled'),
                    'description': gl.get('description', gl.get('logline', 'New greenlight announcement')),
                    'metadata': metadata,
                    'date': gl.get('greenlight_date', gl.get('date', '')),
                    'icon': '🎬',
                    'color': 'green',
                })
            
            # Add quotes as cards
            for quote in quotes:
                metadata = {}
                if quote.get('executive'):
                    metadata['Executive'] = quote.get('executive')
                if quote.get('streamer'):
                    metadata['Platform'] = quote.get('streamer')
                if quote.get('title'):
                    metadata['Title'] = quote.get('title')
                
                quote_text = quote.get('quote', '')
                description = quote_text[:200] + '...' if len(quote_text) > 200 else quote_text
                
                all_cards.append({
                    'type': 'quote',
                    'title': f"Quote from {quote.get('executive', 'Executive')}",
                    'description': description or 'Executive statement',
                    'metadata': metadata,
                    'date': quote.get('date', ''),
                    'icon': '💬',
                    'color': 'blue',
                })
            
            # Add deals as cards
            for deal in deals:
                metadata = {}
                if deal.get('streamer'):
                    metadata['Platform'] = deal.get('streamer')
                if deal.get('production_company'):
                    metadata['Company'] = deal.get('production_company')
                if deal.get('deal_type'):
                    metadata['Type'] = deal.get('deal_type')
                
                all_cards.append({
                    'type': 'deal',
                    'title': deal.get('title', 'Production Deal'),
                    'description': deal.get('description', 'New production deal announcement'),
                    'metadata': metadata,
                    'date': deal.get('date', ''),
                    'icon': '🤝',
                    'color': 'purple',
                })
            
            # Sort all cards by date (most recent first)
            all_cards.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            # Return only the requested number of cards
            return {
                'cards': all_cards[:limit],
                'total': len(all_cards),
                'types': {
                    'greenlights': len(greenlights),
                    'quotes': len(quotes),
                    'deals': len(deals)
                }
            }
            
        except Exception as e:
            print(f"Error in get_landing_page_cards: {e}")
            return {
                'cards': [],
                'total': 0,
                'types': {'greenlights': 0, 'quotes': 0, 'deals': 0},
                'error': str(e)
            }

