"""
Data Migration: Pinecone + Neo4j → PostgreSQL
Migrates all existing data into PostgreSQL as single source of truth
"""

import os
import sys
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_client import PostgresClient

def migrate_pinecone_to_postgres(pg_client):
    """
    Migrate data from Pinecone to PostgreSQL.
    
    Args:
        pg_client: PostgresClient instance
        
    Returns:
        dict: Migration summary
    """
    try:
        from pinecone import Pinecone
    except ImportError:
        return {
            'success': False,
            'message': 'Pinecone library not available',
            'entities_created': 0,
            'cards_created': 0
        }
    
    print("\n" + "="*60)
    print("📥 MIGRATING DATA FROM PINECONE TO POSTGRESQL")
    print("="*60)
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index_name = os.getenv('PINECONE_INDEX', 'mandate-wizard')
        index = pc.Index(index_name)
        
        # Get index stats
        stats = index.describe_index_stats()
        total_vectors = stats.get('total_vector_count', 0)
        print(f"\n📊 Pinecone index '{index_name}' has {total_vectors} vectors")
        
        if total_vectors == 0:
            print("⚠️  No vectors found in Pinecone. Skipping migration.")
            return {
                'success': True,
                'message': 'No vectors to migrate',
                'entities_created': 0,
                'cards_created': 0
            }
        
        # Fetch all vector IDs first
        print("\n🔍 Fetching vector IDs...")
        all_ids = []
        
        # Use list operation to get all IDs
        for ids_batch in index.list():
            all_ids.extend(ids_batch)
        
        print(f"✅ Found {len(all_ids)} vector IDs")
        
        # Fetch vectors in batches
        entities_created = 0
        cards_created = 0
        errors = []
        
        batch_size = 100
        for i in range(0, len(all_ids), batch_size):
            batch_ids = all_ids[i:i+batch_size]
            print(f"\n📦 Processing batch {i//batch_size + 1}/{(len(all_ids)-1)//batch_size + 1} ({len(batch_ids)} vectors)...")
            
            # Fetch vectors with metadata
            fetch_response = index.fetch(ids=batch_ids)
            
            for vector_id, vector_data in fetch_response.get('vectors', {}).items():
                try:
                    metadata = vector_data.get('metadata', {})
                    
                    if not metadata:
                        print(f"  ⚠️  Skipping {vector_id}: no metadata")
                        continue
                    
                    # Extract entity info
                    entity_id = metadata.get('id', vector_id)
                    name = metadata.get('name', 'Unknown')
                    
                    # Determine entity type from ID
                    if entity_id.startswith('person_'):
                        entity_type = 'person'
                        slug = entity_id.replace('person_', '')
                    elif entity_id.startswith('company_'):
                        entity_type = 'company'
                        slug = entity_id.replace('company_', '')
                    elif entity_id.startswith('project_'):
                        entity_type = 'project'
                        slug = entity_id.replace('project_', '')
                    else:
                        entity_type = 'person'
                        slug = entity_id
                    
                    # Check if entity already exists
                    existing = pg_client.get_entity(slug=slug)
                    if existing:
                        print(f"  ⏭️  Skipping {name}: already exists")
                        continue
                    
                    # Build attributes
                    attributes = {
                        'title': metadata.get('title'),
                        'company': metadata.get('streamer'),
                        'region': metadata.get('region'),
                        'formats': metadata.get('formats'),
                        'genres': metadata.get('genres'),
                        'pinecone_id': entity_id,
                        'pinecone_vector_id': vector_id,
                        'source': 'pinecone_migration'
                    }
                    
                    # Remove None values
                    attributes = {k: v for k, v in attributes.items() if v is not None}
                    
                    # Create entity
                    pg_entity_id = pg_client.create_entity(
                        entity_type=entity_type,
                        name=name,
                        slug=slug,
                        attributes=attributes,
                        confidence_score=0.8,
                        source='pinecone_migration',
                        created_by='migration_script'
                    )
                    entities_created += 1
                    print(f"  ✅ Created entity: {name} ({entity_type})")
                    
                    # Create bio card if exists
                    bio = metadata.get('bio')
                    if bio and len(bio.strip()) > 0:
                        pg_client.create_card(
                            entity_id=pg_entity_id,
                            card_type='bio',
                            title=f"Bio - {name}",
                            content=bio,
                            confidence_score=0.8,
                            source='pinecone_migration'
                        )
                        cards_created += 1
                        print(f"    📝 Created bio card")
                    
                    # Create mandate card if exists
                    mandate = metadata.get('mandate')
                    if mandate and len(mandate.strip()) > 0:
                        pg_client.create_card(
                            entity_id=pg_entity_id,
                            card_type='mandate',
                            title=f"Mandate - {name}",
                            content=mandate,
                            confidence_score=0.8,
                            source='pinecone_migration'
                        )
                        cards_created += 1
                        print(f"    📝 Created mandate card")
                    
                except Exception as e:
                    error_msg = f"Error migrating {vector_id}: {str(e)}"
                    print(f"  ❌ {error_msg}")
                    errors.append(error_msg)
        
        # Log migration event
        pg_client.insert_event(
            event_id=f"pinecone_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type='data_update_signal',
            data={
                'migration_type': 'pinecone_to_postgres',
                'entities_created': entities_created,
                'cards_created': cards_created,
                'errors_count': len(errors)
            }
        )
        
        print("\n" + "="*60)
        print("📊 PINECONE MIGRATION SUMMARY")
        print("="*60)
        print(f"  ✅ Entities created: {entities_created}")
        print(f"  ✅ Cards created: {cards_created}")
        print(f"  ❌ Errors: {len(errors)}")
        print("="*60)
        
        return {
            'success': True,
            'message': f'Migrated {entities_created} entities and {cards_created} cards from Pinecone',
            'entities_created': entities_created,
            'cards_created': cards_created,
            'errors': errors[:10]  # First 10 errors
        }
        
    except Exception as e:
        error_msg = f"Pinecone migration failed: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'entities_created': 0,
            'cards_created': 0
        }


