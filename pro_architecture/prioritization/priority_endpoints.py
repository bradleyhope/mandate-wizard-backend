"""
Prioritization API Endpoints

REST API for accessing entity update priorities and schedules.
"""

from flask import Blueprint, jsonify, request
from .priority_engine import PriorityEngine, UpdatePriority
try:
    from database.postgres_client import PostgresClient
except ImportError:
    from ..database.postgres_client import PostgresClient

# Create blueprint
priority_bp = Blueprint('priority', __name__, url_prefix='/api/priority')

# Initialize priority engine (singleton)
priority_engine = PriorityEngine(
    demand_weight=0.5,
    freshness_weight=0.3,
    trending_weight=0.2,
    stale_threshold_days=30,
    critical_demand_threshold=10
)

def get_pg_client():
    """Get PostgreSQL client instance"""
    return PostgresClient()


@priority_bp.route('/batch', methods=['GET'])
def get_update_batch():
    """
    Get a batch of entities to update, prioritized by urgency.
    
    Query Parameters:
        limit (int): Maximum number of entities to return (default: 100)
        min_priority (str): Minimum priority tier (CRITICAL, HIGH, MEDIUM, LOW, DEFERRED)
        entity_type (str): Filter by entity type (optional)
    
    Returns:
        JSON with prioritized list of entities to update
    """
    try:
        # Get parameters
        limit = int(request.args.get('limit', 100))
        min_priority_str = request.args.get('min_priority', '').upper()
        entity_type = request.args.get('entity_type', '')
        
        # Validate min_priority
        min_priority = None
        if min_priority_str:
            try:
                min_priority = UpdatePriority[min_priority_str]
            except KeyError:
                return jsonify({
                    'error': f'Invalid priority tier: {min_priority_str}',
                    'valid_tiers': [p.name for p in UpdatePriority]
                }), 400
        
        # Build query
        query = """
            SELECT id, name, entity_type, demand_score, query_count,
                   last_queried_at, updated_at, created_at
            FROM entities
        """
        
        params = []
        
        if entity_type:
            query += " WHERE entity_type = %s"
            params.append(entity_type)
        
        query += " ORDER BY demand_score DESC, updated_at ASC"
        
        # Execute query
        entities = get_pg_client().execute(query, tuple(params) if params else None)
        
        if not entities:
            return jsonify({
                'batch': [],
                'total': 0,
                'limit': limit
            }), 200
        
        # Get prioritized batch
        batch = priority_engine.get_update_batch(
            entities, 
            batch_size=limit,
            min_priority=min_priority
        )
        
        return jsonify({
            'batch': batch,
            'total': len(batch),
            'limit': limit,
            'min_priority': min_priority.name if min_priority else None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@priority_bp.route('/critical', methods=['GET'])
def get_critical_entities():
    """
    Get entities that require immediate updates (CRITICAL priority).
    
    These are high-demand entities with stale data.
    
    Returns:
        JSON with list of critical entities
    """
    try:
        # Query entities with demand
        query = """
            SELECT id, name, entity_type, demand_score, query_count,
                   last_queried_at, updated_at, created_at
            FROM entities
            WHERE demand_score > 0
            ORDER BY demand_score DESC
        """
        
        entities = get_pg_client().execute(query)
        
        if not entities:
            return jsonify({
                'critical_entities': [],
                'total': 0
            }), 200
        
        # Get critical entities
        critical = priority_engine.get_critical_entities(entities)
        
        return jsonify({
            'critical_entities': critical,
            'total': len(critical),
            'criteria': {
                'min_demand_score': priority_engine.critical_demand_threshold,
                'stale_threshold_days': priority_engine.stale_threshold_days
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@priority_bp.route('/schedule', methods=['GET'])
def get_update_schedule():
    """
    Generate a multi-day update schedule based on priority.
    
    Query Parameters:
        daily_budget (int): Maximum entities to update per day (default: 500)
        entity_type (str): Filter by entity type (optional)
    
    Returns:
        JSON with day-by-day update schedule
    """
    try:
        # Get parameters
        daily_budget = int(request.args.get('daily_budget', 500))
        entity_type = request.args.get('entity_type', '')
        
        # Build query
        query = """
            SELECT id, name, entity_type, demand_score, query_count,
                   last_queried_at, updated_at, created_at
            FROM entities
        """
        
        params = []
        
        if entity_type:
            query += " WHERE entity_type = %s"
            params.append(entity_type)
        
        # Execute query
        entities = get_pg_client().execute(query, tuple(params) if params else None)
        
        if not entities:
            return jsonify({
                'schedule': {},
                'total_entities': 0,
                'total_days': 0,
                'daily_budget': daily_budget
            }), 200
        
        # Generate schedule
        schedule = priority_engine.generate_update_schedule(
            entities,
            daily_budget=daily_budget
        )
        
        # Calculate summary
        total_days = len(schedule)
        total_entities = sum(len(batch) for batch in schedule.values())
        
        return jsonify({
            'schedule': schedule,
            'total_entities': total_entities,
            'total_days': total_days,
            'daily_budget': daily_budget,
            'entity_type': entity_type if entity_type else 'all'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@priority_bp.route('/statistics', methods=['GET'])
def get_priority_statistics():
    """
    Get statistics about priority distribution across all entities.
    
    Query Parameters:
        entity_type (str): Filter by entity type (optional)
    
    Returns:
        JSON with priority distribution and statistics
    """
    try:
        # Get parameters
        entity_type = request.args.get('entity_type', '')
        
        # Build query
        query = """
            SELECT id, name, entity_type, demand_score, query_count,
                   last_queried_at, updated_at, created_at
            FROM entities
        """
        
        params = []
        
        if entity_type:
            query += " WHERE entity_type = %s"
            params.append(entity_type)
        
        # Execute query
        entities = get_pg_client().execute(query, tuple(params) if params else None)
        
        if not entities:
            return jsonify({
                'total_entities': 0,
                'avg_priority_score': 0,
                'tier_distribution': {},
                'top_10_entities': []
            }), 200
        
        # Get statistics
        stats = priority_engine.get_statistics(entities)
        
        # Add filter info
        stats['entity_type'] = entity_type if entity_type else 'all'
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@priority_bp.route('/entity/<entity_id>', methods=['GET'])
def get_entity_priority(entity_id):
    """
    Get priority information for a specific entity.
    
    Path Parameters:
        entity_id (str): Entity UUID
    
    Returns:
        JSON with entity priority details
    """
    try:
        # Query entity
        query = """
            SELECT id, name, entity_type, demand_score, query_count,
                   last_queried_at, updated_at, created_at
            FROM entities
            WHERE id = %s
        """
        
        entities = get_pg_client().execute(query, (entity_id,))
        
        if not entities:
            return jsonify({'error': 'Entity not found'}), 404
        
        entity = entities[0]
        
        # Calculate priority
        priority_score = priority_engine.calculate_priority_score(entity)
        priority_tier = priority_engine.classify_priority(entity)
        
        # Add priority info to entity
        entity['priority_score'] = priority_score
        entity['priority_tier'] = priority_tier.name
        entity['update_recommended'] = priority_tier.value <= UpdatePriority.HIGH.value
        
        return jsonify({
            'entity': entity,
            'priority_breakdown': {
                'demand_component': priority_engine._calculate_demand_score(entity),
                'freshness_component': priority_engine._calculate_freshness_score(entity),
                'trending_component': priority_engine._calculate_trending_score(entity)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
