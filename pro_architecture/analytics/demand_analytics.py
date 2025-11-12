"""
Demand Analytics

Provides analytics queries for entity demand tracking, trending analysis,
and data quality prioritization.
"""

import os
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class DemandAnalytics:
    """Analytics for entity demand tracking"""
    
    def __init__(self):
        """Initialize with database connection"""
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Add SSL mode if not present
        if '?' not in self.db_url:
            self.db_url += '?sslmode=require'
        elif 'sslmode' not in self.db_url:
            self.db_url += '&sslmode=require'
    
    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.db_url)
    
    def get_top_demand_entities(
        self,
        limit: int = 20,
        entity_type: Optional[str] = None,
        min_score: int = 0
    ) -> List[Dict]:
        """
        Get top entities by demand score
        
        Args:
            limit: Maximum number of entities to return
            entity_type: Filter by entity type (person, company, etc.)
            min_score: Minimum demand score
            
        Returns:
            List of entities with demand data
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            query = """
                SELECT 
                    id,
                    name,
                    entity_type,
                    demand_score,
                    query_count,
                    last_queried_at,
                    updated_at,
                    CASE 
                        WHEN updated_at < NOW() - INTERVAL '30 days' AND demand_score > 5 THEN true
                        ELSE false
                    END as needs_update
                FROM entities
                WHERE demand_score >= %s
            """
            
            params = [min_score]
            
            if entity_type:
                query += " AND entity_type = %s"
                params.append(entity_type)
            
            query += " ORDER BY demand_score DESC, query_count DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            entities = []
            for row in rows:
                entities.append({
                    'id': row[0],
                    'name': row[1],
                    'entity_type': row[2],
                    'demand_score': row[3] or 0,
                    'query_count': row[4] or 0,
                    'last_queried_at': row[5].isoformat() if row[5] else None,
                    'last_updated_at': row[6].isoformat() if row[6] else None,
                    'needs_update': row[7]
                })
            
            return entities
            
        finally:
            cur.close()
            conn.close()
    
    def get_entity_demand_details(self, entity_id: str) -> Optional[Dict]:
        """
        Get detailed demand information for a specific entity
        
        Args:
            entity_id: Entity UUID
            
        Returns:
            Entity demand details or None if not found
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Get entity data
            cur.execute("""
                SELECT 
                    id,
                    name,
                    entity_type,
                    demand_score,
                    query_count,
                    last_queried_at,
                    created_at,
                    updated_at
                FROM entities
                WHERE id = %s
            """, (entity_id,))
            
            row = cur.fetchone()
            if not row:
                return None
            
            # Calculate query frequency
            first_query = row[6]  # created_at as proxy for first query
            last_query = row[5]   # last_queried_at
            
            query_frequency = "never"
            if last_query and first_query:
                days_active = (last_query - first_query).days
                if days_active > 0:
                    queries_per_day = row[4] / days_active if row[4] else 0
                    if queries_per_day >= 1:
                        query_frequency = "daily"
                    elif queries_per_day >= 0.14:  # ~1 per week
                        query_frequency = "weekly"
                    elif queries_per_day > 0:
                        query_frequency = "monthly"
            
            # Determine if trending (queried in last 7 days with score > 5)
            trending = False
            if last_query and row[3]:  # demand_score
                days_since_query = (datetime.now() - last_query.replace(tzinfo=None)).days
                trending = days_since_query <= 7 and row[3] > 5
            
            return {
                'id': row[0],
                'name': row[1],
                'entity_type': row[2],
                'demand_score': row[3] or 0,
                'query_count': row[4] or 0,
                'last_queried_at': row[5].isoformat() if row[5] else None,
                'first_queried_at': row[6].isoformat() if row[6] else None,
                'query_frequency': query_frequency,
                'trending': trending
            }
            
        finally:
            cur.close()
            conn.close()
    
    def get_demand_stats(self) -> Dict:
        """
        Get overall demand statistics
        
        Returns:
            Aggregate demand statistics
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Overall stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_entities,
                    COUNT(*) FILTER (WHERE demand_score > 0) as entities_with_demand,
                    SUM(query_count) as total_queries,
                    AVG(demand_score) FILTER (WHERE demand_score > 0) as avg_demand_score,
                    COUNT(*) FILTER (WHERE last_queried_at > NOW() - INTERVAL '7 days' AND demand_score > 5) as trending_entities,
                    COUNT(*) FILTER (WHERE updated_at < NOW() - INTERVAL '30 days' AND demand_score > 5) as needs_update
                FROM entities
            """)
            
            row = cur.fetchone()
            
            # Stats by entity type
            cur.execute("""
                SELECT 
                    entity_type,
                    COUNT(*) FILTER (WHERE demand_score > 0) as count,
                    AVG(demand_score) FILTER (WHERE demand_score > 0) as avg_score
                FROM entities
                WHERE demand_score > 0
                GROUP BY entity_type
                ORDER BY count DESC
            """)
            
            type_stats = []
            for type_row in cur.fetchall():
                type_stats.append({
                    'type': type_row[0],
                    'count': type_row[1],
                    'avg_score': round(float(type_row[2]), 1) if type_row[2] else 0
                })
            
            return {
                'total_entities': row[0],
                'entities_with_demand': row[1],
                'total_queries': row[2] or 0,
                'avg_demand_score': round(float(row[3]), 1) if row[3] else 0,
                'top_entity_types': type_stats,
                'trending_entities': row[4],
                'needs_update': row[5]
            }
            
        finally:
            cur.close()
            conn.close()
    
    def get_trending_entities(
        self,
        timeframe_days: int = 7,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get entities with rapidly increasing demand
        
        Args:
            timeframe_days: Number of days to analyze (1, 7, 30)
            limit: Maximum number of entities to return
            
        Returns:
            List of trending entities with growth metrics
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Get entities queried in the timeframe
            cur.execute("""
                SELECT 
                    e.id,
                    e.name,
                    e.entity_type,
                    e.demand_score,
                    e.query_count,
                    e.last_queried_at,
                    e.updated_at,
                    COUNT(ev.id) as recent_queries
                FROM entities e
                LEFT JOIN events ev ON ev.entity_id = e.id 
                    AND ev.event_type = 'query_signal'
                    AND ev.created_at > NOW() - INTERVAL '%s days'
                WHERE e.last_queried_at > NOW() - INTERVAL '%s days'
                GROUP BY e.id
                HAVING COUNT(ev.id) > 0
                ORDER BY recent_queries DESC, e.demand_score DESC
                LIMIT %s
            """ % (timeframe_days, timeframe_days, limit))
            
            rows = cur.fetchall()
            
            trending = []
            for row in rows:
                # Estimate previous queries (total - recent)
                total_queries = row[4] or 0
                recent_queries = row[7]
                previous_queries = max(1, total_queries - recent_queries)  # Avoid division by zero
                
                # Calculate growth percentage
                growth = ((recent_queries - previous_queries) / previous_queries) * 100
                
                trending.append({
                    'entity': {
                        'id': row[0],
                        'name': row[1],
                        'entity_type': row[2],
                        'demand_score': row[3] or 0,
                        'last_queried_at': row[5].isoformat() if row[5] else None
                    },
                    'demand_growth': f"+{int(growth)}%" if growth > 0 else f"{int(growth)}%",
                    'recent_queries': recent_queries,
                    'previous_queries': previous_queries
                })
            
            return trending
            
        finally:
            cur.close()
            conn.close()
    
    def get_stale_high_demand_entities(
        self,
        days_since_update: int = 30,
        min_demand_score: int = 5,
        limit: int = 20
    ) -> List[Dict]:
        """
        Get high-demand entities with outdated data
        
        Args:
            days_since_update: Minimum days since last update
            min_demand_score: Minimum demand score to consider
            limit: Maximum number of entities to return
            
        Returns:
            List of stale entities prioritized by demand
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT 
                    id,
                    name,
                    entity_type,
                    demand_score,
                    query_count,
                    last_queried_at,
                    updated_at,
                    EXTRACT(DAY FROM (NOW() - updated_at)) as days_since_update,
                    CASE 
                        WHEN demand_score > 20 THEN 'critical'
                        WHEN demand_score > 10 THEN 'high'
                        WHEN demand_score > 5 THEN 'medium'
                        ELSE 'low'
                    END as priority
                FROM entities
                WHERE updated_at < NOW() - INTERVAL '%s days'
                    AND demand_score >= %s
                ORDER BY demand_score DESC, days_since_update DESC
                LIMIT %s
            """ % (days_since_update, min_demand_score, limit))
            
            rows = cur.fetchall()
            
            stale_entities = []
            for row in rows:
                stale_entities.append({
                    'entity': {
                        'id': row[0],
                        'name': row[1],
                        'entity_type': row[2],
                        'demand_score': row[3] or 0,
                        'query_count': row[4] or 0,
                        'last_queried_at': row[5].isoformat() if row[5] else None
                    },
                    'last_updated_at': row[6].isoformat() if row[6] else None,
                    'days_since_update': int(row[7]) if row[7] else 0,
                    'priority': row[8]
                })
            
            return stale_entities
            
        finally:
            cur.close()
            conn.close()
