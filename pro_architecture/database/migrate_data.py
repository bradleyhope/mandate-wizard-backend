"""
Data Migration: Pinecone + Neo4j → PostgreSQL (FIXED VERSION)
Migrates all existing data into PostgreSQL as single source of truth
"""

import os
import sys
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_client import PostgresClient


def get_entity_slug_from_neo4j_node(node_dict):
    """
    Extract entity slug from Neo4j node.
    Handles multiple ID formats and fallback to name.
    
    Args:
        node_dict: Dictionary of node properties
        
    Returns:
        str: Entity slug (e.g., 'anne_mensah')
    """
    # Try entity_id first (might be slug format)
    entity_id = node_dict.get('entity_id')
    if entity_id and isinstance(entity_id, str):
        # Check if it's a slug (not UUID)
        if '-' not in entity_id or len(entity_id) < 30:
            # It's a slug like 'person_anne_mensah' or 'alana_mayo'
            if entity_id.startswith('person_'):
                return entity_id.replace('person_', '')
            elif entity_id.startswith('company_'):
                return entity_id.replace('company_', '')
            elif entity_id.startswith('prodco_'):
                return entity_id.replace('prodco_', '')
            elif entity_id.startswith('platform_'):
                return entity_id.replace('platform_', '')
            else:
                return entity_id
    
    # Try id field (legacy)
    id_field = node_dict.get('id')
    if id_field and isinstance(id_field, str):
        if id_field.startswith('person_'):
            return id_field.replace('person_', '')
        elif id_field.startswith('company_'):
            return id_field.replace('company_', '')
        else:
            return id_field
    
    # Fallback: create slug from name
    name = node_dict.get('name')
    if name:
        slug = name.lower().replace(' ', '_').replace('.', '').replace(',', '').replace("'", '')
        # Remove multiple underscores
        while '__' in slug:
            slug = slug.replace('__', '_')
        return slug
    
    return None


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
                    
                except Exception as e:
                    errors.append(f"Error migrating {vector_id}: {str(e)}")
        
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
        
        print(f"\n✅ Entities created: {entities_created}")
        print(f"✅ Cards created: {cards_created}")
        
        return {
            'success': True,
            'message': f'Migrated {entities_created} entities and {cards_created} cards from Pinecone',
            'entities_created': entities_created,
            'cards_created': cards_created,
            'errors': errors[:10]
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Pinecone migration failed: {str(e)}",
            'entities_created': 0,
            'cards_created': 0
        }


