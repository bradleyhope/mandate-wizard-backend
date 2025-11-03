#!/usr/bin/env python3
"""
Ghost Authentication Service
Handles authentication and subscription verification for Hollywood Signal members
"""

import jwt
import time
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Ghost Configuration
GHOST_URL = "https://hollywood-signal.ghost.io"
GHOST_ADMIN_ID = "68f75d019a9a330001dbb16e"
GHOST_ADMIN_SECRET = "296c196cb6e3c2f086842218051dad973395cd7b7701647a7cf3c4c3644a4268"
GHOST_CONTENT_KEY = "6fd0afbb867dc5b1a41a415565"

class GhostAuthService:
    """Service for authenticating Hollywood Signal subscribers"""
    
    def __init__(self):
        self.ghost_url = GHOST_URL
        self.admin_id = GHOST_ADMIN_ID
        self.admin_secret = GHOST_ADMIN_SECRET
        self.content_key = GHOST_CONTENT_KEY
    
    def generate_admin_token(self):
        """Generate JWT token for Ghost Admin API"""
        # Split the key
        key_id = self.admin_id
        key_secret = bytes.fromhex(self.admin_secret)
        
        # Create JWT token
        iat = int(time.time())
        exp = iat + 300  # 5 minutes
        
        header = {"alg": "HS256", "typ": "JWT", "kid": key_id}
        payload = {
            "iat": iat,
            "exp": exp,
            "aud": "/admin/"
        }
        
        token = jwt.encode(payload, key_secret, algorithm="HS256", headers=header)
        return token
    
    def get_member_by_email(self, email):
        """
        Fetch member from Ghost by email
        Returns member object or None if not found
        """
        try:
            token = self.generate_admin_token()
            headers = {
                "Authorization": f"Ghost {token}",
                "Accept-Version": "v5.0"
            }
            
            # Search for member by email
            url = f"{self.ghost_url}/ghost/api/admin/members/?filter=email:{email}&include=newsletters,labels"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                members = data.get("members", [])
                if members:
                    return members[0]
            
            return None
            
        except Exception as e:
            print(f"Error fetching member: {e}")
            return None
    
    def check_subscription_status(self, email):
        """
        Check if user has active paid subscription
        Returns: {
            "is_member": bool,
            "is_paid": bool,
            "status": "paid" | "free" | "none",
            "member_since": datetime | None
        }
        """
        member = self.get_member_by_email(email)
        
        if not member:
            return {
                "is_member": False,
                "is_paid": False,
                "status": "none",
                "member_since": None
            }
        
        status = member.get("status", "free")
        subscriptions = member.get("subscriptions", [])
        
        # Check if has active paid subscription
        has_active_paid = any(
            sub.get("status") == "active" 
            for sub in subscriptions
        )
        
        return {
            "is_member": True,
            "is_paid": status == "paid" or has_active_paid,
            "status": "paid" if (status == "paid" or has_active_paid) else "free",
            "member_since": member.get("created_at"),
            "name": member.get("name"),
            "email": member.get("email")
        }
    
    def send_magic_link(self, email):
        """
        Send magic link to user's email for passwordless login
        Uses Ghost's built-in magic link system
        """
        try:
            token = self.generate_admin_token()
            headers = {
                "Authorization": f"Ghost {token}",
                "Content-Type": "application/json",
                "Accept-Version": "v5.0"
            }
            
            # Ghost magic link endpoint
            url = f"{self.ghost_url}/ghost/api/admin/members/send-magic-link/"
            payload = {
                "email": email,
                "emailType": "signin"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 201:
                return {"success": True, "message": "Magic link sent to your email"}
            else:
                return {"success": False, "message": "Failed to send magic link"}
                
        except Exception as e:
            print(f"Error sending magic link: {e}")
            return {"success": False, "message": str(e)}


# Flask decorator for protected routes
def require_paid_subscription(f):
    """Decorator to require paid Hollywood Signal subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get email from request (could be from JWT, session, etc.)
        email = request.headers.get("X-User-Email")
        
        if not email:
            return jsonify({"error": "Authentication required"}), 401
        
        # DEV BYPASS: Allow specific email for beta testing
        if email == "bradley@projectbrazen.com":
            request.user_status = {
                "is_member": True,
                "is_paid": True,
                "status": "paid",
                "member_since": "2025-01-01"
            }
            return f(*args, **kwargs)
        
        # Check subscription status
        auth_service = GhostAuthService()
        status = auth_service.check_subscription_status(email)
        
        if not status["is_paid"]:
            return jsonify({
                "error": "Paid subscription required",
                "message": "This feature requires a paid Hollywood Signal subscription",
                "subscribe_url": "https://www.hollywoodsignal.com"
            }), 403
        
        # Add user info to request context
        request.user_status = status
        return f(*args, **kwargs)
    
    return decorated_function


def require_member(f):
    """Decorator to require Hollywood Signal membership (free or paid)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        email = request.headers.get("X-User-Email")
        
        if not email:
            return jsonify({"error": "Authentication required"}), 401
        
        auth_service = GhostAuthService()
        status = auth_service.check_subscription_status(email)
        
        if not status["is_member"]:
            return jsonify({
                "error": "Membership required",
                "message": "Please sign up for Hollywood Signal",
                "subscribe_url": "https://www.hollywoodsignal.com"
            }), 403
        
        request.user_status = status
        return f(*args, **kwargs)
    
    return decorated_function


# Initialize service
ghost_auth = GhostAuthService()

