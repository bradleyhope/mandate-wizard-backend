"""
Database Migration Endpoint for Mandate Wizard
Provides a simple HTTP endpoint to run database migrations
"""

import os
import psycopg2
from flask import jsonify

def run_migration(database_url: str, migration_file: str):
    """
    Run a SQL migration file.
    
    Args:
        database_url: PostgreSQL connection string
        migration_file: Path to SQL migration file
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Read migration file
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        
        # Execute migration
        cur.execute(sql)
        conn.commit()
        
        # Get table count
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'Migration completed successfully. {table_count} tables in database.',
            'migration_file': migration_file
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Migration failed: {str(e)}',
            'migration_file': migration_file
        }

def create_data_migration_endpoint(app):
    """
    Add data migration endpoint to Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/admin/migrate-data', methods=['GET', 'POST'])
    def migrate_data():
        """
        Migrate all data from Pinecone and Neo4j to PostgreSQL.
        
        GET /api/admin/migrate-data
        
        Returns:
            JSON response with migration summary
        """
        from database.migrate_data import run_full_migration
        
        try:
            result = run_full_migration()
            status_code = 200 if result.get('success') else 500
            return jsonify(result), status_code
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Migration failed: {str(e)}'
            }), 500

def create_migration_endpoint(app):
    """
    Add migration endpoint to Flask app.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/admin/migrate', methods=['GET', 'POST'])
    def migrate_database():
        """
        Run database migration.
        
        GET /api/admin/migrate
        
        Returns:
            JSON response with migration status
        """
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            return jsonify({
                'success': False,
                'message': 'DATABASE_URL environment variable not set'
            }), 500
        
        # Path to migrations directory
        migrations_dir = os.path.join(
            os.path.dirname(__file__),
            'migrations'
        )
        
        # Run all migrations in order
        migration_files = [
            '001_initial_schema.sql',
            '002_add_entity_types.sql',
            '003_remove_entity_type_constraint.sql'
        ]
        
        results = []
        for migration_file in migration_files:
            file_path = os.path.join(migrations_dir, migration_file)
            if os.path.exists(file_path):
                result = run_migration(database_url, file_path)
                results.append(result)
                if not result['success']:
                    # Stop on first failure
                    break
        
        # Aggregate results
        all_success = all(r['success'] for r in results)
        result = {
            'success': all_success,
            'message': f'Ran {len(results)} migrations. All successful.' if all_success else 'Some migrations failed.',
            'migrations': results
        }
        
        status_code = 200 if result['success'] else 500
        return jsonify(result), status_code
    
    @app.route('/api/admin/db-status', methods=['GET'])
    def database_status():
        """
        Check database connection and table status.
        
        GET /api/admin/db-status
        
        Returns:
            JSON response with database status
        """
        database_url = os.getenv('DATABASE_URL')
        
        if not database_url:
            return jsonify({
                'connected': False,
                'message': 'DATABASE_URL not configured'
            }), 500
        
        try:
            conn = psycopg2.connect(database_url)
            cur = conn.cursor()
            
            # Get table list
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cur.fetchall()]
            
            # Get row counts
            counts = {}
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            return jsonify({
                'connected': True,
                'tables': tables,
                'row_counts': counts,
                'message': f'Database connected. {len(tables)} tables found.'
            }), 200
            
        except Exception as e:
            return jsonify({
                'connected': False,
                'message': f'Database connection failed: {str(e)}'
            }), 500
