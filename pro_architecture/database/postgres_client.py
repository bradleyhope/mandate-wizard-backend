"""
PostgreSQL Client for Mandate Wizard
System of Record (SoR) for all entity data
"""

import os
import psycopg2
import psycopg2.extras
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

class PostgresClient:
    """Client for PostgreSQL system of record."""
    
    def __init__(self, database_url: str = None):
        """
        Initialize PostgreSQL client.
        
        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.conn = None
        self.connect()
    
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                self.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            print("✅ PostgreSQL connected")
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            raise
    
    def execute(self, query: str, params: tuple = None, fetch=True) -> List[Dict]:
        """Execute query and return results."""
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                if fetch and cur.description:
                    result = [dict(row) for row in cur.fetchall()]
                    self.conn.commit()
                    return result
                self.conn.commit()
                return []
        except Exception as e:
            # Rollback transaction on error
            self.conn.rollback()
            # Re-raise the exception
            raise
    
    # Entity operations
    
    def create_entity(
        self,
        entity_type: str,
        name: str,
        slug: str,
        attributes: Dict,
        confidence_score: float = 0.5,
        source: str = "manual",
        created_by: str = None
    ) -> str:
        """Create a new entity. Returns entity UUID."""
        query = """
            INSERT INTO entities (
                entity_type, name, slug, attributes,
                confidence_score, source, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute(
            query,
            (entity_type, name, slug, json.dumps(attributes),
             confidence_score, source, created_by)
        )
        return str(result[0]['id'])
    
    def get_entity(self, entity_id: str = None, slug: str = None) -> Optional[Dict]:
        """Get entity by ID or slug."""
        if entity_id:
            query = "SELECT * FROM entities WHERE id = %s"
            params = (entity_id,)
        elif slug:
            query = "SELECT * FROM entities WHERE slug = %s"
            params = (slug,)
        else:
            return None
        
        results = self.execute(query, params)
        if results:
            entity = results[0]
            # Parse JSONB attributes
            if isinstance(entity.get('attributes'), str):
                entity['attributes'] = json.loads(entity['attributes'])
            return entity
        return None
    
    def update_entity(
        self,
        entity_id: str,
        attributes: Dict = None,
        confidence_score: float = None,
        verification_status: str = None,
        updated_by: str = None
    ):
        """Update entity attributes."""
        updates = []
        params = []
        
        if attributes:
            updates.append("attributes = %s")
            params.append(json.dumps(attributes))
        if confidence_score is not None:
            updates.append("confidence_score = %s")
            params.append(confidence_score)
        if verification_status:
            updates.append("verification_status = %s")
            params.append(verification_status)
        if updated_by:
            updates.append("updated_by = %s")
            params.append(updated_by)
        
        if not updates:
            return
        
        params.append(entity_id)
        query = f"UPDATE entities SET {', '.join(updates)} WHERE id = %s"
        self.execute(query, tuple(params), fetch=False)
    
    def increment_demand_score(self, entity_id: str = None, slug: str = None):
        """Increment demand score for entity."""
        if entity_id:
            query = """
                UPDATE entities
                SET demand_score = demand_score + 1,
                    query_count = query_count + 1,
                    last_queried_at = NOW()
                WHERE id = %s
            """
            params = (entity_id,)
        elif slug:
            query = """
                UPDATE entities
                SET demand_score = demand_score + 1,
                    query_count = query_count + 1,
                    last_queried_at = NOW()
                WHERE slug = %s
            """
            params = (slug,)
        else:
            return
        
        self.execute(query, params, fetch=False)
    
    # Card operations
    
    def create_card(
        self,
        entity_id: str,
        card_type: str,
        title: str,
        content: str,
        confidence_score: float = 0.5,
        source: str = "manual"
    ) -> str:
        """Create a new card. Returns card UUID."""
        query = """
            INSERT INTO cards (
                entity_id, card_type, title, content,
                confidence_score, source
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        result = self.execute(
            query,
            (entity_id, card_type, title, content, confidence_score, source)
        )
        return str(result[0]['id'])
    
    def get_cards_for_entity(
        self,
        entity_id: str,
        card_type: str = None
    ) -> List[Dict]:
        """Get all cards for an entity."""
        query = "SELECT * FROM cards WHERE entity_id = %s"
        params = [entity_id]
        
        if card_type:
            query += " AND card_type = %s"
            params.append(card_type)
        
        query += " ORDER BY created_at DESC"
        return self.execute(query, tuple(params))
    
    # Relation operations
    
    def create_relation(
        self,
        from_entity_id: str,
        to_entity_id: str,
        relation_type: str,
        attributes: Dict = None,
        confidence_score: float = 0.5
    ) -> str:
        """Create a new relation. Returns relation UUID."""
        query = """
            INSERT INTO relations (
                from_entity_id, to_entity_id, relation_type,
                attributes, confidence_score
            )
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (from_entity_id, to_entity_id, relation_type)
            DO UPDATE SET
                attributes = EXCLUDED.attributes,
                confidence_score = EXCLUDED.confidence_score,
                updated_at = NOW()
            RETURNING id
        """
        result = self.execute(
            query,
            (from_entity_id, to_entity_id, relation_type,
             json.dumps(attributes or {}), confidence_score)
        )
        return str(result[0]['id'])
    
    # Event operations
    
    def insert_event(
        self,
        event_id: str,
        event_type: str,
        data: Dict,
        user_id: str = None,
        entity_id: str = None
    ):
        """Insert an event into the events table."""
        query = """
            INSERT INTO events (event_id, event_type, user_id, entity_id, data)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.execute(
            query,
            (event_id, event_type, user_id, entity_id, json.dumps(data)),
            fetch=False
        )
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
