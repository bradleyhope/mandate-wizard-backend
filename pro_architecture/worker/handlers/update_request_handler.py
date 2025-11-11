"""
UpdateRequest Event Handler
Syncs entity data from PostgreSQL to Pinecone and Neo4j
"""

import os
import psycopg2
from typing import Dict, Any, List


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


def get_entity_from_postgres(entity_id: str) -> Dict[str, Any]:
    """
    Fetch entity data from PostgreSQL
    
    Args:
        entity_id: UUID of the entity
        
    Returns:
        Dictionary with entity data
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, slug, name, entity_type, attributes, 
                   demand_score, last_queried_at, created_at, updated_at
            FROM entities
            WHERE id = %s
        """, (entity_id,))
        
        row = cur.fetchone()
        cur.close()
        
        if not row:
            return None
        
        return {
            'id': row[0],
            'slug': row[1],
            'name': row[2],
            'entity_type': row[3],
            'attributes': row[4],  # JSONB
            'demand_score': row[5],
            'last_queried_at': row[6].isoformat() if row[6] else None,
            'created_at': row[7].isoformat() if row[7] else None,
            'updated_at': row[8].isoformat() if row[8] else None
        }
        
    finally:
        if conn:
            conn.close()


def sync_to_pinecone(entity: Dict[str, Any], operation: str) -> bool:
    """
    Sync entity to Pinecone
    
    Args:
        entity: Entity data from PostgreSQL
        operation: 'create', 'update', or 'delete'
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # TODO: Implement Pinecone sync
        # For now, just log the operation
        print(f"   📌 Pinecone sync ({operation}): {entity['slug']}")
        
        # In Phase 1, we'll implement this as:
        # 1. Generate embedding for entity (name + attributes)
        # 2. Upsert/delete vector in Pinecone
        # 3. Include metadata (entity_type, demand_score, etc.)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pinecone sync failed: {e}")
        return False


def sync_to_neo4j(entity: Dict[str, Any], operation: str) -> bool:
    """
    Sync entity to Neo4j
    
    Args:
        entity: Entity data from PostgreSQL
        operation: 'create', 'update', or 'delete'
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # TODO: Implement Neo4j sync
        # For now, just log the operation
        print(f"   🔗 Neo4j sync ({operation}): {entity['slug']}")
        
        # In Phase 1, we'll implement this as:
        # 1. Create/update/delete node based on entity_type
        # 2. Set node properties from attributes
        # 3. Maintain relationships (from relations table)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Neo4j sync failed: {e}")
        return False


def log_sync_event(entity_id: str, operation: str, pinecone_success: bool, neo4j_success: bool):
    """Log sync event to events table"""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        event_metadata = {
            'operation': operation,
            'pinecone_synced': pinecone_success,
            'neo4j_synced': neo4j_success
        }
        
        cur.execute("""
            INSERT INTO events (event_type, entity_id, metadata, created_at)
            VALUES ('sync', %s, %s, NOW())
        """, (entity_id, str(event_metadata)))
        
        conn.commit()
        cur.close()
        
    except Exception as e:
        print(f"   ⚠️  Failed to log sync event: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def handle_update_request(event_data: dict):
    """
    Handle an UpdateRequest event
    
    Syncs entity data from PostgreSQL (master) to Pinecone and Neo4j
    
    Args:
        event_data: Dictionary with keys:
            - entity_ids: List of entity UUIDs to sync
            - operation: 'create', 'update', or 'delete'
            - source: Source of the update (newsletter, manual, api)
    """
    entity_ids = event_data.get('entity_ids', [])
    operation = event_data.get('operation', 'update')
    source = event_data.get('source', 'unknown')
    
    if not entity_ids:
        print(f"⚠️  UpdateRequest missing entity_ids, skipping")
        return
    
    print(f"🔄 Processing UpdateRequest: {len(entity_ids)} entities ({operation} from {source})")
    
    success_count = 0
    error_count = 0
    
    for entity_id in entity_ids:
        try:
            # Fetch entity from PostgreSQL (master)
            entity = get_entity_from_postgres(entity_id)
            
            if not entity:
                print(f"   ⚠️  Entity {entity_id[:8]}... not found, skipping")
                continue
            
            print(f"   Syncing {entity['slug']} ({entity['entity_type']})...")
            
            # Sync to Pinecone
            pinecone_success = sync_to_pinecone(entity, operation)
            
            # Sync to Neo4j
            neo4j_success = sync_to_neo4j(entity, operation)
            
            # Log the sync event
            log_sync_event(entity_id, operation, pinecone_success, neo4j_success)
            
            if pinecone_success and neo4j_success:
                success_count += 1
                print(f"   ✅ Synced {entity['slug']}")
            else:
                error_count += 1
                print(f"   ⚠️  Partial sync for {entity['slug']}")
            
        except Exception as e:
            print(f"   ❌ Error syncing entity {entity_id[:8]}...: {e}")
            error_count += 1
    
    print(f"✅ UpdateRequest complete: {success_count} synced, {error_count} errors")
    
    # If all entities failed, raise exception to trigger retry
    if error_count > 0 and success_count == 0:
        raise Exception(f"All {error_count} entities failed to sync")
