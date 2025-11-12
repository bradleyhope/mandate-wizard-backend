from flask import Flask, request, jsonify
from flask_cors import CORS
from rag.engine import Engine
from auth.auth_manager import AuthManager
from auth.ghost_client import GhostClient
from logging_service import get_logger
from config import S
import os, psutil, time

# Import migration endpoints
try:
    from database.migrate_endpoint import create_migration_endpoint, create_data_migration_endpoint
    MIGRATION_AVAILABLE = True
except ImportError:
    MIGRATION_AVAILABLE = False
    print("⚠️ Migration endpoints not available")

# Import Redis Streams client
try:
    from streams import get_streams_client
    from streams.events_endpoint import create_events_endpoint
    STREAMS_AVAILABLE = True
except ImportError:
    STREAMS_AVAILABLE = False
    print("⚠️ Redis Streams not available")

# Import Analytics endpoints
try:
    from analytics.demand_endpoints import demand_bp
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("⚠️ Analytics endpoints not available")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins":"*","supports_credentials":True}})

# Initialize authentication and logging
auth_manager = AuthManager()
query_logger = get_logger()

_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = Engine()
    return _engine

@app.route("/healthz")
def healthz():
    return {"ok": True}, 200

@app.route("/", methods=["GET"])
def root():
    return {"service": "Mandate Wizard backend", "mode": S.EMBEDDER + "/" + S.RERANKER}, 200

@app.route("/metrics", methods=["GET"])
def metrics():
    p = psutil.Process(os.getpid())
    return {
        "rss_mb": round(p.memory_info().rss/1024/1024, 1),
        "threads": p.num_threads(),
        "cpu_percent": psutil.cpu_percent(interval=0.1)
    }, 200

# Authentication endpoints
@app.route("/auth/login", methods=["POST"])
def login():
    """Direct login - check subscription and return JWT immediately (no email)."""
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    try:
        # Check if email is whitelisted
        is_whitelisted = auth_manager._is_whitelisted(email)
        
        if not is_whitelisted:
            # Check if user has active subscription
            if not auth_manager.ghost_client.has_active_subscription(email):
                # Log failed authentication
                query_logger.log_authentication(
                    email=email,
                    success=False,
                    method="direct_login",
                    reason="No active subscription"
                )
                return jsonify({
                    "error": "No active Hollywood Signal subscription found for this email."
                }), 403
        
        # Get member info
        member = auth_manager.ghost_client.get_member_by_email(email)
        name = member.get('name') if member else None
        
        # Generate JWT token
        jwt_token = auth_manager.generate_jwt_token(email, name)
        
        # Log successful authentication
        query_logger.log_authentication(
            email=email,
            success=True,
            method="direct_login"
        )
        
        return jsonify({
            "success": True,
            "token": jwt_token,
            "email": email,
            "name": name,
            "whitelisted": is_whitelisted
        }), 200
        
    except Exception as e:
        # Log failed authentication
        query_logger.log_authentication(
            email=email,
            success=False,
            method="direct_login",
            reason=str(e)
        )
        print(f"Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/auth/send-magic-link", methods=["POST"])
def send_magic_link():
    """Send magic link to user's email for authentication."""
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    # Get frontend URL from environment or request origin
    frontend_url = os.environ.get("FRONTEND_URL", request.headers.get("Origin", "http://localhost:3000"))
    
    try:
        success = auth_manager.send_magic_link(email, frontend_url)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Magic link sent to your email"
            }), 200
        else:
            return jsonify({
                "error": "Failed to send magic link. Please ensure you have an active Hollywood Signal subscription and that Mailgun DNS is configured."
            }), 403
            
    except Exception as e:
        print(f"Error sending magic link: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/auth/verify", methods=["POST"])
def verify_magic_token():
    """Verify magic token and return JWT for session."""
    data = request.get_json(force=True) or {}
    token = (data.get("token") or "").strip()
    
    if not token:
        return jsonify({"error": "Token is required"}), 400
    
    try:
        auth_data = auth_manager.authenticate_with_magic_token(token)
        
        if auth_data:
            return jsonify({
                "success": True,
                "token": auth_data['token'],
                "email": auth_data['email'],
                "name": auth_data.get('name')
            }), 200
        else:
            return jsonify({
                "error": "Invalid or expired token"
            }), 401
            
    except Exception as e:
        print(f"Error verifying token: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/auth/check-subscription", methods=["POST"])
def check_subscription():
    """Check if email has active subscription (for testing)."""
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    try:
        ghost_client = GhostClient()
        status = ghost_client.get_member_status(email)
        return jsonify(status), 200
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/auth/logout", methods=["POST"])
def logout():
    """Logout endpoint (client-side token removal)."""
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

