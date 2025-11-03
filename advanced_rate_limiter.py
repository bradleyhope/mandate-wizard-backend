"""
Advanced Rate Limiting for Netflix Mandate Wizard
Tiered subscription model with burst protection
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import threading


class AdvancedRateLimiter:
    """
    Tiered rate limiting with subscription support

    Tiers:
    - FREE: 2 queries/day (trial)
    - STANDARD: 100 queries/day
    - TEAM: 500 queries/day
    - ENTERPRISE: Unlimited
    """

    # Rate limits by tier (queries per day)
    TIER_LIMITS = {
        'free': 2,
        'standard': 100,
        'team': 500,
        'enterprise': float('inf')
    }

    # Burst limits (queries per minute)
    BURST_LIMITS = {
        'free': 1,
        'standard': 10,
        'team': 20,
        'enterprise': 50
    }

    def __init__(self):
        """Initialize rate limiter"""
        # Daily usage: user_email -> (count, reset_time)
        self.daily_usage: Dict[str, Tuple[int, datetime]] = {}

        # Burst usage: user_email -> [(timestamp, count)]
        self.burst_usage: Dict[str, list] = defaultdict(list)

        # Thread lock for concurrent access
        self.lock = threading.Lock()

        # Cleanup thread
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Start background thread to clean up old data"""
        def cleanup():
            while True:
                time.sleep(3600)  # Run every hour
                self._cleanup_old_data()

        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

    def _cleanup_old_data(self):
        """Remove old usage data"""
        with self.lock:
            now = datetime.now()

            # Clean up daily usage (remove entries older than 2 days)
            expired_daily = [
                email for email, (_, reset_time) in self.daily_usage.items()
                if now > reset_time + timedelta(days=1)
            ]
            for email in expired_daily:
                del self.daily_usage[email]

            # Clean up burst usage (remove entries older than 5 minutes)
            cutoff = time.time() - 300
            for email in list(self.burst_usage.keys()):
                self.burst_usage[email] = [
                    (ts, count) for ts, count in self.burst_usage[email]
                    if ts > cutoff
                ]
                if not self.burst_usage[email]:
                    del self.burst_usage[email]

    def get_user_tier(self, email: str, subscription_status: str = None) -> str:
        """
        Determine user's subscription tier

        Args:
            email: User's email
            subscription_status: Subscription status from Ghost CMS

        Returns:
            Tier name (free, standard, team, enterprise)
        """
        if not subscription_status:
            return 'free'

        status_lower = subscription_status.lower()

        if status_lower in ['enterprise', 'unlimited']:
            return 'enterprise'
        elif status_lower in ['team', 'business']:
            return 'team'
        elif status_lower in ['standard', 'pro', 'paid']:
            return 'standard'
        else:
            return 'free'

    def check_daily_limit(self, email: str, tier: str) -> Tuple[bool, int, int]:
        """
        Check if user has exceeded daily limit

        Args:
            email: User's email
            tier: User's tier

        Returns:
            Tuple of (allowed, used, limit)
        """
        with self.lock:
            limit = self.TIER_LIMITS[tier]

            if limit == float('inf'):
                return True, 0, float('inf')

            now = datetime.now()

            # Get or initialize daily usage
            if email not in self.daily_usage:
                # First query of the day
                self.daily_usage[email] = (0, now + timedelta(days=1))

            count, reset_time = self.daily_usage[email]

            # Check if reset time has passed
            if now >= reset_time:
                # Reset counter
                count = 0
                reset_time = now + timedelta(days=1)
                self.daily_usage[email] = (count, reset_time)

            # Check limit
            allowed = count < limit
            return allowed, count, limit

    def check_burst_limit(self, email: str, tier: str) -> Tuple[bool, int, int]:
        """
        Check if user has exceeded burst limit (queries per minute)

        Args:
            email: User's email
            tier: User's tier

        Returns:
            Tuple of (allowed, current_rate, limit)
        """
        with self.lock:
            limit = self.BURST_LIMITS[tier]
            now = time.time()
            cutoff = now - 60  # Last minute

            # Get burst usage
            recent_queries = [
                count for ts, count in self.burst_usage[email]
                if ts > cutoff
            ]

            current_rate = len(recent_queries)
            allowed = current_rate < limit

            return allowed, current_rate, limit

    def record_query(self, email: str, tier: str):
        """
        Record a query for rate limiting

        Args:
            email: User's email
            tier: User's tier
        """
        with self.lock:
            now = datetime.now()
            timestamp = time.time()

            # Update daily usage
            if email not in self.daily_usage:
                self.daily_usage[email] = (1, now + timedelta(days=1))
            else:
                count, reset_time = self.daily_usage[email]

                # Check if reset time has passed
                if now >= reset_time:
                    count = 1
                    reset_time = now + timedelta(days=1)
                else:
                    count += 1

                self.daily_usage[email] = (count, reset_time)

            # Update burst usage
            self.burst_usage[email].append((timestamp, 1))

            # Clean old burst entries
            cutoff = timestamp - 300  # Keep last 5 minutes
            self.burst_usage[email] = [
                (ts, c) for ts, c in self.burst_usage[email]
                if ts > cutoff
            ]

    def check_and_record(
        self,
        email: str,
        subscription_status: str = None
    ) -> Tuple[bool, str, Dict[str, any]]:
        """
        Check rate limits and record query if allowed

        Args:
            email: User's email
            subscription_status: Subscription status

        Returns:
            Tuple of (allowed, reason, details)
        """
        # Determine tier
        tier = self.get_user_tier(email, subscription_status)

        # Check daily limit
        daily_allowed, daily_used, daily_limit = self.check_daily_limit(email, tier)

        if not daily_allowed:
            return False, 'daily_limit_exceeded', {
                'tier': tier,
                'used': daily_used,
                'limit': daily_limit,
                'reset_time': self.daily_usage[email][1].isoformat()
            }

        # Check burst limit
        burst_allowed, burst_rate, burst_limit = self.check_burst_limit(email, tier)

        if not burst_allowed:
            return False, 'burst_limit_exceeded', {
                'tier': tier,
                'current_rate': burst_rate,
                'limit': burst_limit
            }

        # Record query
        self.record_query(email, tier)

        return True, 'allowed', {
            'tier': tier,
            'daily_used': daily_used + 1,
            'daily_limit': daily_limit,
            'burst_rate': burst_rate + 1,
            'burst_limit': burst_limit
        }

    def get_user_stats(self, email: str, subscription_status: str = None) -> Dict[str, any]:
        """Get usage statistics for a user"""
        tier = self.get_user_tier(email, subscription_status)

        with self.lock:
            # Daily stats
            if email in self.daily_usage:
                daily_used, reset_time = self.daily_usage[email]
            else:
                daily_used = 0
                reset_time = datetime.now() + timedelta(days=1)

            daily_limit = self.TIER_LIMITS[tier]
            daily_remaining = max(0, daily_limit - daily_used) if daily_limit != float('inf') else float('inf')

            # Burst stats
            now = time.time()
            cutoff = now - 60
            recent_queries = [
                1 for ts, _ in self.burst_usage.get(email, [])
                if ts > cutoff
            ]
            burst_rate = len(recent_queries)
            burst_limit = self.BURST_LIMITS[tier]

            return {
                'tier': tier,
                'daily': {
                    'used': daily_used,
                    'limit': daily_limit if daily_limit != float('inf') else 'unlimited',
                    'remaining': daily_remaining if daily_remaining != float('inf') else 'unlimited',
                    'reset_time': reset_time.isoformat()
                },
                'burst': {
                    'current_rate': burst_rate,
                    'limit': burst_limit
                }
            }

    def reset_user_limits(self, email: str):
        """Reset limits for a user (admin function)"""
        with self.lock:
            if email in self.daily_usage:
                del self.daily_usage[email]
            if email in self.burst_usage:
                del self.burst_usage[email]

    def get_all_stats(self) -> Dict[str, any]:
        """Get system-wide statistics"""
        with self.lock:
            # Count users by tier
            tier_counts = defaultdict(int)
            for email, (_, _) in self.daily_usage.items():
                # Note: We'd need to store tier info to accurately count
                # For now, estimate based on usage
                pass

            return {
                'total_users': len(self.daily_usage),
                'total_daily_queries': sum(count for count, _ in self.daily_usage.values()),
                'active_users_last_hour': len([
                    email for email, entries in self.burst_usage.items()
                    if entries and entries[-1][0] > time.time() - 3600
                ])
            }


# Global instance
_rate_limiter = None


def get_rate_limiter() -> AdvancedRateLimiter:
    """Get or create global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = AdvancedRateLimiter()
    return _rate_limiter


# Example usage
if __name__ == '__main__':
    limiter = AdvancedRateLimiter()

    # Test user
    email = "test@example.com"

    print("Testing rate limiter...\n")

    # Test free tier (2 queries/day)
    for i in range(5):
        allowed, reason, details = limiter.check_and_record(email, 'free')
        print(f"Query {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")
        print(f"  Reason: {reason}")
        print(f"  Details: {details}")
        print()

        if i < 2:
            time.sleep(0.1)

    # Check stats
    print("\nUser Stats:")
    stats = limiter.get_user_stats(email, 'free')
    print(f"  Tier: {stats['tier']}")
    print(f"  Daily: {stats['daily']['used']}/{stats['daily']['limit']}")
    print(f"  Remaining: {stats['daily']['remaining']}")
