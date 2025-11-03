#!/usr/bin/env python3
"""
Rate Limiting and Abuse Prevention System
Tracks API usage per user and enforces limits
"""

import time
from collections import defaultdict
from functools import wraps
from flask import request, jsonify
import json
import os
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self):
        self.usage_file = "/home/ubuntu/mandate_wizard_web_app/usage_tracking.json"
        self.usage_data = self.load_usage_data()
        
        # Rate limits (temporarily increased for testing)
        self.LIMITS = {
            'paid': {
                'queries_per_day': 1000,
                'queries_per_hour': 100,
                'cost_per_day': 100.00  # $100/day max
            },
            'free': {
                'queries_per_day': 50,
                'queries_per_hour': 20,
                'cost_per_day': 5.00  # $5/day max
            },
            'none': {
                'queries_per_day': 10,
                'queries_per_hour': 5,
                'cost_per_day': 1.00
            }
        }
        
        # Cost estimates (GPT-5 pricing)
        self.GPT5_COST_PER_1K_TOKENS = 0.01  # Estimate
        self.AVG_TOKENS_PER_QUERY = 2000  # Estimate
        
    def load_usage_data(self):
        """Load usage data from file"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_usage_data(self):
        """Save usage data to file"""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def get_user_key(self, email):
        """Get user key for tracking"""
        return email.lower().strip()
    
    def get_user_usage(self, email, subscription_status='free'):
        """Get current usage for user"""
        key = self.get_user_key(email)
        
        if key not in self.usage_data:
            self.usage_data[key] = {
                'subscription_status': subscription_status,
                'daily': {},
                'hourly': {},
                'total_queries': 0,
                'total_cost': 0.0,
                'first_query': None,
                'last_query': None
            }
        
        return self.usage_data[key]
    
    def check_rate_limit(self, email, subscription_status='free'):
        """Check if user has exceeded rate limits"""
        # DEV BYPASS: Allow unlimited queries for beta testing
        if email and email.lower() == "bradley@projectbrazen.com":
            return True, "OK (dev bypass)"
        
        usage = self.get_user_usage(email, subscription_status)
        limits = self.LIMITS.get(subscription_status, self.LIMITS['free'])
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        
        # Clean old data (keep last 7 days)
        self.clean_old_data(usage)
        
        # Check daily limit
        daily_queries = usage['daily'].get(today, 0)
        if daily_queries >= limits['queries_per_day']:
            return False, f"Daily limit exceeded ({limits['queries_per_day']} queries/day)"
        
        # Check hourly limit
        hourly_queries = usage['hourly'].get(current_hour, 0)
        if hourly_queries >= limits['queries_per_hour']:
            return False, f"Hourly limit exceeded ({limits['queries_per_hour']} queries/hour)"
        
        # Check cost limit (if tracking costs)
        daily_cost = usage.get('daily_cost', {}).get(today, 0.0)
        if daily_cost >= limits['cost_per_day']:
            return False, f"Daily cost limit exceeded (${limits['cost_per_day']:.2f}/day)"
        
        return True, "OK"
    
    def record_query(self, email, subscription_status='free', estimated_tokens=None):
        """Record a query for rate limiting"""
        usage = self.get_user_usage(email, subscription_status)
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        now = datetime.now().isoformat()
        
        # Update counters
        usage['daily'][today] = usage['daily'].get(today, 0) + 1
        usage['hourly'][current_hour] = usage['hourly'].get(current_hour, 0) + 1
        usage['total_queries'] += 1
        
        if not usage['first_query']:
            usage['first_query'] = now
        usage['last_query'] = now
        
        # Track cost
        if estimated_tokens is None:
            estimated_tokens = self.AVG_TOKENS_PER_QUERY
        
        cost = (estimated_tokens / 1000) * self.GPT5_COST_PER_1K_TOKENS
        
        if 'daily_cost' not in usage:
            usage['daily_cost'] = {}
        usage['daily_cost'][today] = usage['daily_cost'].get(today, 0.0) + cost
        usage['total_cost'] += cost
        
        self.save_usage_data()
        
        return {
            'queries_today': usage['daily'][today],
            'queries_this_hour': usage['hourly'][current_hour],
            'total_queries': usage['total_queries'],
            'cost_today': usage['daily_cost'][today],
            'total_cost': usage['total_cost']
        }
    
    def clean_old_data(self, usage):
        """Remove data older than 7 days"""
        cutoff = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Clean daily data
        usage['daily'] = {
            date: count 
            for date, count in usage.get('daily', {}).items() 
            if date >= cutoff
        }
        
        # Clean hourly data
        hourly_cutoff = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d-%H')
        usage['hourly'] = {
            hour: count 
            for hour, count in usage.get('hourly', {}).items() 
            if hour >= hourly_cutoff
        }
        
        # Clean cost data
        if 'daily_cost' in usage:
            usage['daily_cost'] = {
                date: cost 
                for date, cost in usage['daily_cost'].items() 
                if date >= cutoff
            }
    
    def get_usage_stats(self, email):
        """Get usage statistics for user"""
        key = self.get_user_key(email)
        if key not in self.usage_data:
            return None
        
        usage = self.usage_data[key]
        limits = self.LIMITS.get(usage.get('subscription_status', 'free'), self.LIMITS['free'])
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_hour = datetime.now().strftime('%Y-%m-%d-%H')
        
        return {
            'subscription_status': usage.get('subscription_status', 'free'),
            'queries_today': usage['daily'].get(today, 0),
            'daily_limit': limits['queries_per_day'],
            'queries_this_hour': usage['hourly'].get(current_hour, 0),
            'hourly_limit': limits['queries_per_hour'],
            'total_queries': usage['total_queries'],
            'cost_today': usage.get('daily_cost', {}).get(today, 0.0),
            'daily_cost_limit': limits['cost_per_day'],
            'total_cost': usage['total_cost'],
            'first_query': usage.get('first_query'),
            'last_query': usage.get('last_query')
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

def require_rate_limit(f):
    """Decorator to enforce rate limits on endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get user email from request
        email = request.json.get('email') if request.json else None
        
        if not email:
            # Try to get from headers or session
            email = request.headers.get('X-User-Email')
        
        if not email:
            return jsonify({
                'error': 'Email required for rate limiting',
                'success': False
            }), 401
        
        # Get subscription status (from auth check)
        subscription_status = request.json.get('subscription_status', 'free')
        
        # Check rate limit
        allowed, message = rate_limiter.check_rate_limit(email, subscription_status)
        
        if not allowed:
            return jsonify({
                'error': message,
                'success': False,
                'rate_limit_exceeded': True
            }), 429
        
        # Record the query
        stats = rate_limiter.record_query(email, subscription_status)
        
        # Call the original function
        response = f(*args, **kwargs)
        
        # Add usage stats to response headers
        if isinstance(response, tuple):
            response_data, status_code = response
        else:
            response_data = response
            status_code = 200
        
        # Add rate limit headers
        if hasattr(response_data, 'headers'):
            response_data.headers['X-RateLimit-Queries-Today'] = str(stats['queries_today'])
            response_data.headers['X-RateLimit-Cost-Today'] = f"${stats['cost_today']:.4f}"
        
        return response_data, status_code
    
    return decorated_function

