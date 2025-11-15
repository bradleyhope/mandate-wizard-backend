"""
Populate Priority Scores Script
Calculates and updates priority_score, scope, and seniority for all entities in PostgreSQL.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_client import PostgresClient
from utils.priority_scoring import calculate_all_scores

def populate_priority_scores():
    """Calculate and populate priority scores for all entities."""
    
    print("="*70)
    print("POPULATE PRIORITY SCORES")
    print("="*70)
    
    # Initialize PostgreSQL client
    pg = PostgresClient()
    
    # Get all entities
    print("\n📊 Fetching all entities...")
    entities = pg.execute("""
        SELECT id, entity_type, name, slug, attributes, query_count
        FROM entities
    """)
    
    print(f"✅ Found {len(entities)} entities")
    
    # Calculate scores for each entity
    print("\n🔢 Calculating priority scores...")
    
    updated_count = 0
    person_count = 0
    
    for entity in entities:
        # Only calculate for people
        if entity['entity_type'] != 'person':
            continue
        
        person_count += 1
        
        # Calculate scores
        scores = calculate_all_scores(entity)
        
        # Update entity
        pg.execute("""
            UPDATE entities
            SET priority_score = %s,
                scope = %s,
                seniority = %s
            WHERE id = %s
        """, (
            scores['priority_score'],
            scores['scope'],
            scores['seniority'],
            entity['id']
        ), fetch=False)
        
        updated_count += 1
        
        # Print progress every 50 entities
        if updated_count % 50 == 0:
            print(f"  Processed {updated_count}/{person_count} people...")
    
    print(f"\n✅ Updated {updated_count} people with priority scores")
    
    # Show statistics
    print("\n📊 Priority Score Statistics:")
    stats = pg.execute("""
        SELECT 
            seniority,
            scope,
            COUNT(*) as count,
            AVG(priority_score) as avg_score,
            MIN(priority_score) as min_score,
            MAX(priority_score) as max_score
        FROM entities
        WHERE entity_type = 'person'
        GROUP BY seniority, scope
        ORDER BY avg_score DESC
    """)
    
    print("\n{:<15} {:<12} {:<8} {:<12} {:<10} {:<10}".format(
        "Seniority", "Scope", "Count", "Avg Score", "Min", "Max"
    ))
    print("-" * 70)
    
    for row in stats:
        print("{:<15} {:<12} {:<8} {:<12.1f} {:<10} {:<10}".format(
            row['seniority'],
            row['scope'],
            row['count'],
            row['avg_score'] or 0,
            row['min_score'] or 0,
            row['max_score'] or 0
        ))
    
    # Show top 10 highest priority people
    print("\n🏆 Top 10 Highest Priority People:")
    top_people = pg.execute("""
        SELECT name, attributes->>'title' as title, priority_score, scope, seniority
        FROM entities
        WHERE entity_type = 'person'
        ORDER BY priority_score DESC
        LIMIT 10
    """)
    
    print("\n{:<30} {:<40} {:<8} {:<10} {:<10}".format(
        "Name", "Title", "Score", "Scope", "Seniority"
    ))
    print("-" * 100)
    
    for person in top_people:
        print("{:<30} {:<40} {:<8} {:<10} {:<10}".format(
            person['name'][:29],
            (person['title'] or 'N/A')[:39],
            person['priority_score'],
            person['scope'],
            person['seniority']
        ))
    
    print("\n" + "="*70)
    print("✅ Priority scores populated successfully!")
    print("="*70)
    
    pg.close()


if __name__ == '__main__':
    populate_priority_scores()
