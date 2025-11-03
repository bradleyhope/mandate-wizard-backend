"""
Pattern Analysis API for Mandate Wizard
Enables statistical queries, trend analysis, and pattern recognition
"""

from neo4j import GraphDatabase
from collections import Counter
import json
from datetime import datetime

class PatternAnalyzer:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        self.driver.close()
    
    # ========== GREENLIGHT QUERIES ==========
    
    def get_greenlights_by_year(self, year):
        """Get all greenlights for a specific year"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.year = $year
                RETURN g.title as title, g.genre as genre, g.format as format,
                       g.executive as executive, g.talent_attached as talent,
                       g.production_company as production_company
                ORDER BY g.greenlight_date DESC
            """, year=str(year))
            
            greenlights = []
            for record in result:
                greenlights.append(dict(record))
            
            return greenlights
    
    def get_limited_series_greenlights(self, year=None):
        """Get all limited series greenlights, optionally filtered by year"""
        with self.driver.session() as session:
            query = """
                MATCH (g:Greenlight)
                WHERE g.format CONTAINS 'Limited' OR g.format CONTAINS 'limited'
            """
            if year:
                query += " AND g.year = $year"
            query += """
                RETURN g.title as title, g.genre as genre, g.year as year,
                       g.executive as executive, g.talent_attached as talent,
                       g.production_company as production_company
                ORDER BY g.year DESC, g.greenlight_date DESC
            """
            
            result = session.run(query, year=str(year) if year else None)
            
            limited_series = []
            for record in result:
                limited_series.append(dict(record))
            
            return limited_series
    
    def get_greenlights_by_genre(self, genre):
        """Get all greenlights for a specific genre"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE toLower(g.genre) CONTAINS toLower($genre)
                RETURN g.title as title, g.genre as genre, g.year as year,
                       g.format as format, g.executive as executive,
                       g.talent_attached as talent, g.production_company as production_company
                ORDER BY g.year DESC
            """, genre=genre)
            
            greenlights = []
            for record in result:
                greenlights.append(dict(record))
            
            return greenlights
    
    # ========== EXECUTIVE ANALYSIS ==========
    
    def get_executive_greenlight_stats(self, executive_name):
        """Get greenlight statistics for a specific executive"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE toLower(g.executive) CONTAINS toLower($exec_name)
                RETURN g.genre as genre, g.format as format, g.year as year
            """, exec_name=executive_name)
            
            greenlights = list(result)
            
            if not greenlights:
                return None
            
            # Analyze patterns
            genres = [r['genre'] for r in greenlights if r['genre']]
            formats = [r['format'] for r in greenlights if r['format']]
            years = [r['year'] for r in greenlights if r['year']]
            
            genre_counts = Counter(genres)
            format_counts = Counter(formats)
            year_counts = Counter(years)
            
            return {
                'executive': executive_name,
                'total_greenlights': len(greenlights),
                'top_genres': dict(genre_counts.most_common(5)),
                'format_breakdown': dict(format_counts),
                'yearly_breakdown': dict(sorted(year_counts.items(), reverse=True)),
                'most_greenlit_genre': genre_counts.most_common(1)[0] if genre_counts else None
            }
    
    def get_executives_by_genre(self, genre):
        """Find which executives greenlight specific genres most"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE toLower(g.genre) CONTAINS toLower($genre)
                  AND g.executive IS NOT NULL
                RETURN g.executive as executive, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """, genre=genre)
            
            executives = []
            for record in result:
                executives.append({
                    'executive': record['executive'],
                    'greenlight_count': record['count']
                })
            
            return executives
    
    def get_international_content_executives(self):
        """Find executives who greenlight international content"""
        with self.driver.session() as session:
            # Look for non-English content indicators
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE (toLower(g.genre) CONTAINS 'korean' OR 
                       toLower(g.genre) CONTAINS 'spanish' OR
                       toLower(g.genre) CONTAINS 'international' OR
                       toLower(g.title) CONTAINS 'casa de' OR
                       toLower(g.title) CONTAINS 'squid' OR
                       toLower(g.production_company) CONTAINS 'korea' OR
                       toLower(g.production_company) CONTAINS 'spain')
                  AND g.executive IS NOT NULL
                RETURN g.executive as executive, 
                       collect(g.title) as titles,
                       count(*) as count
                ORDER BY count DESC
            """)
            
            executives = []
            for record in result:
                executives.append({
                    'executive': record['executive'],
                    'international_greenlights': record['count'],
                    'sample_titles': record['titles'][:5]
                })
            
            return executives
    
    # ========== TREND ANALYSIS ==========
    
    def get_genre_trends_by_year(self):
        """Analyze genre trends over years"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.year IS NOT NULL AND g.genre IS NOT NULL
                RETURN g.year as year, g.genre as genre, count(*) as count
                ORDER BY g.year DESC, count DESC
            """)
            
            trends = {}
            for record in result:
                year = record['year']
                if year not in trends:
                    trends[year] = []
                trends[year].append({
                    'genre': record['genre'],
                    'count': record['count']
                })
            
            return trends
    
    def get_ya_greenlights(self):
        """Get all YA (Young Adult) greenlights"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE toLower(g.genre) CONTAINS 'ya' OR 
                      toLower(g.genre) CONTAINS 'young adult' OR
                      toLower(g.genre) CONTAINS 'teen' OR
                      toLower(g.description) CONTAINS 'young adult' OR
                      toLower(g.description) CONTAINS 'teen'
                RETURN g.title as title, g.genre as genre, g.year as year,
                       g.format as format, g.talent_attached as talent,
                       g.production_company as production_company
                ORDER BY g.year DESC
            """)
            
            ya_greenlights = []
            for record in result:
                ya_greenlights.append(dict(record))
            
            return ya_greenlights
    
    def get_format_trends(self):
        """Analyze format trends (limited vs ongoing series)"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.format IS NOT NULL AND g.year IS NOT NULL
                RETURN g.year as year, g.format as format, count(*) as count
                ORDER BY g.year DESC
            """)
            
            trends = {}
            for record in result:
                year = record['year']
                if year not in trends:
                    trends[year] = {}
                trends[year][record['format']] = record['count']
            
            return trends
    
    # ========== PRODUCTION COMPANY ANALYSIS ==========
    
    def get_prodco_greenlight_rate(self, prodco_name):
        """Get greenlight statistics for a production company"""
        with self.driver.session() as session:
            # Get greenlights
            greenlight_result = session.run("""
                MATCH (g:Greenlight)
                WHERE toLower(g.production_company) CONTAINS toLower($prodco_name)
                RETURN g.title as title, g.genre as genre, g.year as year
            """, prodco_name=prodco_name)
            
            greenlights = list(greenlight_result)
            
            # Get production company info
            prodco_result = session.run("""
                MATCH (pc:ProductionCompany)
                WHERE toLower(pc.name) CONTAINS toLower($prodco_name)
                RETURN pc.greenlight_rate as rate, pc.specialization as specialization,
                       pc.genre_focus as genre_focus
                LIMIT 1
            """, prodco_name=prodco_name)
            
            prodco_info = prodco_result.single()
            
            return {
                'production_company': prodco_name,
                'total_greenlights': len(greenlights),
                'greenlight_rate': prodco_info['rate'] if prodco_info else 'Unknown',
                'specialization': prodco_info['specialization'] if prodco_info else None,
                'genre_focus': prodco_info['genre_focus'] if prodco_info else None,
                'recent_greenlights': [
                    {'title': g['title'], 'genre': g['genre'], 'year': g['year']}
                    for g in greenlights[:10]
                ]
            }
    
    # ========== VISUALIZATION DATA ==========
    
    def get_dashboard_stats(self):
        """Get overall statistics for dashboard visualization"""
        with self.driver.session() as session:
            # Total greenlights by year
            year_stats = session.run("""
                MATCH (g:Greenlight)
                WHERE g.year IS NOT NULL
                RETURN g.year as year, count(*) as count
                ORDER BY g.year DESC
            """)
            
            # Top genres
            genre_stats = session.run("""
                MATCH (g:Greenlight)
                WHERE g.genre IS NOT NULL
                RETURN g.genre as genre, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            # Top executives
            exec_stats = session.run("""
                MATCH (g:Greenlight)
                WHERE g.executive IS NOT NULL
                RETURN g.executive as executive, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            # Format breakdown
            format_stats = session.run("""
                MATCH (g:Greenlight)
                WHERE g.format IS NOT NULL
                RETURN g.format as format, count(*) as count
                ORDER BY count DESC
            """)
            
            return {
                'greenlights_by_year': [dict(r) for r in year_stats],
                'top_genres': [dict(r) for r in genre_stats],
                'top_executives': [dict(r) for r in exec_stats],
                'format_breakdown': [dict(r) for r in format_stats]
            }

