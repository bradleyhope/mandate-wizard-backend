#!/usr/bin/env python3
"""
Bulk Import Script: Layer 4 (Recent Greenlights)

This script imports recent greenlight data from JSON into both Pinecone and Neo4j.

Usage:
    python3 bulk_import_layer4.py

Input File:
    /home/ubuntu/mandate_wizard_web_app/data/recent_greenlights.json

Output:
    - Vectors in Pinecone namespace "greenlights"
    - Nodes in Neo4j with type Project
    - Relationships: (Executive)-[:GREENLIT]->(Project)
    - Relationships: (ProductionCompany)-[:PRODUCED]->(Project)
"""

import json
import os
import sys
from datetime import datetime
from openai import OpenAI
import pinecone
from neo4j import GraphDatabase

# Configuration
DATA_FILE = "/home/ubuntu/mandate_wizard_web_app/data/recent_greenlights.json"
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = "mandate-wizard"
PINECONE_NAMESPACE = "greenlights"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

def load_data():
    """Load greenlights from JSON file"""
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return data.get('greenlights', [])

def create_embedding_text(greenlight):
    """Create text for embedding from greenlight data"""
    text_parts = [
        f"{greenlight['executive_name']} greenlit {greenlight['project_title']}",
        f"in {greenlight.get('greenlight_date', 'unknown date')}."
    ]
    
    text_parts.append(f"{greenlight['genre']} {greenlight['format']}.")
    
    if greenlight.get('episode_count'):
        text_parts.append(f"{greenlight['episode_count']} episodes.")
    
    if greenlight.get('production_company'):
        text_parts.append(f"Produced by {greenlight['production_company']}.")
    
    if greenlight.get('showrunner'):
        text_parts.append(f"Showrunner: {greenlight['showrunner']}.")
    
    if greenlight.get('cast'):
        cast_str = ', '.join(greenlight['cast'][:3])
        text_parts.append(f"Stars: {cast_str}.")
    
    if greenlight.get('budget_range'):
        text_parts.append(f"Budget: {greenlight['budget_range']}.")
    
    if greenlight.get('notes'):
        text_parts.append(greenlight['notes'])
    
    return " ".join(text_parts)

def import_to_pinecone(greenlights):
    """Import greenlights to Pinecone"""
    print("\n" + "="*70)
    print("IMPORTING TO PINECONE")
    print("="*70)
    
    # Initialize OpenAI and Pinecone
    client = OpenAI()
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX)
    
    vectors = []
    for i, greenlight in enumerate(greenlights):
        print(f"\nProcessing {i+1}/{len(greenlights)}: {greenlight['project_title']}")
        
        # Create embedding text
        text = create_embedding_text(greenlight)
        print(f"  Text: {text[:100]}...")
        
        # Generate embedding
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        ).data[0].embedding
        
        # Prepare metadata
        metadata = {
            "project_title": greenlight['project_title'],
            "executive_name": greenlight['executive_name'],
            "greenlight_date": greenlight.get('greenlight_date', ''),
            "announcement_date": greenlight.get('announcement_date', ''),
            "genre": greenlight['genre'],
            "format": greenlight['format'],
            "season_number": greenlight.get('season_number'),
            "episode_count": greenlight.get('episode_count'),
            "production_company": greenlight.get('production_company', ''),
            "showrunner": greenlight.get('showrunner', ''),
            "cast": greenlight.get('cast', []),
            "budget_range": greenlight.get('budget_range', ''),
            "target_release": greenlight.get('target_release', ''),
            "source_url": greenlight.get('source_url', ''),
            "notes": greenlight.get('notes', ''),
            "layer": "greenlights"
        }
        
        # Create vector ID
        title_slug = greenlight['project_title'].lower().replace(' ', '_').replace(':', '')
        vector_id = f"greenlight_{title_slug}"
        
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })
        
        print(f"  ✅ Prepared vector: {vector_id}")
    
    # Batch upsert to Pinecone
    print(f"\n📤 Upserting {len(vectors)} vectors to Pinecone...")
    index.upsert(vectors=vectors, namespace=PINECONE_NAMESPACE)
    print(f"✅ Successfully imported {len(vectors)} greenlights to Pinecone")