def migrate_neo4j_to_postgres(pg_client):
    """
    Migrate data from Neo4j to PostgreSQL.
    
    Args:
        pg_client: PostgresClient instance
        
    Returns:
        dict: Migration summary
    """
    try:
        from neo4j import GraphDatabase
    except ImportError:
        return {
            'success': False,
            'message': 'Neo4j library not available',
            'entities_created': 0,
            'entities_updated': 0,
            'relations_created': 0
        }
    
    print("\n" + "="*60)
    print("📥 MIGRATING DATA FROM NEO4J TO POSTGRESQL")
    print("="*60)
    
    try:
        # Initialize Neo4j
        neo4j_uri = os.getenv('NEO4J_URI')
        neo4j_user = os.getenv('NEO4J_USER')
        neo4j_password = os.getenv('NEO4J_PASSWORD')
        
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        entities_created = 0
        entities_updated = 0
        relations_created = 0
        errors = []
        
        with driver.session() as session:
            # Migrate Person nodes
            print("\n👤 Migrating Person nodes...")
            persons_result = session.run("MATCH (p:Person) RETURN p")
            persons = list(persons_result)
            print(f"  Found {len(persons)} Person nodes")
            
            for record in persons:
                try:
                    person = dict(record['p'])
                    person_id = person.get('id')
                    
                    if not person_id:
                        continue
                    
                    slug = person_id.replace('person_', '')
                    existing = pg_client.get_entity(slug=slug)
                    
                    if existing:
                        # Update with Neo4j data
                        attributes = existing.get('attributes', {})
                        if isinstance(attributes, str):
                            attributes = json.loads(attributes)
                        
                        attributes.update({
                            'email': person.get('email'),
                            'phone': person.get('phone'),
                            'neo4j_migrated': True
                        })
                        
                        pg_client.update_entity(
                            entity_id=existing['id'],
                            attributes=attributes,
                            updated_by='neo4j_migration'
                        )
                        entities_updated += 1
                        print(f"  🔄 Updated: {person.get('name')}")
                    else:
                        # Create new entity
                        pg_entity_id = pg_client.create_entity(
                            entity_type='person',
                            name=person.get('name', 'Unknown'),
                            slug=slug,
                            attributes={
                                'title': person.get('title'),
                                'email': person.get('email'),
                                'phone': person.get('phone'),
                                'neo4j_id': person_id,
                                'source': 'neo4j_migration'
                            },
                            confidence_score=0.8,
                            source='neo4j_migration',
                            created_by='migration_script'
                        )
                        entities_created += 1
                        print(f"  ✅ Created: {person.get('name')}")
                        
                except Exception as e:
                    error_msg = f"Error migrating person: {str(e)}"
                    print(f"  ❌ {error_msg}")
                    errors.append(error_msg)
            
            # Migrate Company nodes
            print("\n🏢 Migrating Company nodes...")
            companies_result = session.run("MATCH (c:Company) RETURN c")
            companies = list(companies_result)
            print(f"  Found {len(companies)} Company nodes")
            
            for record in companies:
                try:
                    company = dict(record['c'])
                    company_id = company.get('id')
                    
                    if not company_id:
                        continue
                    
                    slug = company_id.replace('company_', '')
                    existing = pg_client.get_entity(slug=slug)
                    
                    if not existing:
                        pg_entity_id = pg_client.create_entity(
                            entity_type='company',
                            name=company.get('name', 'Unknown'),
                            slug=slug,
                            attributes={
                                'neo4j_id': company_id,
                                'source': 'neo4j_migration'
                            },
                            confidence_score=0.8,
                            source='neo4j_migration',
                            created_by='migration_script'
                        )
                        entities_created += 1
                        print(f"  ✅ Created: {company.get('name')}")
                        
                except Exception as e:
                    error_msg = f"Error migrating company: {str(e)}"
                    print(f"  ❌ {error_msg}")
                    errors.append(error_msg)
            
            # Migrate relationships
            print("\n🔗 Migrating relationships...")
            rels_result = session.run("""
                MATCH (from)-[r]->(to)
                RETURN from.id as from_id, to.id as to_id, type(r) as rel_type, properties(r) as props
            """)
            rels = list(rels_result)
            print(f"  Found {len(rels)} relationships")
            
            for record in rels:
                try:
                    from_id = record['from_id']
                    to_id = record['to_id']
                    rel_type = record['rel_type'].lower()
                    props = dict(record['props']) if record['props'] else {}
                    
                    if not from_id or not to_id:
                        continue
                    
                    # Get slugs
                    from_slug = from_id.replace('person_', '').replace('company_', '')
                    to_slug = to_id.replace('person_', '').replace('company_', '')
                    
                    # Get entities
                    from_entity = pg_client.get_entity(slug=from_slug)
                    to_entity = pg_client.get_entity(slug=to_slug)
                    
                    if not from_entity or not to_entity:
                        print(f"  ⚠️  Skipping: entities not found ({from_id} -> {to_id})")
                        continue
                    
                    # Create relation
                    pg_client.create_relation(
                        from_entity_id=from_entity['id'],
                        to_entity_id=to_entity['id'],
                        relation_type=rel_type,
                        attributes=props,
                        confidence_score=0.8
                    )
                    relations_created += 1
                    print(f"  ✅ Created: {from_id} -{rel_type}-> {to_id}")
                    
                except Exception as e:
                    error_msg = f"Error migrating relationship: {str(e)}"
                    print(f"  ❌ {error_msg}")
                    errors.append(error_msg)
        
        driver.close()
        
        # Log migration event
        pg_client.insert_event(
            event_id=f"neo4j_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type='data_update_signal',
            data={
                'migration_type': 'neo4j_to_postgres',
                'entities_created': entities_created,
                'entities_updated': entities_updated,
                'relations_created': relations_created,
                'errors_count': len(errors)
            }
        )
        
        print("\n" + "="*60)
        print("📊 NEO4J MIGRATION SUMMARY")
        print("="*60)
        print(f"  ✅ Entities created: {entities_created}")
        print(f"  🔄 Entities updated: {entities_updated}")
        print(f"  ✅ Relations created: {relations_created}")
        print(f"  ❌ Errors: {len(errors)}")
        print("="*60)
        
        return {
            'success': True,
            'message': f'Migrated {entities_created} new entities, updated {entities_updated} entities, created {relations_created} relations from Neo4j',
            'entities_created': entities_created,
            'entities_updated': entities_updated,
            'relations_created': relations_created,
            'errors': errors[:10]
        }
        
    except Exception as e:
        error_msg = f"Neo4j migration failed: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'entities_created': 0,
            'entities_updated': 0,
            'relations_created': 0
        }


