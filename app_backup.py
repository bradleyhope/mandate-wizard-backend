#!/usr/bin/env python3
"""
Mandate Wizard - Production Web Application
HybridRAG Query Engine with Pinecone + Neo4j
"""

from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
from flask_cors import CORS
import os
import secrets
import time
from hybridrag_engine_pinecone import HybridRAGEnginePinecone
import json
from executive_deep_dive import ExecutiveDeepDive
from pattern_analysis import PatternAnalyzer
from recent_mandates import RecentMandatesTracker
from ghost_auth import ghost_auth, require_paid_subscription, require_member
from rate_limiter import rate_limiter, require_rate_limit
from input_validator import input_validator, validate_input
from chat_analytics import chat_analytics
from query_logger import get_query_logger
from resource_manager import get_resource_manager

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Enable CORS for specific origins only (SECURITY FIX)
ALLOWED_ORIGINS = [
    "https://3000-iy1gh94d7s437eutwzpcu-aa64bff1.manusvm.computer",
    "https://predeploy-*.manus.space",
    "https://*.manus.space",
    "http://localhost:3000",  # Development
]
CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS, "supports_credentials": True}})

# Conversation memory: session_id -> list of (question, answer, context)
conversation_memory = {}

# Initialize HybridRAG engine
print("Initializing Mandate Wizard HybridRAG Engine...")

# Database credentials (from starter package)
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1')
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

NEO4J_URI = os.environ.get('NEO4J_URI', 'neo4j+s://0dd3462a.databases.neo4j.io')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg')

# Initialize engine
engine = HybridRAGEnginePinecone(
    pinecone_api_key=PINECONE_API_KEY,
    pinecone_index_name=PINECONE_INDEX_NAME,
    neo4j_uri=NEO4J_URI,
    neo4j_user=NEO4J_USER,
    neo4j_password=NEO4J_PASSWORD
)

# Initialize executive deep dive
deep_dive = ExecutiveDeepDive(
    neo4j_uri=NEO4J_URI,
    neo4j_user=NEO4J_USER,
    neo4j_password=NEO4J_PASSWORD
)

# Initialize pattern analyzer
pattern_analyzer = PatternAnalyzer(
    neo4j_uri=NEO4J_URI,
    neo4j_user=NEO4J_USER,
    neo4j_password=NEO4J_PASSWORD
)

# Initialize recent mandates tracker
recent_mandates = RecentMandatesTracker(
    neo4j_uri=NEO4J_URI,
    neo4j_user=NEO4J_USER,
    neo4j_password=NEO4J_PASSWORD
)

# Initialize query logger
query_logger = get_query_logger()
print("✓ Query logging enabled")

# Initialize resource manager
resource_manager = get_resource_manager()
print("✓ Resource manager initialized")

print("✓ Mandate Wizard ready!")

@app.route('/')
def index():
    """Serve the main interface"""
    return render_template('index.html')

@app.route('/test-api')
def test_api():
    """Simple API connection test page"""
    return render_template('test_api.html')

