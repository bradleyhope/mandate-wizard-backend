"""
Admin endpoint for viewing query logs
"""

from flask import Blueprint, jsonify, request, send_file, render_template
from query_logger import get_query_logger
import os

admin_bp = Blueprint('admin', __name__, template_folder='templates')

@admin_bp.route('/admin/dashboard')
def admin_dashboard():
    """Render admin dashboard HTML page"""
    return render_template('admin_dashboard.html')
query_logger = get_query_logger()

@admin_bp.route('/admin/logs', methods=['GET'])
def get_logs():
    """Get recent query logs"""
    limit = request.args.get('limit', 100, type=int)
    user_email = request.args.get('user_email', None)
    
    logs = query_logger.get_recent_logs(limit=limit, user_email=user_email)
    
    return jsonify({
        'success': True,
        'count': len(logs),
        'logs': logs
    })

@admin_bp.route('/admin/logs/session/<session_id>', methods=['GET'])
def get_session_logs(session_id):
    """Get all logs for a specific session"""
    logs = query_logger.get_session_logs(session_id)
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'count': len(logs),
        'logs': logs
    })

@admin_bp.route('/admin/logs/stats', methods=['GET'])
def get_stats():
    """Get usage statistics"""
    stats = query_logger.get_stats()
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@admin_bp.route('/admin/logs/export', methods=['GET'])
def export_logs():
    """Export logs to JSON file"""
    limit = request.args.get('limit', None, type=int)
    output_file = "/tmp/query_logs_export.json"
    
    count = query_logger.export_to_json(output_file, limit=limit)
    
    return send_file(
        output_file,
        mimetype='application/json',
        as_attachment=True,
        download_name=f'mandate_wizard_logs_{count}_queries.json'
    )

