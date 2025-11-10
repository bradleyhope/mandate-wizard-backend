from flask import Flask, request, jsonify
from flask_cors import CORS
from rag.engine import Engine
from auth.auth_manager import AuthManager
from auth.ghost_client import GhostClient
from config import S
import os, psutil, time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins":"*","supports_credentials":True}})

# Initialize authentication
auth_manager = AuthManager()

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
                return jsonify({
                    "error": "No active Hollywood Signal subscription found for this email."
                }), 403
        
        # Get member info
        member = auth_manager.ghost_client.get_member_by_email(email)
        name = member.get('name') if member else None
        
        # Generate JWT token
        jwt_token = auth_manager.generate_jwt_token(email, name)
        
        return jsonify({
            "success": True,
            "token": jwt_token,
            "email": email,
            "name": name,
            "whitelisted": is_whitelisted
        }), 200
        
    except Exception as e:
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
    
    eng = get_engine()
    out = eng.answer(q)
    
    # Add user context to response
    out['user'] = {
        'email': request.user.get('email'),
        'name': request.user.get('name')
    }
    
    return jsonify(out), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
