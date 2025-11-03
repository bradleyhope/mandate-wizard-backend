#!/usr/bin/env python3
"""
Input Validation and Sanitization
Protects against injection attacks and abuse
"""

import re
from functools import wraps
from flask import request, jsonify

class InputValidator:
    def __init__(self):
        # Maximum lengths
        self.MAX_QUERY_LENGTH = 1000
        self.MAX_EMAIL_LENGTH = 255
        
        # Suspicious patterns (potential prompt injection)
        self.SUSPICIOUS_PATTERNS = [
            r'ignore\s+(previous|all)\s+instructions',
            r'system\s*:',
            r'<\s*script',
            r'javascript\s*:',
            r'on(load|error|click)\s*=',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__',
            r'subprocess',
            r'os\.system',
        ]
        
        # Compile patterns
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.SUSPICIOUS_PATTERNS]
    
    def validate_email(self, email):
        """Validate email format"""
        if not email or len(email) > self.MAX_EMAIL_LENGTH:
            return False, "Invalid email length"
        
        # Basic email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        return True, "OK"
    
    def validate_query(self, query):
        """Validate user query"""
        if not query:
            return False, "Query cannot be empty"
        
        if len(query) > self.MAX_QUERY_LENGTH:
            return False, f"Query too long (max {self.MAX_QUERY_LENGTH} characters)"
        
        # Check for suspicious patterns
        for pattern in self.compiled_patterns:
            if pattern.search(query):
                return False, "Query contains suspicious content"
        
        return True, "OK"
    
    def sanitize_query(self, query):
        """Sanitize user query"""
        if not query:
            return ""
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Trim whitespace
        query = query.strip()
        
        # Remove excessive whitespace
        query = re.sub(r'\s+', ' ', query)
        
        # Remove HTML tags
        query = re.sub(r'<[^>]+>', '', query)
        
        return query
    
    def validate_and_sanitize(self, query):
        """Validate and sanitize query in one step"""
        # Sanitize first
        sanitized = self.sanitize_query(query)
        
        # Then validate
        valid, message = self.validate_query(sanitized)
        
        if not valid:
            return None, message
        
        return sanitized, "OK"

# Global validator instance
input_validator = InputValidator()

def validate_input(f):
    """Decorator to validate input on endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.json if request.json else {}
        
        # Validate email if present
        if 'email' in data:
            valid, message = input_validator.validate_email(data['email'])
            if not valid:
                return jsonify({
                    'error': message,
                    'success': False
                }), 400
        
        # Validate and sanitize query if present
        if 'question' in data or 'query' in data:
            query = data.get('question') or data.get('query')
            sanitized, message = input_validator.validate_and_sanitize(query)
            
            if sanitized is None:
                return jsonify({
                    'error': message,
                    'success': False
                }), 400
            
            # Replace with sanitized version
            if 'question' in data:
                data['question'] = sanitized
            if 'query' in data:
                data['query'] = sanitized
            
            # Note: Cannot modify request.json directly as it's read-only
            # The sanitized data is already in the 'data' variable
            # which will be used by the endpoint
        
        return f(*args, **kwargs)
    
    return decorated_function