# Protected query endpoint
@app.route("/api/answer", methods=["POST"])
@auth_manager.require_auth
def answer():
    """Query endpoint - requires authentication."""
    data = request.get_json(force=True) or {}
    q = (data.get("question") or "").strip()
    if not q:
        return jsonify({"error":"question is required"}), 400
    
    # Get user info
    user_email = request.user.get('email')
    user_name = request.user.get('name')
    
    try:
        # Execute query
        eng = get_engine()
        out = eng.answer(q, user_email=user_email)
        
        # Add user context to response
        out['user'] = {
            'email': user_email,
            'name': user_name
        }
        
        # Log the query and response
        metadata = {
            'ip': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'endpoint': '/api/answer'
        }
        
        query_logger.log_query(
            user_email=user_email,
            user_name=user_name,
            question=q,
            response=out,
            metadata=metadata
        )
        
        # Publish QuerySignal events for entities in the response
        if STREAMS_AVAILABLE:
            try:
                streams_client = get_streams_client()
                entities = out.get('entities', [])
                
                for entity in entities:
                    entity_id = entity.get('id')
                    entity_type = entity.get('type', 'unknown')
                    
                    if entity_id:
                        streams_client.publish_query_signal(
                            entity_id=entity_id,
                            entity_type=entity_type,
                            query=q,
                            user_id=user_email
                        )
            except Exception as stream_error:
                # Don't fail the request if event publishing fails
                print(f"⚠️ Failed to publish query signals: {stream_error}")
        
        return jsonify(out), 200
        
    except Exception as e:
        # Log the error
        query_logger.log_error(
            user_email=user_email,
            error_type=type(e).__name__,
            error_message=str(e),
            context={'question': q}
        )
        raise

# Admin/Stats endpoints
@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    """Get query statistics."""
    hours = int(request.args.get('hours', 24))
    
    try:
        stats = query_logger.get_query_stats(hours=hours)
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/logs/queries", methods=["GET"])
def admin_query_logs():
    """Get recent query logs."""
    import json
    limit = int(request.args.get('limit', 100))
    
    try:
        log_file = query_logger.json_log_file
        
        if not log_file.exists():
            return jsonify({"queries": []}), 200
        
        # Read last N lines
        queries = []
        with open(log_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    queries.append(json.loads(line))
                except:
                    continue
        
        return jsonify({"queries": queries, "count": len(queries)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/recent-cards", methods=["GET"])
def recent_cards():
    """Get recent mandate/news cards for homepage."""
    from rag.retrievers.pinecone_retriever import PineconeRetriever
    from datetime import datetime, timedelta
    
    try:
        limit = int(request.args.get('limit', 10))
        retriever = PineconeRetriever()
        
        # Query for recent content
        # Use a broad query to get diverse results
        results = retriever.retrieve("recent mandate news executive", top_k=50)
        
        # Filter and score cards
        cards = []
        for doc in results:
            meta = doc.get('metadata', {})
            
            # Skip if no name or wrong type
            if not meta.get('name') or len(meta.get('name', '')) < 5:
                continue
            
            # Skip migration-only dates
            updated = meta.get('updated') or meta.get('source_date')
            if not updated or updated.startswith('2025-11-10 07:14'):
                continue
            
            # Only include certain types
            entity_type = meta.get('entity_type') or meta.get('category')
            if entity_type not in ['mandate', 'person', 'news', 'executive_moves']:
                continue
            
            cards.append({
                'id': doc.get('id'),
                'name': meta.get('name'),
                'type': entity_type,
                'streamer': meta.get('streamer'),
                'updated': updated,
                'text': meta.get('text', '')[:200] + '...' if meta.get('text') else ''
            })
        
        # Sort by date (most recent first)
        cards.sort(key=lambda x: x.get('updated', ''), reverse=True)
        
        return jsonify({"cards": cards[:limit]}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/entity/<entity_id>", methods=["GET"])
def get_entity(entity_id):
    """Get full entity details from both Pinecone and Neo4j."""
    from rag.retrievers.pinecone_retriever import PineconeRetriever
    from rag.graph.dao import DAO
    
    try:
        retriever = PineconeRetriever()
        dao = DAO()
        
        # Get from Pinecone
        pinecone_data = retriever.index.fetch(ids=[entity_id])
        
        entity_info = {}
        if pinecone_data and 'vectors' in pinecone_data and entity_id in pinecone_data['vectors']:
            meta = pinecone_data['vectors'][entity_id].get('metadata', {})
            entity_info = {
                'id': entity_id,
                'name': meta.get('name'),
                'title': meta.get('title'),
                'bio': meta.get('bio'),
                'mandate': meta.get('mandate'),
                'streamer': meta.get('streamer'),
                'region': meta.get('region'),
                'formats': meta.get('formats'),
                'genres': meta.get('genres'),
                'updated': meta.get('updated'),
                'text': meta.get('text')
            }
        
        # Get from Neo4j if it's a person
        neo4j_data = None
        if entity_id.startswith('person_'):
            neo4j_data = dao.get_person(entity_id)
        
        return jsonify({
            'entity': entity_info,
            'neo4j': neo4j_data
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Register migration endpoints if available
if MIGRATION_AVAILABLE:
    create_migration_endpoint(app)
    create_data_migration_endpoint(app)
    print("✅ Migration endpoints registered:")
    print("   - /api/admin/migrate (schema migration)")
    print("   - /api/admin/migrate-data (data migration)")

# Register events endpoints if available
if STREAMS_AVAILABLE:
    events_bp = create_events_endpoint()
    app.register_blueprint(events_bp)
    print("✅ Redis Streams endpoints registered:")
    print("   - /api/events/update-request (publish update events)")
    print("   - /api/events/streams/info (stream information)")

# Register analytics endpoints if available
if ANALYTICS_AVAILABLE:
    app.register_blueprint(demand_bp)
    print("✅ Analytics endpoints registered:")
    print("   - /api/analytics/demand/top (top demand entities)")
    print("   - /api/analytics/demand/entity/:id (entity demand details)")
    print("   - /api/analytics/demand/stats (demand statistics)")
    print("   - /api/analytics/demand/trending (trending entities)")
    print("   - /api/analytics/demand/stale (stale high-demand entities)")
    print("   - /api/admin/db-status (database status)")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
