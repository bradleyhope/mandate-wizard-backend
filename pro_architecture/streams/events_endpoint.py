"""
API endpoints for publishing events to Redis Streams
"""

from flask import Blueprint, request, jsonify
from .redis_streams import get_streams_client


def create_events_endpoint():
    """Create Flask blueprint for events endpoints"""
    
    events_bp = Blueprint('events', __name__)
    
    @events_bp.route('/api/events/update-request', methods=['POST'])
    def publish_update_request():
        """
        Publish an UpdateRequest event to trigger data syncing
        
        Request body:
        {
            "entity_ids": ["uuid1", "uuid2", ...],
            "operation": "create" | "update" | "delete",
            "source": "newsletter" | "manual" | "api"
        }
        """
        data = request.get_json(force=True) or {}
        
        entity_ids = data.get('entity_ids', [])
        operation = data.get('operation', 'update')
        source = data.get('source', 'api')
        
        if not entity_ids:
            return jsonify({'error': 'entity_ids is required'}), 400
        
        if operation not in ['create', 'update', 'delete']:
            return jsonify({'error': 'operation must be create, update, or delete'}), 400
        
        try:
            streams_client = get_streams_client()
            event_id = streams_client.publish_update_request(
                entity_ids=entity_ids,
                operation=operation,
                source=source
            )
            
            return jsonify({
                'success': True,
                'event_id': event_id,
                'entity_count': len(entity_ids)
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @events_bp.route('/api/events/streams/info', methods=['GET'])
    def streams_info():
        """Get information about Redis Streams"""
        try:
            streams_client = get_streams_client()
            
            query_signals_info = streams_client.get_stream_info(
                streams_client.QUERY_SIGNAL_STREAM
            )
            update_requests_info = streams_client.get_stream_info(
                streams_client.UPDATE_REQUEST_STREAM
            )
            
            return jsonify({
                'query_signals': query_signals_info,
                'update_requests': update_requests_info,
                'health': streams_client.health_check()
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return events_bp
