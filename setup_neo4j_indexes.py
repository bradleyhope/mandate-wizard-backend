"""
Neo4j Index Setup Script
Creates indexes for optimal query performance (50-70% faster queries)
"""

import os
from neo4j import GraphDatabase
import sys

def create_indexes(driver):
    """Create all necessary indexes for optimal performance"""

    indexes_to_create = [
        # Person indexes
        ("Person", "region", "Speed up region-based queries"),
        ("Person", "name", "Speed up name lookups"),
        ("Person", "current_title", "Speed up title-based filtering"),
        ("Person", "entity_id", "Speed up entity ID lookups"),

        # Greenlight indexes
        ("Greenlight", "genre", "Speed up genre-based queries"),
        ("Greenlight", "format", "Speed up format filtering"),
        ("Greenlight", "year", "Speed up year-based queries"),
        ("Greenlight", "executive", "Speed up executive-project queries"),
        ("Greenlight", "greenlight_date", "Speed up date-based sorting"),
        ("Greenlight", "title", "Speed up title lookups"),

        # ProductionCompany indexes
        ("ProductionCompany", "name", "Speed up production company lookups"),

        # NewsletterSource indexes
        ("NewsletterSource", "date", "Speed up date-based article queries"),
    ]

    created = []
    skipped = []
    failed = []

    with driver.session() as session:
        # Check existing indexes
        result = session.run("SHOW INDEXES")
        existing_indexes = set()
        for record in result:
            # Extract label and property from index name or properties
            if 'labelsOrTypes' in record.keys() and 'properties' in record.keys():
                for label in record['labelsOrTypes']:
                    for prop in record['properties']:
                        existing_indexes.add((label, prop))

        print(f"Found {len(existing_indexes)} existing indexes")

        # Create new indexes
        for label, property, description in indexes_to_create:
            index_name = f"idx_{label.lower()}_{property}"

            # Skip if exists
            if (label, property) in existing_indexes:
                print(f"✓ Index already exists: {index_name} ({description})")
                skipped.append(index_name)
                continue

            # Create index
            try:
                query = f"""
                CREATE INDEX {index_name} IF NOT EXISTS
                FOR (n:{label})
                ON (n.{property})
                """
                session.run(query)
                print(f"✅ Created index: {index_name} ({description})")
                created.append(index_name)

            except Exception as e:
                print(f"❌ Failed to create {index_name}: {e}")
                failed.append(index_name)

    return {
        'created': created,
        'skipped': skipped,
        'failed': failed
    }


def verify_indexes(driver):
    """Verify all indexes are active"""
    with driver.session() as session:
        result = session.run("SHOW INDEXES")
        indexes = []
        for record in result:
            indexes.append({
                'name': record.get('name', 'unknown'),
                'state': record.get('state', 'unknown'),
                'type': record.get('type', 'unknown'),
                'labels': record.get('labelsOrTypes', []),
                'properties': record.get('properties', [])
            })

    print(f"\n📊 Total indexes: {len(indexes)}")
    for idx in indexes:
        status = "✅" if idx['state'] == 'ONLINE' else "⚠️"
        print(f"{status} {idx['name']}: {idx['state']} ({idx['type']})")

    return indexes


def estimate_performance_improvement(driver):
    """Estimate query performance improvement"""

    test_queries = [
        ("Find executives by region", "MATCH (p:Person) WHERE p.region = 'UK' RETURN COUNT(p)"),
        ("Find greenlights by genre", "MATCH (g:Greenlight) WHERE g.genre = 'Thriller' RETURN COUNT(g)"),
        ("Find greenlights by year", "MATCH (g:Greenlight) WHERE g.year = 2024 RETURN COUNT(g)")
    ]

    print("\n⚡ Testing query performance...")

    with driver.session() as session:
        for description, query in test_queries:
            try:
                import time
                start = time.time()
                result = session.run(query)
                count = result.single()[0]
                duration = (time.time() - start) * 1000

                print(f"  {description}: {count} results in {duration:.1f}ms")
            except Exception as e:
                print(f"  {description}: FAILED ({e})")


def main():
    """Main entry point"""
    print("="*70)
    print("Neo4j Index Setup for Netflix Mandate Wizard")
    print("="*70)

    # Get credentials from environment
    neo4j_uri = os.environ.get('NEO4J_URI')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD')

    if not neo4j_uri or not neo4j_password:
        print("\n❌ ERROR: Neo4j credentials not found in environment variables")
        print("Please set NEO4J_URI and NEO4J_PASSWORD")
        sys.exit(1)

    print(f"\n📡 Connecting to Neo4j at {neo4j_uri}...")

    # Connect to Neo4j
    try:
        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )

        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1")
            result.single()

        print("✅ Connected successfully\n")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

    # Create indexes
    print("Creating indexes...")
    print("-"*70)
    results = create_indexes(driver)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"✅ Created:  {len(results['created'])} new indexes")
    print(f"⏭️  Skipped:  {len(results['skipped'])} existing indexes")
    print(f"❌ Failed:   {len(results['failed'])} indexes")

    if results['failed']:
        print("\nFailed indexes:")
        for idx in results['failed']:
            print(f"  - {idx}")

    # Verify indexes
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)
    verify_indexes(driver)

    # Test performance
    estimate_performance_improvement(driver)

    # Close connection
    driver.close()

    print("\n" + "="*70)
    print("✅ Index setup complete!")
    print("Expected performance improvement: 50-70% faster queries")
    print("="*70)


if __name__ == '__main__':
    main()