def run_full_migration():
    """Run complete data migration from Pinecone and Neo4j to PostgreSQL."""
    print("\n" + "="*60)
    print("🚀 STARTING FULL DATA MIGRATION")
    print("="*60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Initialize PostgreSQL client
        pg_client = PostgresClient()
        
        # Run Pinecone migration
        pinecone_result = migrate_pinecone_to_postgres(pg_client)
        
        # Run Neo4j migration
        neo4j_result = migrate_neo4j_to_postgres(pg_client)
        
        # Close connection
        pg_client.close()
        
        # Combined summary
        print("\n" + "="*60)
        print("🎉 MIGRATION COMPLETE")
        print("="*60)
        print(f"Total entities created: {pinecone_result.get('entities_created', 0) + neo4j_result.get('entities_created', 0)}")
        print(f"Total entities updated: {neo4j_result.get('entities_updated', 0)}")
        print(f"Total cards created: {pinecone_result.get('cards_created', 0)}")
        print(f"Total relations created: {neo4j_result.get('relations_created', 0)}")
        print("="*60)
        
        return {
            'success': True,
            'pinecone': pinecone_result,
            'neo4j': neo4j_result
        }
        
    except Exception as e:
        error_msg = f"Migration failed: {str(e)}"
        print(f"\n❌ {error_msg}")
        return {
            'success': False,
            'message': error_msg
        }


if __name__ == "__main__":
    run_full_migration()
