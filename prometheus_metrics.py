"""
Prometheus Metrics for Netflix Mandate Wizard
Real-time monitoring of performance, usage, and system health
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from prometheus_client import CollectorRegistry
from typing import Dict, Any
import time
from functools import wraps

# Create custom registry to avoid conflicts
registry = CollectorRegistry()

# ============================================
# Query Metrics
# ============================================

# Query counter by intent
query_total = Counter(
    'mandatewizard_queries_total',
    'Total number of queries processed',
    ['intent', 'status'],
    registry=registry
)

# Query duration histogram
query_duration_seconds = Histogram(
    'mandatewizard_query_duration_seconds',
    'Query processing duration in seconds',
    ['intent'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

# Cache metrics
cache_hits_total = Counter(
    'mandatewizard_cache_hits_total',
    'Total number of cache hits',
    ['cache_type'],
    registry=registry
)

cache_misses_total = Counter(
    'mandatewizard_cache_misses_total',
    'Total number of cache misses',
    ['cache_type'],
    registry=registry
)

# ============================================
# Database Metrics
# ============================================

# Vector search metrics
vector_search_duration_seconds = Histogram(
    'mandatewizard_vector_search_duration_seconds',
    'Vector search duration in seconds',
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0],
    registry=registry
)

vector_search_results = Histogram(
    'mandatewizard_vector_search_results',
    'Number of results returned from vector search',
    buckets=[1, 3, 5, 10, 20, 50],
    registry=registry
)

# Graph search metrics
graph_search_duration_seconds = Histogram(
    'mandatewizard_graph_search_duration_seconds',
    'Graph search duration in seconds',
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
    registry=registry
)

# ============================================
# LLM Metrics
# ============================================

# LLM API calls
llm_requests_total = Counter(
    'mandatewizard_llm_requests_total',
    'Total number of LLM API requests',
    ['model', 'status'],
    registry=registry
)

llm_tokens_total = Counter(
    'mandatewizard_llm_tokens_total',
    'Total number of tokens used',
    ['model', 'type'],
    registry=registry
)

llm_duration_seconds = Histogram(
    'mandatewizard_llm_duration_seconds',
    'LLM API call duration in seconds',
    ['model'],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    registry=registry
)

llm_cost_usd = Counter(
    'mandatewizard_llm_cost_usd',
    'Total LLM cost in USD',
    ['model'],
    registry=registry
)

# ============================================
# Rate Limiting Metrics
# ============================================

rate_limit_exceeded_total = Counter(
    'mandatewizard_rate_limit_exceeded_total',
    'Total number of rate limit exceeded errors',
    ['tier'],
    registry=registry
)

# ============================================
# User Metrics
# ============================================

active_users_gauge = Gauge(
    'mandatewizard_active_users',
    'Number of active users (last 5 minutes)',
    registry=registry
)

queries_by_subscription = Counter(
    'mandatewizard_queries_by_subscription',
    'Queries by subscription tier',
    ['tier'],
    registry=registry
)

# ============================================
# System Health Metrics
# ============================================

system_health = Gauge(
    'mandatewizard_system_health',
    'System health status (1=healthy, 0=unhealthy)',
    ['component'],
    registry=registry
)

# Error metrics
errors_total = Counter(
    'mandatewizard_errors_total',
    'Total number of errors',
    ['error_type', 'component'],
    registry=registry
)

# ============================================
# Advanced RAG Metrics (Batch 2)
# ============================================

adaptive_topk_distribution = Histogram(
    'mandatewizard_adaptive_topk',
    'Distribution of adaptive top-k values',
    buckets=[1, 3, 5, 8, 10, 15, 20, 30],
    registry=registry
)

cross_encoder_reranking_improvement = Histogram(
    'mandatewizard_cross_encoder_improvement',
    'Average position improvement from cross-encoder reranking',
    buckets=[0, 1, 2, 3, 5, 10, 20],
    registry=registry
)

query_expansion_enabled = Counter(
    'mandatewizard_query_expansion_total',
    'Number of queries with expansion enabled',
    registry=registry
)

hyde_enabled = Counter(
    'mandatewizard_hyde_total',
    'Number of queries with HyDE enabled',
    registry=registry
)

# ============================================
# Info Metrics
# ============================================

app_info = Info(
    'mandatewizard_app',
    'Application information',
    registry=registry
)

app_info.info({
    'version': '5.0',
    'component': 'netflix-mandate-wizard',
    'environment': 'production'
})


# ============================================
# Metric Recording Functions
# ============================================

def record_query(intent: str, duration: float, status: str = 'success'):
    """Record a query execution"""
    query_total.labels(intent=intent, status=status).inc()
    query_duration_seconds.labels(intent=intent).observe(duration)


def record_cache_hit(cache_type: str = 'semantic'):
    """Record a cache hit"""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str = 'semantic'):
    """Record a cache miss"""
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_vector_search(duration: float, num_results: int):
    """Record vector search metrics"""
    vector_search_duration_seconds.observe(duration)
    vector_search_results.observe(num_results)


def record_graph_search(duration: float):
    """Record graph search metrics"""
    graph_search_duration_seconds.observe(duration)


def record_llm_request(model: str, duration: float, tokens_input: int,
                       tokens_output: int, cost: float, status: str = 'success'):
    """Record LLM API request"""
    llm_requests_total.labels(model=model, status=status).inc()
    llm_tokens_total.labels(model=model, type='input').inc(tokens_input)
    llm_tokens_total.labels(model=model, type='output').inc(tokens_output)
    llm_duration_seconds.labels(model=model).observe(duration)
    llm_cost_usd.labels(model=model).inc(cost)


def record_rate_limit_exceeded(tier: str):
    """Record rate limit exceeded"""
    rate_limit_exceeded_total.labels(tier=tier).inc()


def record_error(error_type: str, component: str):
    """Record an error"""
    errors_total.labels(error_type=error_type, component=component).inc()


def record_adaptive_topk(top_k: int):
    """Record adaptive top-k value"""
    adaptive_topk_distribution.observe(top_k)


def record_cross_encoder_improvement(improvement: float):
    """Record cross-encoder reranking improvement"""
    cross_encoder_reranking_improvement.observe(improvement)


def update_system_health(component: str, is_healthy: bool):
    """Update system health status"""
    system_health.labels(component=component).set(1 if is_healthy else 0)


def update_active_users(count: int):
    """Update active users count"""
    active_users_gauge.set(count)


def record_subscription_query(tier: str):
    """Record query by subscription tier"""
    queries_by_subscription.labels(tier=tier).inc()


# ============================================
# Decorators for Automatic Metric Collection
# ============================================

def track_query(intent: str = 'HYBRID'):
    """Decorator to track query execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = 'success'
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                record_query(intent, duration, status)
        return wrapper
    return decorator


