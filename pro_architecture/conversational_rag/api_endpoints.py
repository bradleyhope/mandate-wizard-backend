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
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Error in endpoint: {error_msg}")
        print(f"Traceback:\n{traceback_str}")
        return jsonify({
            'error': error_msg if error_msg else 'Unknown error',
            'type': type(e).__name__
        }), 500


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
        
        try:
            # Try conversational RAG first
            # Note: Render has 30s timeout, so operations must complete quickly
            result = rag.process_query(conversation_id, query)
            return jsonify(result), 200
        
        except Exception as conv_error:
            # If conversational RAG fails, fallback to regular RAG
            import traceback
            print(f"⚠️ Conversational RAG failed, falling back to regular RAG")
            print(f"Error: {str(conv_error)}")
            print(f"Traceback:\n{traceback.format_exc()}")
            
            try:
                # Use regular RAG engine as fallback (from existing conversational RAG instance)
                fallback_result = rag.rag_engine.answer(query)
                
                # Format response to match conversational format
                response = {
                    'answer': fallback_result.get('final_answer', fallback_result.get('answer', 'Unable to process query')),
                    'turn_number': 0,  # Indicate fallback mode
                    'quality_score': None,
                    'repetition_score': None,
                    'entities_mentioned': [],
                    'followups': fallback_result.get('follow_up_questions', []),
                    'sources': fallback_result.get('sources', []),
                    'fallback_mode': True,
                    'fallback_reason': str(conv_error)
                }
                
                return jsonify(response), 200
            
            except Exception as fallback_error:
                # Even fallback failed - return a helpful message
                print(f"❌ Fallback RAG also failed: {str(fallback_error)}")
                print(f"Traceback:\n{traceback.format_exc()}")
                
                # Return a user-friendly response instead of error
                return jsonify({
                    'answer': "I'm having trouble processing your question right now. Could you try rephrasing it or asking a different question?",
                    'turn_number': 0,
                    'quality_score': None,
                    'repetition_score': None,
                    'entities_mentioned': [],
                    'followups': [],
                    'sources': [],
                    'fallback_mode': True,
                    'error_occurred': True
                }), 200  # Return 200 with helpful message, not 500
    
    except Exception as e:
        # Outer exception handler - should rarely be hit
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Critical error in endpoint: {error_msg}")
        print(f"Traceback:\n{traceback_str}")
        
        # Still return a helpful message, not a raw error
        return jsonify({
            'answer': "I'm experiencing technical difficulties. Please try again in a moment.",
            'turn_number': 0,
            'quality_score': None,
            'repetition_score': None,
            'entities_mentioned': [],
            'followups': [],
            'sources': [],
            'error_occurred': True
        }), 200  # Return 200 with message, not 500


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
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Error in endpoint: {error_msg}")
        print(f"Traceback:\n{traceback_str}")
        return jsonify({
            'error': error_msg if error_msg else 'Unknown error',
            'type': type(e).__name__
        }), 500


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
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Error in endpoint: {error_msg}")
        print(f"Traceback:\n{traceback_str}")
        return jsonify({
            'error': error_msg if error_msg else 'Unknown error',
            'type': type(e).__name__
        }), 500


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
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Error in endpoint: {error_msg}")
        print(f"Traceback:\n{traceback_str}")
        return jsonify({
            'error': error_msg if error_msg else 'Unknown error',
            'type': type(e).__name__
        }), 500


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
        import traceback
        error_msg = str(e)
        traceback_str = traceback.format_exc()
        print(f"❌ Error in endpoint: {error_msg}")
        print(f"Traceback:\n{traceback_str}")
        return jsonify({
            'error': error_msg if error_msg else 'Unknown error',
            'type': type(e).__name__
        }), 500


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


@conversational_bp.route('/debug/query', methods=['POST'])
@require_auth
def debug_query():
    """
    DEBUG endpoint - returns full error details
    
    POST /api/conversational/debug/query
    {
        "conversation_id": "uuid",
        "query": "user question"
    }
    
    Returns full error stack traces for debugging
    """
    import traceback
    
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    query = data.get('query')
    
    debug_info = {
        'conversation_id': conversation_id,
        'query': query,
        'steps': []
    }
    
    try:
        rag = get_conversational_rag()
        debug_info['steps'].append({'step': 'get_conversational_rag', 'status': 'success'})
        
        try:
            result = rag.process_query(conversation_id, query)
            debug_info['steps'].append({'step': 'process_query', 'status': 'success'})
            debug_info['result'] = result
            return jsonify(debug_info), 200
            
        except Exception as conv_error:
            debug_info['steps'].append({
                'step': 'process_query',
                'status': 'failed',
                'error': str(conv_error),
                'error_type': type(conv_error).__name__,
                'traceback': traceback.format_exc()
            })
            
            try:
                fallback_result = rag.rag_engine.answer(query)
                debug_info['steps'].append({'step': 'fallback_rag', 'status': 'success'})
                debug_info['fallback_result'] = fallback_result
                return jsonify(debug_info), 200
                
            except Exception as fallback_error:
                debug_info['steps'].append({
                    'step': 'fallback_rag',
                    'status': 'failed',
                    'error': str(fallback_error),
                    'error_type': type(fallback_error).__name__,
                    'traceback': traceback.format_exc()
                })
                return jsonify(debug_info), 200
                
    except Exception as e:
        debug_info['steps'].append({
            'step': 'initialization',
            'status': 'failed',
            'error': str(e),
            'error_type': type(e).__name__,
            'traceback': traceback.format_exc()
        })
        return jsonify(debug_info), 200
