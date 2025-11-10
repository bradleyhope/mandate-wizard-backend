"""
Authentication manager for handling magic links and sessions.
"""
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
from functools import wraps
from flask import request, jsonify

from .ghost_client import GhostClient
from .email_service import EmailService


class AuthManager:
    """Manages authentication tokens and sessions."""
    
    def __init__(self):
        self.jwt_secret = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
        self.ghost_client = GhostClient()
        self.email_service = EmailService()
        
        # In-memory store for magic link tokens (in production, use Redis)
        self._magic_tokens: Dict[str, Dict[str, Any]] = {}
    
    def generate_magic_token(self, email: str) -> str:
        """
        Generate a magic link token for email authentication.
        
        Args:
            email: User's email address
            
        Returns:
            Magic token string
        """
        token = secrets.token_urlsafe(32)
        
        self._magic_tokens[token] = {
            'email': email,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=15)
        }
        
        return token
    
    def verify_magic_token(self, token: str) -> Optional[str]:
        """
        Verify a magic link token and return the associated email.
        
        Args:
            token: Magic token to verify
            
        Returns:
            Email address if token is valid, None otherwise
        """
        token_data = self._magic_tokens.get(token)
        
        if not token_data:
            return None
        
        # Check if token has expired
        if datetime.now() > token_data['expires_at']:
            del self._magic_tokens[token]
            return None
        
        # Token is valid, remove it (one-time use)
        email = token_data['email']
        del self._magic_tokens[token]
        
        return email
    
    def generate_jwt_token(self, email: str, name: Optional[str] = None) -> str:
        """
        Generate JWT token for authenticated session.
        
        Args:
            email: User's email address
            name: Optional user name
            
        Returns:
            JWT token string
        """
        payload = {
            'email': email,
            'name': name,
            'iat': datetime.now(),
            'exp': datetime.now() + timedelta(days=30)  # Token valid for 30 days
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            print("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid JWT token: {e}")
            return None
    
    def send_magic_link(self, email: str, frontend_url: str) -> bool:
        """
        Generate and send magic link to user's email.
        
        Args:
            email: User's email address
            frontend_url: Base URL of frontend application
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # First check if user has active subscription
        if not self.ghost_client.has_active_subscription(email):
            print(f"User {email} does not have active subscription")
            return False
        
        # Get member info for personalization
        member = self.ghost_client.get_member_by_email(email)
        name = member.get('name') if member else None
        
        # Generate magic token
        magic_token = self.generate_magic_token(email)
        
        # Create magic link URL
        magic_link = f"{frontend_url}/auth/verify?token={magic_token}"
        
        # Send email
        return self.email_service.send_magic_link(email, magic_link, name)
    
    def authenticate_with_magic_token(self, magic_token: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with magic token and return session data.
        
        Args:
            magic_token: Magic token from email link
            
        Returns:
            Dict with JWT token and user info, or None if authentication fails
        """
        # Verify magic token
        email = self.verify_magic_token(magic_token)
        
        if not email:
            print("Invalid or expired magic token")
            return None
        
        # Verify subscription is still active
        if not self.ghost_client.has_active_subscription(email):
            print(f"User {email} subscription is no longer active")
            return None
        
        # Get member info
        member = self.ghost_client.get_member_by_email(email)
        name = member.get('name') if member else None
        
        # Generate JWT token
        jwt_token = self.generate_jwt_token(email, name)
        
        return {
            'token': jwt_token,
            'email': email,
            'name': name
        }
    
    def require_auth(self, f):
        """
        Decorator to protect routes with JWT authentication.
        
        Usage:
            @app.route('/protected')
            @auth_manager.require_auth
            def protected_route():
                return {'data': 'secret'}
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401
            
            token = auth_header.replace('Bearer ', '')
            
            # Verify token
            payload = self.verify_jwt_token(token)
            
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Check if subscription is still active
            email = payload.get('email')
            if not self.ghost_client.has_active_subscription(email):
                return jsonify({'error': 'Subscription is no longer active'}), 403
            
            # Add user info to request context
            request.user = payload
            
            return f(*args, **kwargs)
        
        return decorated_function