@app.route('/auth/check', methods=['POST'])
def check_auth():
    """Check if user is authenticated and has valid subscription"""
    data = request.json
    email = data.get('email', '')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    try:
        status = ghost_auth.check_subscription_status(email)
        return jsonify({
            'authenticated': status['is_member'],
            'subscription_status': status['status'],
            'is_paid': status['is_paid'],
            'member_since': status['member_since'],
            'name': status.get('name'),
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/auth/magic-link', methods=['POST'])
def send_magic_link():
    """Send magic link for passwordless login"""
    data = request.json
    email = data.get('email', '')
    
    if not email:
        return jsonify({'error': 'Email required'}), 400
    
    # DEV BYPASS: For beta testing, simulate magic link for test email
    if email == "bradley@projectbrazen.com":
        # Generate a test token
        import jwt
        test_token = jwt.encode(
            {'email': email, 'sub': email, 'exp': int(time.time()) + 3600},
            app.secret_key,
            algorithm='HS256'
        )
        print(f"[DEV] Magic link token for {email}: {test_token}")
        print(f"[DEV] Test URL: http://localhost:3000/?token={test_token}")
        return jsonify({
            'success': True,
            'message': 'Magic link sent to your email',
            'dev_token': test_token  # Only for dev testing
        })
    
    try:
        result = ghost_auth.send_magic_link(email)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/auth/verify-token', methods=['POST'])
def verify_token():
    """Verify Ghost magic link token and create session"""
    data = request.json
    token = data.get('token', '')
    
    if not token:
        return jsonify({'error': 'Token required'}), 400
    
    try:
        # For now, extract email from token and verify subscription
        # In production, you'd verify the Ghost token signature
        import jwt
        decoded = jwt.decode(token, options={"verify_signature": False})
        email = decoded.get('sub') or decoded.get('email')
        
        if not email:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Check subscription status
        status = ghost_auth.check_subscription_status(email)
        
        if not status['is_paid']:
            return jsonify({
                'error': 'Paid subscription required',
                'is_paid': False,
                'success': False
            }), 403
        
        # Create session token
        session_token = secrets.token_urlsafe(32)
        session['user_email'] = email
        session['session_token'] = session_token
        session['subscription_status'] = status
        
        return jsonify({
            'success': True,
            'email': email,
            'session_token': session_token,
            'subscription_status': status['status'],
            'is_paid': status['is_paid'],
            'name': status.get('name')
        })
        
    except Exception as e:
        print(f"Token verification error: {e}")
        return jsonify({'error': 'Invalid or expired token', 'success': False}), 401

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout and clear session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# ============================================
# ANALYTICS ENDPOINTS
# ============================================

@app.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get summary statistics"""
    days = request.args.get('days', 7, type=int)
    try:
        summary = chat_analytics.get_summary_stats(days=days)
        return jsonify({'summary': summary, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/analytics/user/<email>', methods=['GET'])
def get_user_analytics(email):
    """Get analytics for specific user"""
    try:
        journey = chat_analytics.get_user_journey(email)
        return jsonify({'journey': journey, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

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
                )[:50])
            },
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/ask', methods=['POST'])
@app.route('/query', methods=['POST'])
@validate_input
@require_rate_limit
@require_paid_subscription
def ask():
    """Handle question and return answer with conversation memory"""
    start_time = time.time()
    data = request.json
    question = data.get('question', '')
    session_id = data.get('session_id', 'default')
    email = data.get('email', 'unknown')
    subscription_status = data.get('subscription_status', 'unknown')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Get conversation history
        if session_id not in conversation_memory:
            conversation_memory[session_id] = []
        
        history = conversation_memory[session_id][-20:]  # Last 20 exchanges for deep context
        
        # Query the HybridRAG engine
        result = engine.query(question, conversation_history=history)
        
        # Cleanup resources if needed
        resource_manager.cleanup_if_needed()
        
        # Store in conversation memory
        conversation_memory[session_id].append({
            'question': question,
            'answer': result['answer'],
            'intent': result.get('intent', 'HYBRID'),
            'context': result.get('context', {})
        })
        
        # Limit memory to last 30 exchanges per session (keep 20 for context + 10 buffer)
        if len(conversation_memory[session_id]) > 30:
            conversation_memory[session_id] = conversation_memory[session_id][-30:]
        
        # Log analytics
        response_time = time.time() - start_time
        chat_analytics.log_query(
            email=email,
            question=question,
            answer=result['answer'],
            metadata={
                'response_time': response_time,
                'success': True,
                'intent': result.get('intent', 'HYBRID'),
                'session_id': session_id,
                'subscription_status': subscription_status,
                'tokens_used': len(question.split()) + len(result['answer'].split()),  # Rough estimate
                'cost': 0.02  # Rough estimate
            }
        )
        
        # Log detailed query for beta analysis
        query_logger.log_query(
            user_email=email,
            question=question,
            answer=result['answer'],
            intent=result.get('intent', 'HYBRID'),
            followups=result.get('followups', []),
            resources=result.get('resources', []),
            response_time_ms=int(response_time * 1000),
            session_id=session_id,
            vector_count=result.get('context', {}).get('vector_count', 0),
            graph_count=result.get('context', {}).get('graph_count', 0),
            token_count=len(question.split()) + len(result['answer'].split()),
            metadata={
                'subscription_status': subscription_status,
                'conversation_length': len(conversation_memory.get(session_id, [])),
                'has_history': len(history) > 0
            }
        )
        
        return jsonify({
            'answer': result['answer'],
            'follow_up_questions': result.get('followups', []),  # Engine returns 'followups'
            'resources': result.get('resources', []),
            'intent': result.get('intent', 'HYBRID'),
            'session_id': session_id,
            'success': True
        })
        
    except TimeoutError as e:
        print(f"[ERROR] Query timeout after {time.time() - start_time:.1f}s: {e}")
        
        # Log timeout
        response_time = time.time() - start_time
        chat_analytics.log_query(
            email=email,
            question=question,
            answer=None,
            metadata={
                'response_time': response_time,
                'success': False,
                'error': 'timeout',
                'session_id': session_id,
                'subscription_status': subscription_status
            }
        )
        
        return jsonify({
            'error': 'Query timed out. Please try a simpler question or try again later.',
            'success': False,
            'error_type': 'timeout'
        }), 504
    
    except ValueError as e:
        # GPT-5 API errors or validation errors
        error_msg = str(e)
        print(f"[ERROR] Validation/API error: {error_msg}")
        
        response_time = time.time() - start_time
        chat_analytics.log_query(
            email=email,
            question=question,
            answer=None,
            metadata={
                'response_time': response_time,
                'success': False,
                'error': error_msg,
                'session_id': session_id,
                'subscription_status': subscription_status
            }
        )
        
        # Provide user-friendly error message
        if 'rate limit' in error_msg.lower():
            user_message = 'API rate limit exceeded. Please wait a moment and try again.'
            status_code = 429
        elif 'api' in error_msg.lower() or 'gpt' in error_msg.lower():
            user_message = 'AI service temporarily unavailable. Please try again.'
            status_code = 503
        else:
            user_message = 'Invalid request. Please rephrase your question.'
            status_code = 400
        
        return jsonify({
            'error': user_message,
            'success': False,
            'error_type': 'api_error'
        }), status_code
    
    except Exception as e:
        # Catch-all for unexpected errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] Unexpected error processing query: {e}")
        print(f"[ERROR] Traceback:\n{error_trace}")
        
        # Log failed query
        response_time = time.time() - start_time
        chat_analytics.log_query(
            email=email,
            question=question,
            answer=None,
            metadata={
                'response_time': response_time,
                'success': False,
                'error': str(e),
                'error_trace': error_trace[:500],  # First 500 chars of trace
                'session_id': session_id,
                'subscription_status': subscription_status
            }
        )
        
        # Log error in detailed query logger
        query_logger.log_query(
            user_email=email,
            question=question,
            answer="ERROR: Query failed",
            error=str(e),
            response_time_ms=int(response_time * 1000),
            session_id=session_id,
            metadata={'subscription_status': subscription_status, 'error_trace': error_trace[:200]}
        )
        
        return jsonify({
            'error': 'An unexpected error occurred. Our team has been notified.',
            'success': False,
            'error_type': 'server_error'
        }), 500

@app.route('/ask_stream', methods=['POST'])
@validate_input
@require_rate_limit
@require_paid_subscription
def ask_stream():
    """Handle question and return streaming answer using Server-Sent Events"""
    data = request.json
    question = data.get('question', '')
    session_id = data.get('session_id', 'default')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    def generate():
        try:
            # Get conversation history
            if session_id not in conversation_memory:
                conversation_memory[session_id] = []
            
            history = conversation_memory[session_id][-20:]  # Last 20 exchanges for deep context
            
            # Stream the query results
            full_answer = ""
            result_data = {'followups': [], 'resources': []}
            
            for event in engine.query_with_streaming(question, conversation_history=history):
                if event['type'] == 'chunk':
                    full_answer += event['content']
                elif event['type'] == 'followups':
                    result_data['followups'] = event['data']
                elif event['type'] == 'resources':
                    result_data['resources'] = event['data']
                
                # Send event to client
                yield f"data: {json.dumps(event)}\n\n"
            
            # Store in conversation memory
            conversation_memory[session_id].append({
                'question': question,
                'answer': full_answer,
                'intent': 'STREAMING',
                'context': {}
            })
            
            # Limit memory to last 30 exchanges per session
            if len(conversation_memory[session_id]) > 30:
                conversation_memory[session_id] = conversation_memory[session_id][-30:]
            
        except Exception as e:
            print(f"Error in streaming query: {e}")
            error_event = {'type': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/stats', methods=['GET'])
def stats():
    """Return database statistics"""
    try:
        return jsonify({
            'persons': len(engine.persons),
            'mandates': len(engine.mandates),
            'projects': len(engine.projects),
            'regions': len(engine.persons_by_region),
            'genres': len(engine.persons_by_genre),
            'formats': len(engine.persons_by_format),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/executives', methods=['GET'])
def list_executives():
    """List all executives"""
    try:
        executives = deep_dive.list_all_executives()
        return jsonify({
            'executives': executives,
            'count': len(executives),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/executive/<exec_name>', methods=['GET'])
def executive_profile(exec_name):
    """Get full executive profile (API or HTML)"""
    try:
        # Check if request wants JSON (API) or HTML (browser)
        if request.accept_mimetypes.best == 'application/json' or request.args.get('format') == 'json':
            # Return JSON for API calls
            profile = deep_dive.generate_profile(exec_name)
            
            if 'error' in profile:
                return jsonify({
                    'error': profile['error'],
                    'success': False
                }), 404
            
            return jsonify({
                'profile': profile,
                'success': True
            })
        else:
            # Return HTML page for browser
            return render_template('executive_profile.html')
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

# ============================================
# LANGGRAPH PATHWAY ENDPOINT
# ============================================

from pathway_graph import MandateWizardPathway

# Initialize pathway system
print("Initializing LangGraph pathway system...")
pathway = MandateWizardPathway(rag_engine=engine)
print("✓ LangGraph pathway ready!")

@app.route('/ask_pathway', methods=['POST'])
def ask_pathway():
    """
    Handle question using LangGraph pathway system
    Returns persona-adapted answer with pathway navigation
    """
    data = request.json
    question = data.get('question', '')
    user_id = data.get('user_id', 'anonymous')
    session_id = data.get('session_id', 'default')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    try:
        # Run through LangGraph pathway
        result = pathway.run(query=question, user_id=user_id)
        
        # Store in conversation memory
        if session_id not in conversation_memory:
            conversation_memory[session_id] = []
        
        conversation_memory[session_id].append({
            'question': question,
            'answer': result['answer'],
            'intent': 'PATHWAY',
            'context': {
                'user_profile': result['user_profile'],
                'layers_visited': result['current_layer'],
                'executive_name': result.get('executive_name', '')
            }
        })
        
        # Return enriched result
        return jsonify({
            'answer': result['answer'],
            'follow_ups': result['follow_ups'],
            'confidence_score': result['confidence_score'],
            'user_profile': result['user_profile'],
            'response_strategy': result['response_strategy'],
            'layers_visited': result['current_layer'],
            'layers_needed': result['layers_needed'],
            'executive_name': result.get('executive_name', ''),
            'sources': result.get('sources', []),
            'success': True
        })
        
    except Exception as e:
        print(f"Error in pathway query: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/ask_pathway_stream', methods=['POST'])
def ask_pathway_stream():
    """
    Handle question using LangGraph pathway system with streaming
    Returns persona-adapted answer with real-time updates
    """
    data = request.json
    question = data.get('question', '')
    user_id = data.get('user_id', 'anonymous')
    session_id = data.get('session_id', 'default')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    def generate():
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': 'Detecting persona...'})}\n\n"
            
            # Run through LangGraph pathway
            result = pathway.run(query=question, user_id=user_id)
            
            # Send user profile
            yield f"data: {json.dumps({'type': 'profile', 'data': result['user_profile']})}\n\n"
            
            # Send layers visited
            yield f"data: {json.dumps({'type': 'layers', 'data': {'visited': result['current_layer'], 'needed': result['layers_needed']}})}\n\n"
            
            # Send answer in chunks (simulate streaming)
            answer = result['answer']
            chunk_size = 50
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            # Send follow-ups
            yield f"data: {json.dumps({'type': 'followups', 'data': result['follow_ups']})}\n\n"
            
            # Send sources
            if result.get('sources'):
                yield f"data: {json.dumps({'type': 'sources', 'data': result['sources']})}\n\n"
            
            # Send completion
            yield f"data: {json.dumps({'type': 'complete', 'confidence': result['confidence_score']})}\n\n"
            
            # Store in conversation memory
            if session_id not in conversation_memory:
                conversation_memory[session_id] = []
            
            conversation_memory[session_id].append({
                'question': question,
                'answer': result['answer'],
                'intent': 'PATHWAY_STREAM',
                'context': {
                    'user_profile': result['user_profile'],
                    'layers_visited': result['current_layer']
                }
            })
            
        except Exception as e:
            print(f"Error in pathway streaming: {e}")
            import traceback
            traceback.print_exc()
            error_event = {'type': 'error', 'message': str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# ========== PATTERN ANALYSIS API ENDPOINTS ==========

@app.route('/api/pattern/greenlights/<int:year>', methods=['GET'])
def get_greenlights_by_year(year):
    """Get all greenlights for a specific year"""
    try:
        greenlights = pattern_analyzer.get_greenlights_by_year(year)
        return jsonify({
            'success': True,
            'year': year,
            'count': len(greenlights),
            'greenlights': greenlights
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/limited-series', methods=['GET'])
def get_limited_series():
    """Get all limited series greenlights"""
    try:
        year = request.args.get('year', type=int)
        limited_series = pattern_analyzer.get_limited_series_greenlights(year)
        return jsonify({
            'success': True,
            'year': year if year else 'all',
            'count': len(limited_series),
            'limited_series': limited_series
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/genre/<genre>', methods=['GET'])
def get_greenlights_by_genre(genre):
    """Get all greenlights for a specific genre"""
    try:
        greenlights = pattern_analyzer.get_greenlights_by_genre(genre)
        return jsonify({
            'success': True,
            'genre': genre,
            'count': len(greenlights),
            'greenlights': greenlights
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/executive/<executive_name>/stats', methods=['GET'])
def get_executive_stats(executive_name):
    """Get greenlight statistics for an executive"""
    try:
        stats = pattern_analyzer.get_executive_greenlight_stats(executive_name)
        if stats:
            return jsonify({'success': True, 'stats': stats})
        else:
            return jsonify({'success': False, 'error': 'Executive not found or no greenlights'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/executives/genre/<genre>', methods=['GET'])
def get_executives_by_genre(genre):
    """Find which executives greenlight specific genres most"""
    try:
        executives = pattern_analyzer.get_executives_by_genre(genre)
        return jsonify({
            'success': True,
            'genre': genre,
            'executives': executives
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/executives/international', methods=['GET'])
def get_international_executives():
    """Find executives who greenlight international content"""
    try:
        executives = pattern_analyzer.get_international_content_executives()
        return jsonify({
            'success': True,
            'executives': executives
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/trends/genres', methods=['GET'])
def get_genre_trends():
    """Get genre trends by year"""
    try:
        trends = pattern_analyzer.get_genre_trends_by_year()
        return jsonify({
            'success': True,
            'trends': trends
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/trends/formats', methods=['GET'])
def get_format_trends():
    """Get format trends (limited vs ongoing series)"""
    try:
        trends = pattern_analyzer.get_format_trends()
        return jsonify({
            'success': True,
            'trends': trends
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/ya-greenlights', methods=['GET'])
def get_ya_greenlights():
    """Get all YA (Young Adult) greenlights"""
    try:
        ya_greenlights = pattern_analyzer.get_ya_greenlights()
        return jsonify({
            'success': True,
            'count': len(ya_greenlights),
            'ya_greenlights': ya_greenlights
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Get overall statistics for dashboard visualization"""
    try:
        stats = pattern_analyzer.get_dashboard_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pattern/prodco/<prodco_name>/stats', methods=['GET'])
def get_prodco_stats(prodco_name):
    """Get greenlight statistics for a production company"""
    try:
        stats = pattern_analyzer.get_prodco_greenlight_rate(prodco_name)
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== END PATTERN ANALYSIS API ==========

# ========== RECENT MANDATES API (Landing Page Cards) ==========

@app.route('/api/recent-mandates', methods=['GET'])
def get_recent_mandates():
    """Get recent intelligence for landing page cards"""
    try:
        data = recent_mandates.get_landing_page_cards()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent-mandates/greenlights', methods=['GET'])
def get_recent_greenlights_api():
    """Get recent greenlights"""
    try:
        limit = request.args.get('limit', 10, type=int)
        greenlights = recent_mandates.get_recent_greenlights(limit=limit)
        return jsonify({
            'success': True,
            'count': len(greenlights),
            'greenlights': greenlights
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent-mandates/quotes', methods=['GET'])
def get_recent_quotes_api():
    """Get recent executive quotes"""
    try:
        limit = request.args.get('limit', 10, type=int)
        quotes = recent_mandates.get_recent_quotes(limit=limit)
        return jsonify({
            'success': True,
            'count': len(quotes),
            'quotes': quotes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/recent-mandates/deals', methods=['GET'])
def get_recent_deals_api():
    """Get recent production company deals"""
    try:
        limit = request.args.get('limit', 10, type=int)
        deals = recent_mandates.get_recent_deals(limit=limit)
        return jsonify({
            'success': True,
            'count': len(deals),
            'deals': deals
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== END RECENT MANDATES API ==========

# Register admin blueprint for query logs
from admin_logs import admin_bp
app.register_blueprint(admin_bp)
print("✓ Admin log endpoints registered at /admin/logs")

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎬 MANDATE WIZARD - Web Application")
    print("="*70)
    print(f"✓ Connected to Pinecone vector database")
    print(f"✓ Connected to Neo4j graph database")
    print(f"✓ Loaded {len(engine.persons)} executives from Neo4j")
    print(f"✓ HybridRAG engine ready")
    print("="*70)
    print("\n🚀 Starting server on http://0.0.0.0:5000")
    print("\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)




