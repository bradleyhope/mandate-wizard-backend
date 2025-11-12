"""
Priority Engine for Mandate Wizard

Implements data-driven prioritization for entity updates based on:
- User demand (demand_score, query_count)
- Data freshness (last_updated_at)
- Entity importance (entity_type, relationships)
- Update urgency (stale high-demand entities)

This engine determines which entities should be updated first to maximize
value for users while optimizing resource usage.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import math


class UpdatePriority(Enum):
    """Priority levels for entity updates"""
    CRITICAL = 1    # Stale high-demand entities
    HIGH = 2        # Trending or frequently queried
    MEDIUM = 3      # Moderate demand or aging data
    LOW = 4         # Low demand, recent data
    DEFERRED = 5    # No demand, fresh data


class PriorityEngine:
    """
    Calculates update priority for entities based on demand and freshness.
    
    Priority Score Formula:
    priority_score = (demand_weight * demand_score) + 
                    (freshness_weight * freshness_score) +
                    (trending_weight * trending_score)
    
    Higher scores = higher priority for updates
    """
    
    def __init__(self,
                 demand_weight: float = 0.5,
                 freshness_weight: float = 0.3,
                 trending_weight: float = 0.2,
                 stale_threshold_days: int = 30,
                 critical_demand_threshold: int = 10):
        """
        Initialize priority engine with configurable weights.
        
        Args:
            demand_weight: Weight for demand score (0-1)
            freshness_weight: Weight for data freshness (0-1)
            trending_weight: Weight for trending status (0-1)
            stale_threshold_days: Days before data is considered stale
            critical_demand_threshold: Demand score threshold for critical priority
        """
        self.demand_weight = demand_weight
        self.freshness_weight = freshness_weight
        self.trending_weight = trending_weight
        self.stale_threshold_days = stale_threshold_days
        self.critical_demand_threshold = critical_demand_threshold
        
        # Validate weights sum to 1.0
        total_weight = demand_weight + freshness_weight + trending_weight
        if not math.isclose(total_weight, 1.0, rel_tol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def calculate_priority_score(self, entity: Dict[str, Any]) -> float:
        """
        Calculate priority score for an entity.
        
        Args:
            entity: Entity dict with demand_score, last_updated_at, etc.
            
        Returns:
            Priority score (0-100, higher = more urgent)
        """
        demand_score = self._calculate_demand_score(entity)
        freshness_score = self._calculate_freshness_score(entity)
        trending_score = self._calculate_trending_score(entity)
        
        priority_score = (
            self.demand_weight * demand_score +
            self.freshness_weight * freshness_score +
            self.trending_weight * trending_score
        )
        
        return round(priority_score, 2)
    
    def _calculate_demand_score(self, entity: Dict[str, Any]) -> float:
        """
        Calculate demand component (0-100).
        
        Uses logarithmic scaling to prevent extreme values from dominating.
        """
        raw_demand = entity.get('demand_score', 0)
        
        if raw_demand == 0:
            return 0.0
        
        # Logarithmic scaling: log10(demand + 1) * 20
        # demand=1 -> 6, demand=10 -> 20, demand=100 -> 40, demand=1000 -> 60
        score = math.log10(raw_demand + 1) * 20
        
        return min(score, 100.0)
    
    def _calculate_freshness_score(self, entity: Dict[str, Any]) -> float:
        """
        Calculate freshness component (0-100).
        
        Older data = higher score (more urgent to update).
        """
        last_updated = entity.get('last_updated_at')
        
        if not last_updated:
            # No update timestamp = assume very old
            return 100.0
        
        # Parse timestamp
        if isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
        
        # Calculate age in days
        now = datetime.utcnow()
        if last_updated.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        
        age_days = (now - last_updated).total_seconds() / 86400
        
        # Scoring: 0 days = 0, 30 days = 50, 60+ days = 100
        score = min((age_days / self.stale_threshold_days) * 50, 100.0)
        
        return score
    
    def _calculate_trending_score(self, entity: Dict[str, Any]) -> float:
        """
        Calculate trending component (0-100).
        
        Entities with recent query activity score higher.
        """
        last_queried = entity.get('last_queried_at')
        query_count = entity.get('query_count', 0)
        
        if not last_queried or query_count == 0:
            return 0.0
        
        # Parse timestamp
        if isinstance(last_queried, str):
            last_queried = datetime.fromisoformat(last_queried.replace('Z', '+00:00'))
        
        # Calculate recency (queries in last 7 days are trending)
        now = datetime.utcnow()
        if last_queried.tzinfo:
            from datetime import timezone
            now = datetime.now(timezone.utc)
        
        days_since_query = (now - last_queried).total_seconds() / 86400
        
        if days_since_query <= 1:
            return 100.0  # Queried today = very trending
        elif days_since_query <= 7:
            return 70.0   # Queried this week = trending
        elif days_since_query <= 30:
            return 30.0   # Queried this month = somewhat trending
        else:
            return 0.0    # Old queries = not trending
    
    def classify_priority(self, entity: Dict[str, Any]) -> UpdatePriority:
        """
        Classify entity into priority tier.
        
        Args:
            entity: Entity dict with demand and freshness data
            
        Returns:
            UpdatePriority enum value
        """
        demand_score = entity.get('demand_score', 0)
        priority_score = self.calculate_priority_score(entity)
        
        # Check for critical: high demand + stale data
        if demand_score >= self.critical_demand_threshold:
            last_updated = entity.get('last_updated_at')
            if last_updated:
                if isinstance(last_updated, str):
                    last_updated = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                
                now = datetime.utcnow()
                if last_updated.tzinfo:
                    from datetime import timezone
                    now = datetime.now(timezone.utc)
                
                age_days = (now - last_updated).total_seconds() / 86400
                
                if age_days >= self.stale_threshold_days:
                    return UpdatePriority.CRITICAL
        
        # Classify by priority score
        if priority_score >= 70:
            return UpdatePriority.HIGH
        elif priority_score >= 40:
            return UpdatePriority.MEDIUM
        elif priority_score >= 20:
            return UpdatePriority.LOW
        else:
            return UpdatePriority.DEFERRED
    
    def rank_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank entities by update priority.
        
        Args:
            entities: List of entity dicts
            
        Returns:
            Sorted list with priority_score and priority_tier added
        """
        # Calculate scores
        for entity in entities:
            entity['priority_score'] = self.calculate_priority_score(entity)
            entity['priority_tier'] = self.classify_priority(entity).name
        
        # Sort by priority score (descending)
        ranked = sorted(entities, key=lambda e: e['priority_score'], reverse=True)
        
        return ranked
    
    def get_update_batch(self, 
                        entities: List[Dict[str, Any]], 
                        batch_size: int = 100,
                        min_priority: Optional[UpdatePriority] = None) -> List[Dict[str, Any]]:
        """
        Get a batch of entities to update, prioritized by urgency.
        
        Args:
            entities: List of all entities
            batch_size: Maximum number of entities to return
            min_priority: Minimum priority tier to include (optional)
            
        Returns:
            List of entities to update, sorted by priority
        """
        # Rank all entities
        ranked = self.rank_entities(entities)
        
        # Filter by minimum priority if specified
        if min_priority:
            ranked = [
                e for e in ranked 
                if UpdatePriority[e['priority_tier']].value <= min_priority.value
            ]
        
        # Return top N
        return ranked[:batch_size]
    
    def get_critical_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get entities that require immediate updates (CRITICAL priority).
        
        Args:
            entities: List of all entities
            
        Returns:
            List of critical entities
        """
        ranked = self.rank_entities(entities)
        
        critical = [
            e for e in ranked 
            if e['priority_tier'] == UpdatePriority.CRITICAL.name
        ]
        
        return critical
    
    def generate_update_schedule(self, 
                                 entities: List[Dict[str, Any]], 
                                 daily_budget: int = 500) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a multi-day update schedule based on priority.
        
        Args:
            entities: List of all entities
            daily_budget: Maximum entities to update per day
            
        Returns:
            Dict mapping day number to list of entities to update
        """
        ranked = self.rank_entities(entities)
        
        schedule = {}
        day = 1
        
        for i in range(0, len(ranked), daily_budget):
            batch = ranked[i:i + daily_budget]
            schedule[f"day_{day}"] = batch
            day += 1
        
        return schedule
    
    def get_statistics(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get priority distribution statistics.
        
        Args:
            entities: List of entities
            
        Returns:
            Dict with statistics about priority distribution
        """
        ranked = self.rank_entities(entities)
        
        # Count by priority tier
        tier_counts = {}
        for priority in UpdatePriority:
            tier_counts[priority.name] = len([
                e for e in ranked 
                if e['priority_tier'] == priority.name
            ])
        
        # Calculate averages
        total_entities = len(ranked)
        avg_priority_score = sum(e['priority_score'] for e in ranked) / max(total_entities, 1)
        
        # Find top priorities
        top_10 = ranked[:10]
        
        return {
            'total_entities': total_entities,
            'avg_priority_score': round(avg_priority_score, 2),
            'tier_distribution': tier_counts,
            'top_10_entities': [
                {
                    'id': e.get('id'),
                    'name': e.get('name'),
                    'priority_score': e['priority_score'],
                    'priority_tier': e['priority_tier'],
                    'demand_score': e.get('demand_score', 0)
                }
                for e in top_10
            ]
        }
