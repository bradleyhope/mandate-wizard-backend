"""
Re-Embed Executives Script
Generates rich text for all executives and re-embeds them in Pinecone with updated metadata.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_client import PostgresClient
from utils.rich_text_builder import build_rich_text
from rag.embedder import get_embedder
from pinecone import Pinecone

def reembed_executives(batch_size: int = 50, entity_type: str = 'person'):
    """
    Re-embed all executives with rich text and updated metadata.
    
    Args:
        batch_size: Number of entities to process in each batch
        entity_type: Type of entity to re-embed ('person', 'project', 'company', or 'all')
    """
    
    print("="*70)
    print("RE-EMBED EXECUTIVES WITH RICH TEXT")
    print("="*70)
    
    # Initialize clients
    pg = PostgresClient()
    embedder = get_embedder()
    pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
    index = pc.Index(os.environ['PINECONE_INDEX_NAME'])
    
    # Build query based on entity_type
    if entity_type == 'all':
        where_clause = "WHERE 1=1"
    else:
        where_clause = f"WHERE entity_type = '{entity_type}'"
    
    # Get all entities with their cards
    print(f"\n📊 Fetching all {entity_type} entities...")
    entities = pg.execute(f"""
        SELECT id, entity_type, name, slug, attributes, priority_score, scope, seniority, query_count
        FROM entities
        {where_clause}
        ORDER BY priority_score DESC NULLS LAST
    """)
    
    print(f"✅ Found {len(entities)} entities to re-embed")
    
    if not entities:
        print("❌ No entities found!")
        return
    
    # Process in batches
    total_processed = 0
    total_updated = 0
    total_errors = 0
    
    for i in range(0, len(entities), batch_size):
        batch = entities[i:i+batch_size]
        print(f"\n📦 Processing batch {i//batch_size + 1} ({len(batch)} entities)...")
        
        vectors_to_upsert = []
        entity_ids_to_update = []
        
        for entity in batch:
            try:
                # Get cards for this entity
                cards = pg.execute("""
                    SELECT card_type, title, content
                    FROM cards
                    WHERE entity_id = %s
                """, (entity['id'],))
                
                # Build rich text
                rich_text = build_rich_text(entity, cards)
                
                if not rich_text or len(rich_text) < 10:
                    print(f"  ⚠️ Skipping {entity['name']} - insufficient text")
                    continue
                
                # Generate embedding
                embedding = embedder.embed_one(rich_text)
                
                # Prepare metadata
                metadata = {
                    'entity_id': entity['id'],
                    'entity_type': entity['entity_type'],
                    'name': entity['name'],
                    'slug': entity['slug'],
                    'text': rich_text[:1000],  # Store first 1000 chars
                    'priority_score': entity.get('priority_score', 50),
                    'scope': entity.get('scope', 'local'),
                    'seniority': entity.get('seniority', 'unknown'),
                    'query_count': entity.get('query_count', 0),
                }
                
                # Add attributes to metadata
                attributes = entity.get('attributes', {})
                if attributes:
                    if attributes.get('title'):
                        metadata['title'] = attributes['title']
                    if attributes.get('company'):
                        metadata['company'] = attributes['company']
                    if attributes.get('region'):
                        metadata['region'] = attributes['region']
                    if attributes.get('genres'):
                        metadata['genres'] = str(attributes['genres'])
                    if attributes.get('formats'):
                        metadata['formats'] = str(attributes['formats'])
                
                # Prepare vector for upsert
                vector_id = f"{entity['entity_type']}_{entity['slug']}"
                vectors_to_upsert.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': metadata
                })
                
                entity_ids_to_update.append(entity['id'])
                
            except Exception as e:
                print(f"  ❌ Error processing {entity['name']}: {str(e)}")
                total_errors += 1
        
        # Upsert batch to Pinecone
        if vectors_to_upsert:
            try:
                # Determine namespace based on entity type
                namespace = 'executives' if entity_type == 'person' else entity_type + 's'
                
                index.upsert(vectors=vectors_to_upsert, namespace=namespace)
                total_updated += len(vectors_to_upsert)
                print(f"  ✅ Upserted {len(vectors_to_upsert)} vectors to Pinecone (namespace: {namespace})")
                
                # Update last_embedded timestamp in PostgreSQL
                pg.execute(f"""
                    UPDATE entities
                    SET last_embedded = %s
                    WHERE id = ANY(%s)
                """, (datetime.utcnow(), entity_ids_to_update), fetch=False)
                
            except Exception as e:
                print(f"  ❌ Error upserting batch to Pinecone: {str(e)}")
                total_errors += len(vectors_to_upsert)
        
        total_processed += len(batch)
        print(f"  Progress: {total_processed}/{len(entities)} ({total_processed/len(entities)*100:.1f}%)")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total entities processed: {total_processed}")
    print(f"Successfully updated: {total_updated}")
    print(f"Errors: {total_errors}")
    print(f"Success rate: {total_updated/total_processed*100:.1f}%")
    
    # Show sample of updated entities
    print("\n📊 Sample of updated entities:")
    sample = pg.execute(f"""
        SELECT name, attributes->>'title' as title, priority_score, scope, seniority, last_embedded
        FROM entities
        {where_clause}
        AND last_embedded IS NOT NULL
        ORDER BY priority_score DESC
        LIMIT 10
    """)
    
    print("\n{:<30} {:<40} {:<8} {:<10} {:<10}".format(
        "Name", "Title", "Score", "Scope", "Seniority"
    ))
    print("-" * 100)
    
    for entity in sample:
        print("{:<30} {:<40} {:<8} {:<10} {:<10}".format(
            entity['name'][:29],
            (entity['title'] or 'N/A')[:39],
            entity['priority_score'] or 0,
            entity['scope'] or 'N/A',
            entity['seniority'] or 'N/A'
        ))
    
    print("\n" + "="*70)
    print("✅ Re-embedding complete!")
    print("="*70)
    
    pg.close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Re-embed entities in Pinecone')
    parser.add_argument('--entity-type', type=str, default='person',
                        choices=['person', 'project', 'company', 'all'],
                        help='Type of entity to re-embed')
    parser.add_argument('--batch-size', type=int, default=50,
                        help='Number of entities to process in each batch')
    
    args = parser.parse_args()
    
    reembed_executives(batch_size=args.batch_size, entity_type=args.entity_type)
