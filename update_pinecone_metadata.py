#!/usr/bin/env python3
"""
Update Pinecone with Enriched Metadata
Re-embeds greenlights with loglines, descriptions, and executive info
"""

from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
import json
from typing import List, Dict
import time

# Pinecone configuration
PINECONE_API_KEY = "pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1"
PINECONE_INDEX_NAME = "netflix-mandate-wizard"

# Neo4j connection
NEO4J_URI = "neo4j+s://0dd3462a.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg"

# Initialize embedding model (same as used in hybridrag_engine_pinecone.py)
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Initialize Pinecone
print("Connecting to Pinecone...")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def get_greenlights_with_metadata(driver) -> List[Dict]:
    """Get all greenlights with their enriched metadata"""
    with driver.session() as session:
        result = session.run("""
            MATCH (g:Greenlight)
            OPTIONAL MATCH (p:Person)-[:GREENLIT]->(g)
            WITH g, collect(p.name) AS executives
            RETURN g.title AS title,
                   g.genre AS genre,
                   g.format AS format,
                   g.streamer AS streamer,
                   g.logline AS logline,
                   g.description AS description,
                   g.episode_count AS episode_count,
                   executives
            ORDER BY g.title
        """)
        return [dict(record) for record in result]

def create_rich_text(greenlight: Dict) -> str:
    """Create rich text representation for embedding"""
    parts = []
    
    # Title
    parts.append(f"Title: {greenlight['title']}")
    
    # Platform
    if greenlight['streamer']:
        parts.append(f"Platform: {greenlight['streamer']}")
    
    # Genre
    if greenlight['genre']:
        parts.append(f"Genre: {greenlight['genre']}")
    
    # Format
    if greenlight['format']:
        parts.append(f"Format: {greenlight['format']}")
    
    # Episode count
    if greenlight['episode_count']:
        parts.append(f"Episodes: {greenlight['episode_count']}")
    
    # Executives
    if greenlight['executives']:
        execs = ', '.join(greenlight['executives'])
        parts.append(f"Greenlit by: {execs}")
    
    # Logline
    if greenlight['logline']:
        parts.append(f"Logline: {greenlight['logline']}")
    
    # Description
    if greenlight['description']:
        parts.append(f"Description: {greenlight['description']}")
    
    return ' | '.join(parts)

def update_pinecone_vector(greenlight: Dict):
    """Update or create Pinecone vector for greenlight"""
    
    # Create rich text
    rich_text = create_rich_text(greenlight)
    
    # Generate embedding
    embedding = embedding_model.encode(rich_text).tolist()
    
    # Create vector ID (use title as ID, normalized to ASCII)
    import unicodedata
    import re
    # Normalize to ASCII (remove accents, convert to closest ASCII)
    normalized = unicodedata.normalize('NFKD', greenlight['title'])
    ascii_title = normalized.encode('ASCII', 'ignore').decode('ASCII')
    # Replace spaces and special chars with underscores
    vector_id = re.sub(r'[^a-z0-9]+', '_', ascii_title.lower()).strip('_')
    
    # Create metadata
    metadata = {
        'title': greenlight['title'],
        'text': rich_text,
        'type': 'greenlight'
    }
    
    if greenlight['genre']:
        metadata['genre'] = greenlight['genre']
    if greenlight['streamer']:
        metadata['streamer'] = greenlight['streamer']
    if greenlight['format']:
        metadata['format'] = greenlight['format']
    if greenlight['executives']:
        metadata['executives'] = ', '.join(greenlight['executives'])
    
    # Upsert to Pinecone
    index.upsert(vectors=[(vector_id, embedding, metadata)])
    
    return vector_id

def main():
    """Main execution"""
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Get greenlights with metadata
        print("\nFetching greenlights from Neo4j...")
        greenlights = get_greenlights_with_metadata(driver)
        print(f"Found {len(greenlights)} greenlights")
        
        # Get initial Pinecone stats
        stats_before = index.describe_index_stats()
        print(f"\nPinecone stats before update:")
        print(f"  Total vectors: {stats_before['total_vector_count']}")
        
        # Update Pinecone
        print(f"\n=== UPDATING PINECONE VECTORS ===\n")
        
        updated_count = 0
        with_executives = 0
        with_loglines = 0
        with_descriptions = 0
        
        for idx, greenlight in enumerate(greenlights, 1):
            title = greenlight['title']
            
            # Update vector
            vector_id = update_pinecone_vector(greenlight)
            
            # Track enrichment
            has_exec = bool(greenlight['executives'])
            has_logline = bool(greenlight['logline'])
            has_desc = bool(greenlight['description'])
            
            if has_exec:
                with_executives += 1
            if has_logline:
                with_loglines += 1
            if has_desc:
                with_descriptions += 1
            
            # Print status
            enrichments = []
            if has_exec:
                enrichments.append(f"👔 {len(greenlight['executives'])} exec(s)")
            if has_logline:
                enrichments.append("📝 logline")
            if has_desc:
                enrichments.append("📄 description")
            
            status = ' + '.join(enrichments) if enrichments else "basic info only"
            print(f"[{idx}/{len(greenlights)}] {title}")
            print(f"  ✅ Updated: {vector_id}")
            print(f"  📊 {status}")
            
            updated_count += 1
            
            # Rate limiting
            if idx % 10 == 0:
                time.sleep(0.5)
        
        # Get final Pinecone stats
        time.sleep(2)  # Wait for index to update
        stats_after = index.describe_index_stats()
        
        print(f"\n=== UPDATE COMPLETE ===")
        print(f"Vectors updated: {updated_count}")
        print(f"With executives: {with_executives} ({with_executives/len(greenlights)*100:.1f}%)")
        print(f"With loglines: {with_loglines} ({with_loglines/len(greenlights)*100:.1f}%)")
        print(f"With descriptions: {with_descriptions} ({with_descriptions/len(greenlights)*100:.1f}%)")
        print(f"\nPinecone stats after update:")
        print(f"  Total vectors: {stats_after['total_vector_count']}")
        print(f"  Vectors added/updated: {stats_after['total_vector_count'] - stats_before['total_vector_count']}")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()

