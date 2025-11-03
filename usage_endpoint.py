"""
Usage Statistics Endpoint
Add this to app.py to expose usage stats
"""

from flask import jsonify, request
from rate_limiter import rate_limiter

def add_usage_endpoints(app):
    """Add usage statistics endpoints to Flask app"""
    
    @app.route('/api/usage/stats', methods=['GET'])
    def get_usage_stats():
        """Get usage statistics for current user"""
        email = request.args.get('email')
        
        if not email:
            return jsonify({
                'error': 'Email required',
                'success': False
            }), 400
        
        stats = rate_limiter.get_usage_stats(email)
        
        if not stats:
            return jsonify({
                'error': 'No usage data found',
                'success': False
            }), 404
        
        return jsonify({
            'stats': stats,
            'success': True
        })
    
    @app.route('/api/usage/all', methods=['GET'])
    def get_all_usage():
        """Get all usage statistics (admin only)"""
        # TODO: Add admin authentication
        
        return jsonify({
            'usage_data': rate_limiter.usage_data,
            'success': True
        })

