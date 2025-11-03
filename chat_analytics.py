#!/usr/bin/env python3
"""
Deep Chat Analytics System
Tracks user queries, analyzes patterns, and provides insights
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import re

class ChatAnalytics:
    def __init__(self):
        self.analytics_file = "/home/ubuntu/mandate_wizard_web_app/chat_analytics.json"
        self.analytics_data = self.load_analytics()
        
    def load_analytics(self):
        """Load analytics data from file"""
        if os.path.exists(self.analytics_file):
            try:
                with open(self.analytics_file, 'r') as f:
                    return json.load(f)
            except:
                return self.init_analytics_structure()
        return self.init_analytics_structure()
    
    def init_analytics_structure(self):
        """Initialize analytics data structure"""
        return {
            'queries': [],  # All queries with metadata
            'users': {},    # Per-user statistics
            'patterns': {   # Pattern analysis
                'topics': defaultdict(int),
                'intents': defaultdict(int),
                'keywords': defaultdict(int),
                'entities': defaultdict(int)
            },
            'performance': {  # Performance metrics
                'response_times': [],
                'success_rate': [],
                'error_types': defaultdict(int)
            },
            'engagement': {  # User engagement
                'session_lengths': [],
                'queries_per_session': [],
                'follow_up_rate': 0.0
            }
        }
    
    def save_analytics(self):
        """Save analytics data to file"""
        with open(self.analytics_file, 'w') as f:
            json.dump(self.analytics_data, f, indent=2)
    
    def log_query(self, email, question, answer, metadata=None):
        """Log a query with full context"""
        timestamp = datetime.now().isoformat()
        
        # Extract metadata
        if metadata is None:
            metadata = {}
        
        query_record = {
            'timestamp': timestamp,
            'email': email,
            'question': question,
            'answer': answer[:500] if answer else None,  # Truncate for storage
            'question_length': len(question),
            'answer_length': len(answer) if answer else 0,
            'response_time': metadata.get('response_time', 0),
            'success': metadata.get('success', True),
            'error': metadata.get('error'),
            'intent': metadata.get('intent', 'unknown'),
            'session_id': metadata.get('session_id', 'default'),
            'subscription_status': metadata.get('subscription_status', 'unknown'),
            'tokens_used': metadata.get('tokens_used', 0),
            'cost': metadata.get('cost', 0.0)
        }
        
        # Add to queries list
        self.analytics_data['queries'].append(query_record)
        
        # Update user statistics
        self.update_user_stats(email, query_record)
        
        # Extract patterns
        self.extract_patterns(question, query_record)
        
        # Update performance metrics
        self.update_performance(query_record)
        
        # Save periodically (every 10 queries)
        if len(self.analytics_data['queries']) % 10 == 0:
            self.save_analytics()
        
        return query_record
    
    def update_user_stats(self, email, query_record):
        """Update per-user statistics"""
        if email not in self.analytics_data['users']:
            self.analytics_data['users'][email] = {
                'first_query': query_record['timestamp'],
                'last_query': query_record['timestamp'],
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'avg_response_time': 0.0,
                'favorite_topics': defaultdict(int),
                'sessions': defaultdict(int)
            }
        
        user_stats = self.analytics_data['users'][email]
        user_stats['last_query'] = query_record['timestamp']
        user_stats['total_queries'] += 1
        
        if query_record['success']:
            user_stats['successful_queries'] += 1
        else:
            user_stats['failed_queries'] += 1
        
        user_stats['total_tokens'] += query_record.get('tokens_used', 0)
        user_stats['total_cost'] += query_record.get('cost', 0.0)
        
        # Update average response time
        total_time = user_stats['avg_response_time'] * (user_stats['total_queries'] - 1)
        user_stats['avg_response_time'] = (total_time + query_record['response_time']) / user_stats['total_queries']
        
        # Track sessions
        session_id = query_record.get('session_id', 'default')
        if session_id not in user_stats['sessions']:
            user_stats['sessions'][session_id] = 0
        user_stats['sessions'][session_id] += 1
    
    def extract_patterns(self, question, query_record):
        """Extract patterns from query"""
        question_lower = question.lower()
        
        # Extract topics (simple keyword matching)
        topic_keywords = {
            'greenlights': ['greenlight', 'green light', 'approved', 'picked up'],
            'executives': ['executive', 'exec', 'vp', 'president', 'ceo'],
            'deals': ['deal', 'contract', 'agreement', 'partnership'],
            'mandates': ['mandate', 'looking for', 'seeking', 'wants'],
            'talent': ['actor', 'actress', 'star', 'talent', 'cast'],
            'production': ['production', 'producer', 'studio', 'company'],
            'genre': ['drama', 'comedy', 'thriller', 'documentary', 'reality'],
            'strategy': ['strategy', 'focus', 'priority', 'direction']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in question_lower for kw in keywords):
                if topic not in self.analytics_data['patterns']['topics']:
                    self.analytics_data['patterns']['topics'][topic] = 0
                self.analytics_data['patterns']['topics'][topic] += 1
        
        # Extract intents (from metadata)
        intent = query_record.get('intent', 'unknown')
        if intent not in self.analytics_data['patterns']['intents']:
            self.analytics_data['patterns']['intents'][intent] = 0
        self.analytics_data['patterns']['intents'][intent] += 1
        
        # Extract keywords (simple frequency analysis)
        words = re.findall(r'\b\w{4,}\b', question_lower)  # Words 4+ chars
        for word in words:
            if word not in ['what', 'when', 'where', 'which', 'about', 'have', 'been', 'this', 'that']:
                if word not in self.analytics_data['patterns']['keywords']:
                    self.analytics_data['patterns']['keywords'][word] = 0
                self.analytics_data['patterns']['keywords'][word] += 1
    
    def update_performance(self, query_record):
        """Update performance metrics"""
        perf = self.analytics_data['performance']
        
        # Track response times
        perf['response_times'].append({
            'timestamp': query_record['timestamp'],
            'time': query_record['response_time']
        })
        
        # Keep only last 1000 response times
        if len(perf['response_times']) > 1000:
            perf['response_times'] = perf['response_times'][-1000:]
        
        # Track success rate
        perf['success_rate'].append({
            'timestamp': query_record['timestamp'],
            'success': query_record['success']
        })
        
        # Track errors
        if not query_record['success'] and query_record.get('error'):
            error_type = query_record['error'].split(':')[0]  # First part of error
            if error_type not in perf['error_types']:
                perf['error_types'][error_type] = 0
            perf['error_types'][error_type] += 1
    
    def get_summary_stats(self, days=7):
        """Get summary statistics for last N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        recent_queries = [
            q for q in self.analytics_data['queries']
            if q['timestamp'] >= cutoff
        ]
        
        if not recent_queries:
            return {'error': 'No queries in time period'}
        
        total_queries = len(recent_queries)
        successful = sum(1 for q in recent_queries if q['success'])
        failed = total_queries - successful
        
        avg_response_time = sum(q['response_time'] for q in recent_queries) / total_queries
        total_cost = sum(q.get('cost', 0.0) for q in recent_queries)
        
        # Unique users
        unique_users = len(set(q['email'] for q in recent_queries))
        
        # Top topics
        topic_counts = defaultdict(int)
        for topic, count in self.analytics_data['patterns']['topics'].items():
            topic_counts[topic] = count
        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top keywords
        keyword_counts = dict(self.analytics_data['patterns']['keywords'])
        top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            'period': f'Last {days} days',
            'total_queries': total_queries,
            'successful_queries': successful,
            'failed_queries': failed,
            'success_rate': f"{(successful/total_queries)*100:.1f}%",
            'unique_users': unique_users,
            'avg_queries_per_user': total_queries / unique_users if unique_users > 0 else 0,
            'avg_response_time': f"{avg_response_time:.2f}s",
            'total_cost': f"${total_cost:.2f}",
            'avg_cost_per_query': f"${total_cost/total_queries:.4f}",
            'top_topics': top_topics,
            'top_keywords': top_keywords
        }
    
    def get_user_journey(self, email):
        """Get user journey analysis"""
        user_queries = [
            q for q in self.analytics_data['queries']
            if q['email'] == email
        ]
        
        if not user_queries:
            return {'error': 'No queries found for user'}
        
        # Sort by timestamp
        user_queries.sort(key=lambda x: x['timestamp'])
        
        # Analyze journey
        first_query = user_queries[0]
        last_query = user_queries[-1]
        
        # Session analysis
        sessions = defaultdict(list)
        for query in user_queries:
            sessions[query['session_id']].append(query)
        
        session_stats = []
        for session_id, queries in sessions.items():
            session_stats.append({
                'session_id': session_id,
                'query_count': len(queries),
                'duration': self.calculate_duration(queries),
                'topics': self.extract_session_topics(queries)
            })
        
        return {
            'email': email,
            'first_query_date': first_query['timestamp'],
            'last_query_date': last_query['timestamp'],
            'total_queries': len(user_queries),
            'total_sessions': len(sessions),
            'avg_queries_per_session': len(user_queries) / len(sessions),
            'session_details': session_stats,
            'query_timeline': [
                {
                    'timestamp': q['timestamp'],
                    'question': q['question'][:100],
                    'success': q['success']
                }
                for q in user_queries[-20:]  # Last 20 queries
            ]
        }
    
    def calculate_duration(self, queries):
        """Calculate session duration"""
        if len(queries) < 2:
            return 0
        
        first = datetime.fromisoformat(queries[0]['timestamp'])
        last = datetime.fromisoformat(queries[-1]['timestamp'])
        return (last - first).total_seconds()
    
    def extract_session_topics(self, queries):
        """Extract topics from session queries"""
        topics = defaultdict(int)
        for query in queries:
            question_lower = query['question'].lower()
            if 'greenlight' in question_lower:
                topics['greenlights'] += 1
            if 'executive' in question_lower or 'exec' in question_lower:
                topics['executives'] += 1
            if 'deal' in question_lower:
                topics['deals'] += 1
        return dict(topics)
    
    def get_drop_off_analysis(self):
        """Analyze where users drop off"""
        # Group queries by session
        sessions = defaultdict(list)
        for query in self.analytics_data['queries']:
            sessions[query['session_id']].append(query)
        
        # Analyze drop-off points
        query_counts = [len(queries) for queries in sessions.values()]
        
        return {
            'total_sessions': len(sessions),
            'single_query_sessions': sum(1 for c in query_counts if c == 1),
            'multi_query_sessions': sum(1 for c in query_counts if c > 1),
            'avg_queries_per_session': sum(query_counts) / len(query_counts) if query_counts else 0,
            'max_queries_in_session': max(query_counts) if query_counts else 0,
            'drop_off_rate': f"{(sum(1 for c in query_counts if c == 1) / len(query_counts) * 100):.1f}%" if query_counts else "0%"
        }

# Global analytics instance
chat_analytics = ChatAnalytics()

