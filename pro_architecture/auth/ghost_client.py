"""
Ghost CMS API client for subscription verification.
"""
import jwt
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os


class GhostClient:
    """Client for Ghost Admin API to verify member subscriptions."""
    
    def __init__(self):
        self.api_url = os.environ.get("GHOST_API_URL", "https://hollywood-signal.ghost.io")
        self.admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY", "")
        
        if not self.admin_api_key:
            raise ValueError("GHOST_ADMIN_API_KEY environment variable is required")
        
        # Parse the admin API key (format: id:secret)
        try:
            self.key_id, self.key_secret = self.admin_api_key.split(":")
        except ValueError:
            raise ValueError("GHOST_ADMIN_API_KEY must be in format 'id:secret'")
    
    def _generate_jwt_token(self) -> str:
        """Generate JWT token for Ghost Admin API authentication."""
        iat = int(datetime.now().timestamp())
        
        payload = {
            'iat': iat,
            'exp': iat + 300,  # Token expires in 5 minutes
            'aud': '/admin/'
        }
        
        token = jwt.encode(
            payload,
            bytes.fromhex(self.key_secret),
            algorithm='HS256',
            headers={'kid': self.key_id}
        )
        
        return token
    
    def _make_request(self, endpoint: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
        """Make authenticated request to Ghost Admin API."""
        token = self._generate_jwt_token()
        headers = {
            'Authorization': f'Ghost {token}',
            'Content-Type': 'application/json',
            'Accept-Version': 'v5.0'
        }
        
        url = f"{self.api_url}/ghost/api/admin/{endpoint}"
        
        try:
            response = requests.request(method, url, headers=headers, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ghost API request failed: {e}")
            return {}
    
    def get_member_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get member information by email address.
        
        Args:
            email: Member's email address
            
        Returns:
            Member data dict or None if not found
        """
        try:
            data = self._make_request(f"members/?filter=email:{email}")
            members = data.get('members', [])
            
            if members:
                return members[0]
            return None
        except Exception as e:
            print(f"Error fetching member: {e}")
            return None
    
    def has_active_subscription(self, email: str) -> bool:
        """
        Check if a member has an active subscription.
        
        Args:
            email: Member's email address
            
        Returns:
            True if member has active subscription, False otherwise
        """
        member = self.get_member_by_email(email)
        
        if not member:
            print(f"Member not found: {email}")
            return False
        
        # Check if member has any active subscriptions
        subscriptions = member.get('subscriptions', [])
        
        for sub in subscriptions:
            status = sub.get('status', '').lower()
            if status in ['active', 'trialing']:
                return True
        
        # Also check if member is comped (free subscription)
        if member.get('comped', False):
            return True
        
        print(f"No active subscription found for: {email}")
        return False
    
    def get_member_status(self, email: str) -> Dict[str, Any]:
        """
        Get detailed member status information.
        
        Args:
            email: Member's email address
            
        Returns:
            Dict with member status details
        """
        member = self.get_member_by_email(email)
        
        if not member:
            return {
                'exists': False,
                'has_subscription': False,
                'status': 'not_found'
            }
        
        subscriptions = member.get('subscriptions', [])
        active_subs = [s for s in subscriptions if s.get('status', '').lower() in ['active', 'trialing']]
        
        return {
            'exists': True,
            'has_subscription': len(active_subs) > 0 or member.get('comped', False),
            'status': 'active' if (active_subs or member.get('comped')) else 'inactive',
            'email': member.get('email'),
            'name': member.get('name'),
            'created_at': member.get('created_at'),
            'subscriptions': len(subscriptions),
            'active_subscriptions': len(active_subs),
            'comped': member.get('comped', False)
        }
