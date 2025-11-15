"""
Run Migration Script
Safely runs the priority fields migration with better error handling.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.postgres_client import PostgresClient

def run_migration():
    """Run the priority fields migration."""
    
    print("="*70)
    print("PRIORITY FIELDS MIGRATION")
    print("="*70)
    
    # Initialize PostgreSQL client
    try:
        pg = PostgresClient()
        print("✅ PostgreSQL connected")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {str(e)}")
        return False
    
    # Read migration file (v2 - safer version)
    migration_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'database/migrations/004_add_priority_fields_v2.sql'
    )
    
    try:
        with open(migration_path, 'r') as f:
            migration_sql = f.read()
        print(f"✅ Loaded migration file: {migration_path}")
    except Exception as e:
        print(f"❌ Failed to read migration file: {str(e)}")
        pg.close()
        return False
    
    # Execute migration
    print("\n🔄 Executing migration...")
    try:
        # Execute the migration
        pg.execute(migration_sql, fetch=False)
        print("✅ Migration executed successfully!")
        
        # Verify columns were added
        print("\n🔍 Verifying migration...")
        result = pg.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'entities'
            AND column_name IN ('priority_score', 'scope', 'seniority', 'last_embedded')
            ORDER BY column_name
        """)
        
        if result:
            print(f"\n✅ Found {len(result)} new columns:")
            for row in result:
                print(f"  - {row['column_name']} ({row['data_type']})")
                if row['column_default']:
                    print(f"    Default: {row['column_default']}")
        else:
            print("⚠️ No columns found - migration may have failed")
        
        # Check constraints
        print("\n🔍 Checking constraints...")
        constraints = pg.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'entities'
            AND constraint_name IN ('valid_priority_score', 'valid_scope', 'valid_seniority')
        """)
        
        if constraints:
            print(f"✅ Found {len(constraints)} constraints:")
            for row in constraints:
                print(f"  - {row['constraint_name']} ({row['constraint_type']})")
        
        # Check indexes
        print("\n🔍 Checking indexes...")
        indexes = pg.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'entities'
            AND indexname IN ('idx_entities_priority', 'idx_entities_scope', 
                             'idx_entities_seniority', 'idx_entities_last_embedded')
        """)
        
        if indexes:
            print(f"✅ Found {len(indexes)} indexes:")
            for row in indexes:
                print(f"  - {row['indexname']}")
        
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE!")
        print("="*70)
        
        pg.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        print("\nError details:")
        print(str(e))
        pg.close()
        return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