def migrate_neo4j_to_postgres(pg_client):
    """
    Migrate data from Neo4j to PostgreSQL (FIXED VERSION).
    Handles all node types and multiple ID formats.
    
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
    print("📥 MIGRATING DATA FROM NEO4J TO POSTGRESQL (FIXED)")
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
        
        # Map to track Neo4j node ID -> PostgreSQL entity ID
        node_to_entity_map = {}
        
        with driver.session() as session:
            # Migrate Person nodes
            print("\n👤 Migrating Person nodes...")
            persons_result = session.run("MATCH (p:Person) RETURN p")
            persons = list(persons_result)
            print(f"  Found {len(persons)} Person nodes")
            
            for record in persons:
                try:
                    person_dict = dict(record['p'])
                    name = person_dict.get('name')
                    
                    if not name:
                        continue
                    
                    slug = get_entity_slug_from_neo4j_node(person_dict)
                    if not slug:
                        continue
                    
                    # Check if entity already exists
                    existing = pg_client.get_entity(slug=slug)
                    
                    if existing:
                        # Update with Neo4j data
                        entities_updated += 1
                        node_to_entity_map[slug] = existing['id']
                    else:
                        # Create new entity
                        attributes = {
                            'title': person_dict.get('current_title'),
                            'company': person_dict.get('streamer'),
                            'region': person_dict.get('region'),
                            'email': person_dict.get('email'),
                            'phone': person_dict.get('phone'),
                            'neo4j_entity_id': person_dict.get('entity_id'),
                            'neo4j_person_id': person_dict.get('person_id'),
                            'source': 'neo4j_migration'
                        }
                        
                        # Remove None values
                        attributes = {k: v for k, v in attributes.items() if v is not None}
                        
                        pg_entity_id = pg_client.create_entity(
                            entity_type='person',
                            name=name,
                            slug=slug,
                            attributes=attributes,
                            confidence_score=0.8,
                            source='neo4j_migration',
                            created_by='migration_script'
                        )
                        entities_created += 1
                        node_to_entity_map[slug] = pg_entity_id
                        print(f"  ✅ Created: {name}")
                    
                except Exception as e:
                    error_msg = f"Error migrating Person {person_dict.get('name', 'unknown')}: {str(e)}"
                    print(f"  ❌ {error_msg}")
                    errors.append(error_msg)
                    # Continue to next entity
            
            # Migrate Company nodes
            print("\n🏢 Migrating Company nodes...")
            companies_result = session.run("MATCH (c:Company) RETURN c")
            companies = list(companies_result)
            print(f"  Found {len(companies)} Company nodes")
            
            for record in companies:
                try:
                    company_dict = dict(record['c'])
                    name = company_dict.get('name')
                    
                    if not name:
                        continue
                    
                    slug = get_entity_slug_from_neo4j_node(company_dict)
                    if not slug:
                        continue
                    
                    existing = pg_client.get_entity(slug=slug)
                    
                    if existing:
                        entities_updated += 1
                        node_to_entity_map[slug] = existing['id']
                    else:
                        attributes = {
                            'neo4j_entity_id': company_dict.get('entity_id'),
                            'source': 'neo4j_migration'
                        }
                        attributes = {k: v for k, v in attributes.items() if v is not None}
                        
                        pg_entity_id = pg_client.create_entity(
                            entity_type='company',
                            name=name,
                            slug=slug,
                            attributes=attributes,
                            confidence_score=0.8,
                            source='neo4j_migration',
                            created_by='migration_script'
                        )
                        entities_created += 1
                        node_to_entity_map[slug] = pg_entity_id
                        print(f"  ✅ Created: {name}")
                    
                except Exception as e:
                    errors.append(f"Error migrating Company {company_dict.get('name', 'unknown')}: {str(e)}")
            
            # Migrate ProductionCompany nodes
            print("\n🎬 Migrating ProductionCompany nodes...")
            prodcos_result = session.run("MATCH (pc:ProductionCompany) RETURN pc")
            prodcos = list(prodcos_result)
            print(f"  Found {len(prodcos)} ProductionCompany nodes")
            
            for record in prodcos:
                try:
                    prodco_dict = dict(record['pc'])
                    name = prodco_dict.get('name')
                    
                    if not name:
                        continue
                    
                    slug = get_entity_slug_from_neo4j_node(prodco_dict)
                    if not slug:
                        continue
                    
                    existing = pg_client.get_entity(slug=slug)
                    
                    if existing:
                        entities_updated += 1
                        node_to_entity_map[slug] = existing['id']
                    else:
                        attributes = {
                            'neo4j_entity_id': prodco_dict.get('entity_id'),
                            'source': 'neo4j_migration'
                        }
                        attributes = {k: v for k, v in attributes.items() if v is not None}
                        
                        pg_entity_id = pg_client.create_entity(
                            entity_type='production_company',
                            name=name,
                            slug=slug,
                            attributes=attributes,
                            confidence_score=0.8,
                            source='neo4j_migration',
                            created_by='migration_script'
                        )
                        entities_created += 1
                        node_to_entity_map[slug] = pg_entity_id
                        print(f"  ✅ Created: {name}")
                    
                except Exception as e:
                    errors.append(f"Error migrating ProductionCompany: {str(e)}")
            
            # Migrate Platform nodes
            print("\n📺 Migrating Platform nodes...")
            platforms_result = session.run("MATCH (p:Platform) RETURN p")
            platforms = list(platforms_result)
            print(f"  Found {len(platforms)} Platform nodes")
            
            for record in platforms:
                try:
                    platform_dict = dict(record['p'])
                    name = platform_dict.get('name')
                    
                    if not name:
                        continue
                    
                    slug = get_entity_slug_from_neo4j_node(platform_dict)
                    if not slug:
                        continue
                    
                    existing = pg_client.get_entity(slug=slug)
                    
                    if existing:
                        entities_updated += 1
                        node_to_entity_map[slug] = existing['id']
                    else:
                        attributes = {
                            'neo4j_entity_id': platform_dict.get('entity_id'),
                            'source': 'neo4j_migration'
                        }
                        attributes = {k: v for k, v in attributes.items() if v is not None}
                        
                        pg_entity_id = pg_client.create_entity(
                            entity_type='platform',
                            name=name,
                            slug=slug,
                            attributes=attributes,
                            confidence_score=0.8,
                            source='neo4j_migration',
                            created_by='migration_script'
                        )
                        entities_created += 1
                        node_to_entity_map[slug] = pg_entity_id
                        print(f"  ✅ Created: {name}")
                    
                except Exception as e:
                    errors.append(f"Error migrating Platform: {str(e)}")
            
            # Migrate relationships
            print("\n🔗 Migrating relationships...")
            
            # Key relationship types to migrate
            rel_types = ['REPORTS_TO', 'WORKS_WITH', 'AT_COMPANY']
            
            for rel_type in rel_types:
                print(f"\n  Migrating {rel_type} relationships...")
                rels_result = session.run(f"""
                    MATCH (from)-[r:{rel_type}]->(to)
                    RETURN from, r, to
                """)
                rels = list(rels_result)
                print(f"    Found {len(rels)} {rel_type} relationships")
                
                for record in rels:
                    try:
                        from_dict = dict(record['from'])
                        to_dict = dict(record['to'])
                        rel_dict = dict(record['r'])
                        
                        from_slug = get_entity_slug_from_neo4j_node(from_dict)
                        to_slug = get_entity_slug_from_neo4j_node(to_dict)
                        
                        if not from_slug or not to_slug:
                            continue
                        
                        from_entity_id = node_to_entity_map.get(from_slug)
                        to_entity_id = node_to_entity_map.get(to_slug)
                        
                        if not from_entity_id or not to_entity_id:
                            continue
                        
                        # Create relation
                        pg_client.create_relation(
                            from_entity_id=from_entity_id,
                            to_entity_id=to_entity_id,
                            relation_type=rel_type.lower(),
                            attributes=rel_dict,
                            confidence_score=0.8,
                            source='neo4j_migration'
                        )
                        relations_created += 1
                        
                    except Exception as e:
                        errors.append(f"Error migrating {rel_type} relationship: {str(e)}")
            
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
        
        print(f"\n✅ Entities created: {entities_created}")
        print(f"✅ Entities updated: {entities_updated}")
        print(f"✅ Relations created: {relations_created}")
        
        return {
            'success': True,
            'message': f'Migrated {entities_created} new entities, updated {entities_updated} entities, created {relations_created} relations from Neo4j',
            'entities_created': entities_created,
            'entities_updated': entities_updated,
            'relations_created': relations_created,
            'errors': errors[:10]
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n❌ NEO4J MIGRATION FAILED:")
        print(f"Error: {str(e)}")
        print(f"\nFull traceback:\n{error_details}")
        return {
            'success': False,
            'message': f"Neo4j migration failed: {str(e)}",
            'entities_created': entities_created,
            'entities_updated': entities_updated,
            'relations_created': relations_created,
            'errors': errors[:20]
        }


def run_full_migration():
    """Run complete migration from both Pinecone and Neo4j"""
    print("\n" + "="*60)
    print("🚀 STARTING FULL DATA MIGRATION")
    print("="*60)
    
    # Initialize PostgreSQL client
    pg_client = PostgresClient()
    
    # Migrate from Pinecone
    pinecone_result = migrate_pinecone_to_postgres(pg_client)
    
    # Migrate from Neo4j
    neo4j_result = migrate_neo4j_to_postgres(pg_client)
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE")
    print("="*60)
    
    return {
        'success': True,
        'pinecone': pinecone_result,
        'neo4j': neo4j_result
    }


if __name__ == '__main__':
    result = run_full_migration()
    print("\nFinal result:")
    print(json.dumps(result, indent=2))
