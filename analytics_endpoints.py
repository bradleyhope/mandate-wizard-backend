"""
Analytics Dashboard Endpoints
Add these to app.py to expose analytics data
"""

from flask import jsonify, request
from chat_analytics import chat_analytics

def add_analytics_endpoints(app):
    """Add analytics endpoints to Flask app"""
    
    @app.route('/api/analytics/summary', methods=['GET'])
    def get_analytics_summary():
        """Get summary statistics"""
        days = request.args.get('days', 7, type=int)
        
        try:
            summary = chat_analytics.get_summary_stats(days=days)
            return jsonify({
                'summary': summary,
                'success': True
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    
    @app.route('/api/analytics/user/<email>', methods=['GET'])
    def get_user_analytics(email):
        """Get analytics for specific user"""
        try:
            journey = chat_analytics.get_user_journey(email)
            return jsonify({
                'journey': journey,
                'success': True
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    
    @app.route('/api/analytics/drop-off', methods=['GET'])
    def get_drop_off_analysis():
        """Get drop-off analysis"""
        try:
            analysis = chat_analytics.get_drop_off_analysis()
            return jsonify({
                'analysis': analysis,
                'success': True
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    
    @app.route('/api/analytics/export', methods=['GET'])
    def export_analytics():
        """Export all analytics data"""
        try:
            return jsonify({
                'data': chat_analytics.analytics_data,
                'success': True
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'success': False
            }), 500
    
    @app.route('/api/analytics/patterns', methods=['GET'])
    def get_patterns():
        """Get pattern analysis"""
        try:
            patterns = chat_analytics.analytics_data['patterns']
            return jsonify({
                'patterns': {
                    'topics': dict(patterns['topics']),
                    'intents': dict(patterns['intents']),
                    'keywords': dict(sorted(
                        patterns['keywords'].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:50])  # Top 50 keywords
                },
                'success': True
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'success': False
            }), 500

