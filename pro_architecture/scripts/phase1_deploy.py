"""
Phase 1 Deployment Script
Runs all Phase 1 tasks in sequence:
1. Run PostgreSQL migration
2. Calculate and populate priority scores
3. Re-embed all executives with rich text
"""

import os
import sys
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_client import PostgresClient

def run_migration():
    """Run the PostgreSQL migration to add priority fields."""
    print("\n" + "="*70)
    print("STEP 1: RUN POSTGRESQL MIGRATION")
    print("="*70)
    
    pg = PostgresClient()
    
    # Read migration file
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database/migrations/004_add_priority_fields.sql'
    )
    
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    # Execute migration
    try:
        pg.execute(migration_sql, fetch=False)
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        print("Note: If columns already exist, this is expected.")
    
    pg.close()


def populate_scores():
    """Run the priority score population script."""
    print("\n" + "="*70)
    print("STEP 2: POPULATE PRIORITY SCORES")
    print("="*70)
    
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'populate_priority_scores.py'
    )
    
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ Priority score population failed with code {result.returncode}")
        return False
    
    return True


def reembed_entities():
    """Run the re-embedding script."""
    print("\n" + "="*70)
    print("STEP 3: RE-EMBED EXECUTIVES")
    print("="*70)
    
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'reembed_executives.py'
    )
    
    # Re-embed people first (highest priority)
    print("\n🔄 Re-embedding people...")
    result = subprocess.run(
        [sys.executable, script_path, '--entity-type', 'person', '--batch-size', '50'],
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"❌ Re-embedding failed with code {result.returncode}")
        return False
    
    return True


def main():
    """Run all Phase 1 deployment steps."""
    print("="*70)
    print("PHASE 1 DEPLOYMENT: PRIORITY SCORES & RE-EMBEDDING")
    print("="*70)
    print("\nThis script will:")
    print("1. Add priority_score, scope, seniority fields to PostgreSQL")
    print("2. Calculate and populate priority scores for all entities")
    print("3. Re-embed all executives with rich text in Pinecone")
    print("\nEstimated time: 10-30 minutes (depending on number of entities)")
    
    response = input("\nProceed? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Deployment cancelled")
        return
    
    # Step 1: Run migration
    run_migration()
    
    # Step 2: Populate scores
    if not populate_scores():
        print("\n❌ Deployment failed at Step 2")
        return
    
    # Step 3: Re-embed
    if not reembed_entities():
        print("\n❌ Deployment failed at Step 3")
        return
    
    # Success!
    print("\n" + "="*70)
    print("✅ PHASE 1 DEPLOYMENT COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. Update retrieval logic to use priority scores for boosting")
    print("2. Test with documentary queries")
    print("3. Deploy to production")
    print("\nRun: python3 scripts/test_retrieval.py")


if __name__ == '__main__':
    main()