def import_to_neo4j(greenlights):
    """Import greenlights to Neo4j"""
    print("\n" + "="*70)
    print("IMPORTING TO NEO4J")
    print("="*70)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        for i, greenlight in enumerate(greenlights):
            print(f"\nProcessing {i+1}/{len(greenlights)}: {greenlight['project_title']}")
            
            # Create project node
            session.run("""
                MERGE (p:Project {title: $title})
                SET p.greenlight_date = date($greenlight_date),
                    p.announcement_date = date($announcement_date),
                    p.genre = $genre,
                    p.format = $format,
                    p.season_number = $season_number,
                    p.episode_count = $episode_count,
                    p.budget_range = $budget_range,
                    p.target_release = $target_release,
                    p.source_url = $source_url,
                    p.notes = $notes
            """,
                title=greenlight['project_title'],
                greenlight_date=greenlight.get('greenlight_date', ''),
                announcement_date=greenlight.get('announcement_date', ''),
                genre=greenlight['genre'],
                format=greenlight['format'],
                season_number=greenlight.get('season_number'),
                episode_count=greenlight.get('episode_count'),
                budget_range=greenlight.get('budget_range', ''),
                target_release=greenlight.get('target_release', ''),
                source_url=greenlight.get('source_url', ''),
                notes=greenlight.get('notes', '')
            )
            print(f"  ✅ Created Project node")
            
            # Link to executive
            exec_name = greenlight['executive_name']
            result = session.run("""
                MATCH (e:Executive {name: $exec_name})
                MATCH (p:Project {title: $project_title})
                MERGE (e)-[r:GREENLIT]->(p)
                SET r.date = date($greenlight_date)
                RETURN e.name
            """,
                exec_name=exec_name,
                project_title=greenlight['project_title'],
                greenlight_date=greenlight.get('greenlight_date', '')
            )
            
            if result.single():
                print(f"  ✅ Linked to executive: {exec_name}")
            else:
                print(f"  ⚠️  Executive not found: {exec_name}")
            
            # Link to production company
            prodco = greenlight.get('production_company')
            if prodco:
                session.run("""
                    MERGE (pc:ProductionCompany {name: $prodco_name})
                    WITH pc
                    MATCH (p:Project {title: $project_title})
                    MERGE (pc)-[r:PRODUCED]->(p)
                """,
                    prodco_name=prodco,
                    project_title=greenlight['project_title']
                )
                print(f"  ✅ Linked to production company: {prodco}")
    
    driver.close()
    print(f"\n✅ Successfully imported {len(greenlights)} greenlights to Neo4j")

def main():
    print("="*70)
    print("LAYER 4 BULK IMPORT: RECENT GREENLIGHTS")
    print("="*70)
    
    # Load data
    print("\n📂 Loading data from:", DATA_FILE)
    greenlights = load_data()
    print(f"✅ Loaded {len(greenlights)} greenlights")
    
    if not greenlights:
        print("❌ No greenlights found in file. Exiting.")
        sys.exit(1)
    
    # Import to Pinecone
    try:
        import_to_pinecone(greenlights)
    except Exception as e:
        print(f"\n❌ Error importing to Pinecone: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Import to Neo4j
    try:
        import_to_neo4j(greenlights)
    except Exception as e:
        print(f"\n❌ Error importing to Neo4j: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Summary
    print("\n" + "="*70)
    print("IMPORT COMPLETE")
    print("="*70)
    print(f"✅ {len(greenlights)} greenlights imported successfully")
    print(f"📊 Pinecone namespace: {PINECONE_NAMESPACE}")
    print(f"📊 Neo4j node type: Project")
    print("\nNext steps:")
    print("1. Verify data in Pinecone dashboard")
    print("2. Query Neo4j to verify relationships")
    print("3. Test queries in the web app")
    print("="*70)

if __name__ == "__main__":
    main()

