"""
API Endpoints for Conversational RAG
Integrates with Mandate Wizard backend
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import os

from database.postgres_client import PostgresClient
from rag.engine import Engine
from conversational_rag.conversational_rag import ConversationalRAG


# Create blueprint
conversational_bp = Blueprint('conversational', __name__, url_prefix='/api/conversational')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_conversational_rag():
    """Get or create ConversationalRAG instance"""
    if not hasattr(get_conversational_rag, 'instance'):
        pg_client = PostgresClient()
        rag_engine = Engine()
        
        # LLM client (create OpenAI client directly)
        from openai import OpenAI
        llm_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Embedding client (same as LLM client)
        embedding_client = llm_client
        
        get_conversational_rag.instance = ConversationalRAG(
            pg_client,
            rag_engine,
            llm_client,
            embedding_client
        )
    
    return get_conversational_rag.instance


def require_auth(f):
    """Require authentication (placeholder)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implement actual auth
        # For now, get user_id from header or default
        user_id = request.headers.get('X-User-ID', 'anonymous')
        request.user_id = user_id
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ENDPOINTS
# ============================================================================

@conversational_bp.route('/start', methods=['POST'])
@require_auth
def start_conversation():
    """
    Start a new conversation
    
    POST /api/conversational/start
    {
        "session_id": "optional_session_id",
        "initial_goal": "optional_goal_description"
    }
    
    Returns:
    {
        "conversation_id": "uuid",
        "message": "Conversation started"
    }
    """
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id', request.headers.get('X-Session-ID', 'default'))
        initial_goal = data.get('initial_goal')
        
        rag = get_conversational_rag()
        conversation_id = rag.start_conversation(
            user_id=request.user_id,
            session_id=session_id,
            initial_goal=initial_goal
        )
        
        return jsonify({
            'conversation_id': conversation_id,
            'message': 'Conversation started successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conversational_bp.route('/query', methods=['POST'])
@require_auth
def process_query():
    """
    Process a user query in a conversation
    
    POST /api/conversational/query
    {
        "conversation_id": "uuid",
        "query": "user question"
    }
    
    Returns:
    {
        "answer": "generated answer",
        "turn_number": 1,
        "quality": {...},
        "repetition_score": 0.15,
        "metadata": {...}
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        conversation_id = data.get('conversation_id')
        query = data.get('query')
        
        if not conversation_id or not query:
            return jsonify({'error': 'conversation_id and query are required'}), 400
        
        rag = get_conversational_rag()
        result = rag.process_query(conversation_id, query)
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conversational_bp.route('/feedback', methods=['POST'])
@require_auth
def add_feedback():
    """
    Add user feedback
    
    POST /api/conversational/feedback
    {
        "conversation_id": "uuid",
        "turn_number": 1,  // optional, null for conversation-level
        "feedback_type": "thumbs_up|thumbs_down|rating|comment",
        "feedback_value": 1.0,  // 1.0 for thumbs_up, 0.0 for thumbs_down, 1-5 for rating
        "comment": "optional comment",
        "implicit_signals": {  // optional
            "dwell_time_ms": 15000,
            "scroll_depth": 0.8
        }
    }
    
    Returns:
    {
        "message": "Feedback recorded"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        conversation_id = data.get('conversation_id')
        feedback_type = data.get('feedback_type')
        feedback_value = data.get('feedback_value')
        
        if not all([conversation_id, feedback_type, feedback_value is not None]):
            return jsonify({'error': 'conversation_id, feedback_type, and feedback_value are required'}), 400
        
        rag = get_conversational_rag()
        rag.add_feedback(
            conversation_id=conversation_id,
            turn_number=data.get('turn_number'),
            feedback_type=feedback_type,
            feedback_value=float(feedback_value),
            comment=data.get('comment'),
            implicit_signals=data.get('implicit_signals')
        )
        
        return jsonify({'message': 'Feedback recorded successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conversational_bp.route('/conversation/<conversation_id>', methods=['GET'])
@require_auth
def get_conversation(conversation_id):
    """
    Get full conversation with all turns
    
    GET /api/conversational/conversation/{conversation_id}
    
    Returns:
    {
        "id": "uuid",
        "user_id": "user123",
        "user_goal": "...",
        "total_turns": 5,
        "avg_quality_score": 0.85,
        "turns": [...]
    }
    """
    try:
        rag = get_conversational_rag()
        conversation = rag.get_conversation(conversation_id)
        
        if not conversation:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify(conversation), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conversational_bp.route('/conversation/<conversation_id>/stats', methods=['GET'])
@require_auth
def get_conversation_stats(conversation_id):
    """
    Get conversation statistics
    
    GET /api/conversational/conversation/{conversation_id}/stats
    
    Returns:
    {
        "total_turns": 5,
        "avg_quality_score": 0.85,
        "goal_achieved": false,
        "feedback": {...},
        "unique_entities_covered": 12,
        "top_entities": [...]
    }
    """
    try:
        rag = get_conversational_rag()
        stats = rag.get_conversation_stats(conversation_id)
        
        if not stats:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@conversational_bp.route('/conversation/<conversation_id>/end', methods=['POST'])
@require_auth
def end_conversation(conversation_id):
    """
    End a conversation
    
    POST /api/conversational/conversation/{conversation_id}/end
    {
        "goal_achieved": true
    }
    
    Returns:
    {
        "message": "Conversation ended"
    }
    """
    try:
        data = request.get_json() or {}
        goal_achieved = data.get('goal_achieved', False)
        
        rag = get_conversational_rag()
        rag.end_conversation(conversation_id, goal_achieved)
        
        return jsonify({'message': 'Conversation ended successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# HEALTH CHECK
# ============================================================================

@conversational_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        rag = get_conversational_rag()
        return jsonify({
            'status': 'healthy',
            'service': 'conversational_rag',
            'version': '1.0.0-phase1'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500
