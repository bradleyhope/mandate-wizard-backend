"""
QuerySignal Event Handler
Updates entity demand scores when users query them
"""

import os
import psycopg2
from datetime import datetime


def get_db_connection():
    """Get PostgreSQL database connection"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Add SSL mode if not present
    if '?' not in database_url:
        database_url += '?sslmode=require'
    elif 'sslmode' not in database_url:
        database_url += '&sslmode=require'
    
    return psycopg2.connect(database_url)


def handle_query_signal(event_data: dict):
    """
    Handle a QuerySignal event
    
    Updates the entity's demand_score and last_queried_at timestamp
    Logs the event to the events table for audit trail
    
    Args:
        event_data: Dictionary with keys:
            - entity_id: UUID of the queried entity
            - entity_type: Type of entity (person, company, etc.)
            - query: The user's query text
            - user_id: User identifier
            - timestamp: Unix timestamp of the query
    """
    entity_id = event_data.get('entity_id')
    entity_type = event_data.get('entity_type')
    query = event_data.get('query')
    user_id = event_data.get('user_id')
    timestamp = event_data.get('timestamp')
    
    if not entity_id:
        print(f"⚠️  QuerySignal missing entity_id, skipping")
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Update entity demand score and last_queried_at
        cur.execute("""
            UPDATE entities 
            SET demand_score = COALESCE(demand_score, 0) + 1,
                last_queried_at = NOW(),
                updated_at = NOW()
            WHERE id = %s
            RETURNING demand_score, last_queried_at
        """, (entity_id,))
        
        result = cur.fetchone()
        
        if result:
            new_demand_score, last_queried = result
            print(f"✅ Updated entity {entity_id[:8]}... demand_score={new_demand_score}")
            
            # Log the event to events table
            event_metadata = {
                'entity_type': entity_type,
                'query': query,
                'user_id': user_id,
                'timestamp': timestamp,
                'new_demand_score': new_demand_score
            }
            
            cur.execute("""
                INSERT INTO events (event_type, entity_id, metadata, created_at)
                VALUES ('query', %s, %s, NOW())
            """, (entity_id, str(event_metadata)))
            
            conn.commit()
        else:
            print(f"⚠️  Entity {entity_id} not found in database, skipping")
            conn.rollback()
        
        cur.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error handling QuerySignal: {e}")
        if conn:
            conn.rollback()
        raise  # Re-raise to trigger retry
        
    except Exception as e:
        print(f"❌ Error handling QuerySignal: {e}")
        if conn:
            conn.rollback()
        raise  # Re-raise to trigger retry
        
    finally:
        if conn:
            conn.close()