def track_vector_search(func):
    """Decorator to track vector search"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            num_results = len(result.get('documents', []))
            record_vector_search(duration, num_results)
            return result
        except Exception as e:
            record_error('vector_search_failed', 'pinecone')
            raise
    return wrapper


def track_graph_search(func):
    """Decorator to track graph search"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            record_graph_search(duration)
            return result
        except Exception as e:
            record_error('graph_search_failed', 'neo4j')
            raise
    return wrapper


# ============================================
# Metrics Endpoint
# ============================================

def get_metrics() -> bytes:
    """Get Prometheus metrics in text format"""
    return generate_latest(registry)


def get_metrics_summary() -> Dict[str, Any]:
    """Get human-readable metrics summary"""
    # This would aggregate metrics for display
    # Implementation depends on storing metrics data
    return {
        'total_queries': 0,  # Would be computed from REGISTRY
        'cache_hit_rate': 0.0,
        'avg_query_duration': 0.0,
        'total_cost': 0.0
    }


# ============================================
# Health Check
# ============================================

def check_system_health() -> Dict[str, bool]:
    """Check health of all components"""
    health = {
        'pinecone': True,  # Would actually check connection
        'neo4j': True,
        'llm': True,
        'cache': True
    }

    # Update Prometheus gauges
    for component, is_healthy in health.items():
        update_system_health(component, is_healthy)

    return health
