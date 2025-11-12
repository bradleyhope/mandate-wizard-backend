"""
Demand Analytics API Endpoints

Flask blueprints for demand tracking and analytics APIs.
"""

from flask import Blueprint, jsonify, request
from .demand_analytics import DemandAnalytics

# Create blueprint
demand_bp = Blueprint('demand', __name__, url_prefix='/api/analytics/demand')


@demand_bp.route('/top', methods=['GET'])
def get_top_demand():
    """
    GET /api/analytics/demand/top
    
    Get top entities by demand score
    
    Query Parameters:
        limit (int): Maximum number of entities (default: 20, max: 100)
        entity_type (str): Filter by entity type
        min_score (int): Minimum demand score (default: 0)
    
    Returns:
        JSON with top demand entities
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        entity_type = request.args.get('entity_type')
        min_score = int(request.args.get('min_score', 0))
        
        # Get analytics
        analytics = DemandAnalytics()
        entities = analytics.get_top_demand_entities(
            limit=limit,
            entity_type=entity_type,
            min_score=min_score
        )
        
        return jsonify({
            'entities': entities,
            'total': len(entities),
            'limit': limit
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@demand_bp.route('/entity/<entity_id>', methods=['GET'])
def get_entity_demand(entity_id):
    """
    GET /api/analytics/demand/entity/:id
    
    Get demand details for a specific entity
    
    Returns:
        JSON with entity demand details
    """
    try:
        analytics = DemandAnalytics()
        entity = analytics.get_entity_demand_details(entity_id)
        
        if not entity:
            return jsonify({'error': 'Entity not found'}), 404
        
        return jsonify({'entity': entity})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@demand_bp.route('/stats', methods=['GET'])
def get_demand_stats():
    """
    GET /api/analytics/demand/stats
    
    Get overall demand statistics
    
    Returns:
        JSON with aggregate demand statistics
    """
    try:
        analytics = DemandAnalytics()
        stats = analytics.get_demand_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@demand_bp.route('/trending', methods=['GET'])
def get_trending():
    """
    GET /api/analytics/demand/trending
    
    Get entities with rapidly increasing demand
    
    Query Parameters:
        timeframe (str): Time period to analyze - 1d, 7d, 30d (default: 7d)
        limit (int): Maximum number of entities (default: 10, max: 50)
    
    Returns:
        JSON with trending entities and growth metrics
    """
    try:
        # Parse query parameters
        timeframe = request.args.get('timeframe', '7d')
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Convert timeframe to days
        timeframe_map = {'1d': 1, '7d': 7, '30d': 30}
        days = timeframe_map.get(timeframe, 7)
        
        # Get analytics
        analytics = DemandAnalytics()
        trending = analytics.get_trending_entities(
            timeframe_days=days,
            limit=limit
        )
        
        return jsonify({
            'trending': trending,
            'timeframe': timeframe,
            'total': len(trending)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@demand_bp.route('/stale', methods=['GET'])
def get_stale():
    """
    GET /api/analytics/demand/stale
    
    Get high-demand entities with outdated data
    
    Query Parameters:
        days_since_update (int): Minimum days since last update (default: 30)
        min_demand_score (int): Minimum demand score (default: 5)
        limit (int): Maximum number of entities (default: 20, max: 100)
    
    Returns:
        JSON with stale entities prioritized by demand
    """
    try:
        # Parse query parameters
        days_since_update = int(request.args.get('days_since_update', 30))
        min_demand_score = int(request.args.get('min_demand_score', 5))
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Get analytics
        analytics = DemandAnalytics()
        stale_entities = analytics.get_stale_high_demand_entities(
            days_since_update=days_since_update,
            min_demand_score=min_demand_score,
            limit=limit
        )
        
        return jsonify({
            'stale_entities': stale_entities,
            'total': len(stale_entities),
            'criteria': {
                'days_since_update': days_since_update,
                'min_demand_score': min_demand_score
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
