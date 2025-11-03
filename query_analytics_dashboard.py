"""
Query Analytics Dashboard
Track user behavior, popular queries, and system performance
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
import threading


class QueryAnalyticsDashboard:
    """
    Comprehensive analytics for query patterns and user behavior
    """

    def __init__(self, history_days: int = 30):
        """
        Initialize analytics dashboard

        Args:
            history_days: Number of days to keep analytics data
        """
        self.history_days = history_days

        # Query logs: timestamp -> query_data
        self.query_log = []

        # Aggregated metrics
        self.metrics = {
            'total_queries': 0,
            'unique_users': set(),
            'queries_by_intent': defaultdict(int),
            'queries_by_tier': defaultdict(int),
            'avg_response_time': 0.0,
            'cache_hit_rate': 0.0,
            'error_rate': 0.0
        }

        # Popular queries (question -> count)
        self.popular_queries = Counter()

        # Popular executives mentioned
        self.popular_executives = Counter()

        # Popular regions queried
        self.popular_regions = Counter()

        # Popular genres queried
        self.popular_genres = Counter()

        # Time-series data (hour -> count)
        self.queries_by_hour = defaultdict(int)
        self.queries_by_day = defaultdict(int)

        # Performance buckets
        self.response_time_buckets = {
            '<100ms': 0,
            '100-500ms': 0,
            '500ms-1s': 0,
            '1-2s': 0,
            '2-5s': 0,
            '>5s': 0
        }

        # Thread lock
        self.lock = threading.Lock()

        # Start cleanup thread
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background thread to clean up old data"""
        def cleanup():
            import time
            while True:
                time.sleep(86400)  # Run daily
                self._cleanup_old_data()

        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def _cleanup_old_data(self):
        """Remove data older than history_days"""
        with self.lock:
            cutoff = datetime.now() - timedelta(days=self.history_days)

            # Filter query log
            self.query_log = [
                entry for entry in self.query_log
                if entry['timestamp'] > cutoff
            ]

    def log_query(
        self,
        question: str,
        answer: str,
        intent: str,
        response_time: float,
        user_email: str,
        subscription_tier: str,
        cached: bool = False,
        error: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Log a query for analytics

        Args:
            question: User's question
            answer: System's answer
            intent: Query intent
            response_time: Response time in seconds
            user_email: User's email
            subscription_tier: User's subscription tier
            cached: Whether result was cached
            error: Error message if query failed
            metadata: Additional metadata
        """
        with self.lock:
            timestamp = datetime.now()

            # Create query entry
            entry = {
                'timestamp': timestamp,
                'question': question,
                'answer': answer,
                'intent': intent,
                'response_time': response_time,
                'user_email': user_email,
                'subscription_tier': subscription_tier,
                'cached': cached,
                'error': error,
                'success': error is None,
                'metadata': metadata or {}
            }

            # Add to log
            self.query_log.append(entry)

            # Update metrics
            self._update_metrics(entry)

    def _update_metrics(self, entry: Dict[str, Any]):
        """Update aggregated metrics with new query"""
        # Total queries
        self.metrics['total_queries'] += 1

        # Unique users
        self.metrics['unique_users'].add(entry['user_email'])

        # Queries by intent
        self.metrics['queries_by_intent'][entry['intent']] += 1

        # Queries by tier
        self.metrics['queries_by_tier'][entry['subscription_tier']] += 1

        # Popular queries
        question_normalized = entry['question'].lower().strip()
        self.popular_queries[question_normalized] += 1

        # Extract and count executives mentioned
        answer_lower = entry['answer'].lower()
        common_executives = [
            'brandon riegg', 'kennedy corrin', 'peter friedlander',
            'bela bajaria', 'scott stuber', 'ted sarandos'
        ]
        for exec_name in common_executives:
            if exec_name in answer_lower or exec_name in question_normalized:
                self.popular_executives[exec_name] += 1

        # Extract regions (simplified)
        regions = ['uk', 'mena', 'nordics', 'india', 'korea', 'japan', 'france', 'germany']
        for region in regions:
            if region in question_normalized:
                self.popular_regions[region] += 1

        # Extract genres
        genres = ['thriller', 'comedy', 'drama', 'documentary', 'horror', 'sci-fi', 'romance']
        for genre in genres:
            if genre in question_normalized:
                self.popular_genres[genre] += 1

        # Time-series
        hour_key = entry['timestamp'].strftime('%Y-%m-%d %H:00')
        day_key = entry['timestamp'].strftime('%Y-%m-%d')
        self.queries_by_hour[hour_key] += 1
        self.queries_by_day[day_key] += 1

        # Response time buckets
        rt = entry['response_time'] * 1000  # Convert to ms
        if rt < 100:
            self.response_time_buckets['<100ms'] += 1
        elif rt < 500:
            self.response_time_buckets['100-500ms'] += 1
        elif rt < 1000:
            self.response_time_buckets['500ms-1s'] += 1
        elif rt < 2000:
            self.response_time_buckets['1-2s'] += 1
        elif rt < 5000:
            self.response_time_buckets['2-5s'] += 1
        else:
            self.response_time_buckets['>5s'] += 1

        # Update rolling averages
        total = self.metrics['total_queries']
        prev_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = (
            (prev_avg * (total - 1) + entry['response_time']) / total
        )

        # Cache hit rate
        cached_count = sum(1 for e in self.query_log if e['cached'])
        self.metrics['cache_hit_rate'] = cached_count / total

        # Error rate
        error_count = sum(1 for e in self.query_log if not e['success'])
        self.metrics['error_rate'] = error_count / total

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        with self.lock:
            return {
                'overview': {
                    'total_queries': self.metrics['total_queries'],
                    'unique_users': len(self.metrics['unique_users']),
                    'avg_response_time': round(self.metrics['avg_response_time'], 3),
                    'cache_hit_rate': round(self.metrics['cache_hit_rate'], 3),
                    'error_rate': round(self.metrics['error_rate'], 3)
                },
                'queries_by_intent': dict(self.metrics['queries_by_intent']),
                'queries_by_tier': dict(self.metrics['queries_by_tier']),
                'popular_queries': self.popular_queries.most_common(10),
                'popular_executives': self.popular_executives.most_common(10),
                'popular_regions': self.popular_regions.most_common(10),
                'popular_genres': self.popular_genres.most_common(10),
                'response_time_distribution': self.response_time_buckets,
                'recent_activity': self._get_recent_activity(),
                'time_series': {
                    'hourly': self._get_hourly_data(),
                    'daily': self._get_daily_data()
                }
            }

    def _get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent queries"""
        recent = sorted(self.query_log, key=lambda x: x['timestamp'], reverse=True)[:limit]

        return [
            {
                'timestamp': entry['timestamp'].isoformat(),
                'question': entry['question'][:100],
                'intent': entry['intent'],
                'response_time': round(entry['response_time'], 3),
                'cached': entry['cached'],
                'success': entry['success']
            }
            for entry in recent
        ]

    def _get_hourly_data(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get queries per hour for last N hours"""
        now = datetime.now()
        data = []

        for i in range(hours):
            hour = now - timedelta(hours=hours - i)
            hour_key = hour.strftime('%Y-%m-%d %H:00')
            count = self.queries_by_hour.get(hour_key, 0)

            data.append({
                'hour': hour_key,
                'count': count
            })

        return data

    def _get_daily_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get queries per day for last N days"""
        now = datetime.now()
        data = []

        for i in range(days):
            day = now - timedelta(days=days - i)
            day_key = day.strftime('%Y-%m-%d')
            count = self.queries_by_day.get(day_key, 0)

            data.append({
                'date': day_key,
                'count': count
            })

        return data

    def get_user_analytics(self, email: str) -> Dict[str, Any]:
        """Get analytics for a specific user"""
        with self.lock:
            user_queries = [e for e in self.query_log if e['user_email'] == email]

            if not user_queries:
                return {'error': 'No queries found for user'}

            # User-specific metrics
            total = len(user_queries)
            avg_response_time = sum(e['response_time'] for e in user_queries) / total
            cached_count = sum(1 for e in user_queries if e['cached'])
            error_count = sum(1 for e in user_queries if not e['success'])

            # Intent distribution
            intent_dist = Counter(e['intent'] for e in user_queries)

            # Most recent queries
            recent = sorted(user_queries, key=lambda x: x['timestamp'], reverse=True)[:10]

            return {
                'email': email,
                'total_queries': total,
                'avg_response_time': round(avg_response_time, 3),
                'cache_hit_rate': round(cached_count / total, 3),
                'error_rate': round(error_count / total, 3),
                'intent_distribution': dict(intent_dist),
                'recent_queries': [
                    {
                        'timestamp': e['timestamp'].isoformat(),
                        'question': e['question'][:100],
                        'intent': e['intent']
                    }
                    for e in recent
                ]
            }

    def export_to_json(self, filepath: str):
        """Export analytics data to JSON file"""
        with self.lock:
            data = self.get_dashboard_data()

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report"""
        with self.lock:
            if not self.query_log:
                return {'error': 'No data available'}

            # Calculate percentiles
            response_times = sorted(e['response_time'] for e in self.query_log)
            n = len(response_times)

            p50 = response_times[int(n * 0.50)]
            p95 = response_times[int(n * 0.95)]
            p99 = response_times[int(n * 0.99)]

            return {
                'total_queries': len(self.query_log),
                'response_times': {
                    'mean': round(self.metrics['avg_response_time'], 3),
                    'p50': round(p50, 3),
                    'p95': round(p95, 3),
                    'p99': round(p99, 3),
                    'min': round(min(response_times), 3),
                    'max': round(max(response_times), 3)
                },
                'cache_performance': {
                    'hit_rate': round(self.metrics['cache_hit_rate'], 3),
                    'cache_queries': sum(1 for e in self.query_log if e['cached']),
                    'direct_queries': sum(1 for e in self.query_log if not e['cached'])
                },
                'reliability': {
                    'error_rate': round(self.metrics['error_rate'], 3),
                    'success_count': sum(1 for e in self.query_log if e['success']),
                    'error_count': sum(1 for e in self.query_log if not e['success'])
                }
            }


# Global instance
_analytics_dashboard = None


def get_analytics_dashboard() -> QueryAnalyticsDashboard:
    """Get or create global analytics dashboard instance"""
    global _analytics_dashboard
    if _analytics_dashboard is None:
        _analytics_dashboard = QueryAnalyticsDashboard(history_days=30)
    return _analytics_dashboard
