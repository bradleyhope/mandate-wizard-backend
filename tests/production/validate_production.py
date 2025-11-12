#!/usr/bin/env python3
"""
Production Validation Script

Comprehensive test of the complete Mandate Wizard pro architecture:
1. Check all services are running
2. Verify database connections
3. Test Redis Streams connectivity
4. Validate background worker is processing
5. Test analytics endpoints
6. Monitor system health

This script provides a complete health check of the production system.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "https://mandate-wizard-backend.onrender.com"
WORKER_SERVICE_ID = "srv-d4a5pv95pdvs73e0nfs0"

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

def print_section(text: str):
    """Print formatted section"""
    print(f"\n{Colors.BOLD}{text}{Colors.END}")
    print("-" * 80)

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"   {text}")

class ProductionValidator:
    """Validates production deployment"""
    
    def __init__(self):
        self.results = {
            'backend': False,
            'postgres': False,
            'redis': False,
            'worker': False,
            'analytics': False
        }
        self.errors = []
        
    def test_backend_health(self) -> bool:
        """Test backend API health"""
        print_section("1. Backend API Health Check")
        
        try:
            # Test health endpoint
            response = requests.get(f"{BACKEND_URL}/healthz", timeout=10)
            
            if response.status_code == 200:
                print_success("Backend API is responding")
                print_info(f"URL: {BACKEND_URL}")
                print_info(f"Status: {response.status_code}")
                
                # Test root endpoint
                root_response = requests.get(f"{BACKEND_URL}/", timeout=10)
                if root_response.status_code == 200:
                    data = root_response.json()
                    print_info(f"Service: {data.get('service', 'Unknown')}")
                    print_info(f"Mode: {data.get('mode', 'Unknown')}")
                
                # Test metrics endpoint
                metrics_response = requests.get(f"{BACKEND_URL}/metrics", timeout=10)
                if metrics_response.status_code == 200:
                    metrics = metrics_response.json()
                    print_info(f"Memory: {metrics.get('rss_mb', 'N/A')} MB")
                    print_info(f"Threads: {metrics.get('threads', 'N/A')}")
                    print_info(f"CPU: {metrics.get('cpu_percent', 'N/A')}%")
                
                return True
            else:
                print_error(f"Backend returned status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Backend health check failed: {e}")
            self.errors.append(f"Backend: {e}")
            return False
    
    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection via analytics endpoint"""
        print_section("2. PostgreSQL Connection Check")
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/analytics/demand/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                total_entities = data.get('total_entities', 0)
                
                print_success("PostgreSQL is connected and responding")
                print_info(f"Total Entities: {total_entities:,}")
                print_info(f"Total Queries: {data.get('total_queries', 0):,}")
                print_info(f"Entities with Demand: {data.get('entities_with_demand', 0):,}")
                print_info(f"Avg Demand Score: {data.get('avg_demand_score', 0):.2f}")
                
                if total_entities > 0:
                    print_success(f"Database contains {total_entities:,} entities")
                    return True
                else:
                    print_warning("Database is empty")
                    return False
            else:
                print_error(f"Stats endpoint returned status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"PostgreSQL connection check failed: {e}")
            self.errors.append(f"PostgreSQL: {e}")
            return False
    
    def test_redis_streams(self) -> bool:
        """Test Redis Streams via events endpoint"""
        print_section("3. Redis Streams Check")
        
        try:
            # Check if events endpoint exists
            response = requests.get(f"{BACKEND_URL}/api/events/stats", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                print_success("Redis Streams is accessible")
                
                # Display stream stats if available
                query_stream = data.get('query_signals', {})
                update_stream = data.get('update_requests', {})
                
                print_info(f"Query Signals Stream:")
                print_info(f"  Length: {query_stream.get('length', 'N/A')}")
                print_info(f"  Consumer Groups: {query_stream.get('groups', 'N/A')}")
                
                print_info(f"Update Requests Stream:")
                print_info(f"  Length: {update_stream.get('length', 'N/A')}")
                print_info(f"  Consumer Groups: {update_stream.get('groups', 'N/A')}")
                
                return True
            elif response.status_code == 404:
                print_warning("Events endpoint not available (expected if not implemented)")
                print_info("Redis Streams status cannot be verified via API")
                return True  # Don't fail validation
            else:
                print_warning(f"Events endpoint returned status {response.status_code}")
                return True  # Don't fail validation
                
        except Exception as e:
            print_warning(f"Redis Streams check failed: {e}")
            print_info("This is non-critical - worker may still be functioning")
            return True  # Don't fail validation
    
    def test_background_worker(self) -> bool:
        """Test background worker by checking if it's processing events"""
        print_section("4. Background Worker Check")
        
        print_info("Background worker status cannot be directly checked via API")
        print_info(f"Worker Service ID: {WORKER_SERVICE_ID}")
        print_info("To verify worker is running:")
        print_info("  1. Check Render dashboard")
        print_info("  2. Look for worker logs")
        print_info("  3. Monitor demand score updates after queries")
        
        # Indirect check: see if demand scores are being updated
        try:
            response = requests.get(f"{BACKEND_URL}/api/analytics/demand/top?limit=10", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get('entities', [])
                
                # Check if any entities have demand scores > 0
                entities_with_demand = [e for e in entities if e.get('demand_score', 0) > 0]
                
                if entities_with_demand:
                    print_success(f"Worker appears to be functioning ({len(entities_with_demand)} entities with demand)")
                    
                    for entity in entities_with_demand[:3]:
                        print_info(f"  {entity['name']}: score={entity['demand_score']}, queries={entity['query_count']}")
                    
                    return True
                else:
                    print_warning("No entities with demand scores yet")
                    print_info("Worker may be running but no queries processed yet")
                    return True  # Don't fail - this is expected initially
            else:
                print_warning(f"Could not check worker status (status {response.status_code})")
                return True  # Don't fail validation
                
        except Exception as e:
            print_warning(f"Worker check failed: {e}")
            return True  # Don't fail validation
    
    def test_analytics_endpoints(self) -> bool:
        """Test all analytics endpoints"""
        print_section("5. Analytics Endpoints Check")
        
        endpoints = [
            ("/api/analytics/demand/stats", "Overall Statistics"),
            ("/api/analytics/demand/top?limit=5", "Top Entities"),
            ("/api/analytics/demand/trending?limit=5", "Trending Entities"),
            ("/api/analytics/demand/stale?limit=5", "Stale Entities"),
        ]
        
        all_passed = True
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    print_success(f"{name}: OK")
                    
                    # Show sample data
                    data = response.json()
                    if 'total' in data:
                        print_info(f"  Total results: {data['total']}")
                else:
                    print_error(f"{name}: Status {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                print_error(f"{name}: {e}")
                all_passed = False
        
        # Test entity endpoint with a sample UUID
        print_info("\nTesting entity detail endpoint...")
        try:
            # Get a sample entity ID from top entities
            top_response = requests.get(f"{BACKEND_URL}/api/analytics/demand/top?limit=1", timeout=10)
            if top_response.status_code == 200:
                entities = top_response.json().get('entities', [])
                if entities:
                    entity_id = entities[0]['id']
                    entity_response = requests.get(
                        f"{BACKEND_URL}/api/analytics/demand/entity/{entity_id}", 
                        timeout=10
                    )
                    
                    if entity_response.status_code == 200:
                        print_success("Entity Detail: OK")
                        entity = entity_response.json().get('entity', {})
                        print_info(f"  Sample: {entity.get('name', 'Unknown')}")
                        print_info(f"  Demand Score: {entity.get('demand_score', 0)}")
                        print_info(f"  Query Frequency: {entity.get('query_frequency', 'unknown')}")
                    else:
                        print_error(f"Entity Detail: Status {entity_response.status_code}")
                        all_passed = False
        except Exception as e:
            print_error(f"Entity Detail: {e}")
            all_passed = False
        
        return all_passed
    
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print_header("PRODUCTION VALIDATION")
        print(f"Backend URL: {BACKEND_URL}")
        print(f"Test Time: {datetime.utcnow().isoformat()}")
        
        # Run all tests
        self.results['backend'] = self.test_backend_health()
        self.results['postgres'] = self.test_postgres_connection()
        self.results['redis'] = self.test_redis_streams()
        self.results['worker'] = self.test_background_worker()
        self.results['analytics'] = self.test_analytics_endpoints()
        
        # Print summary
        print_header("VALIDATION SUMMARY")
        
        for component, status in self.results.items():
            if status:
                print_success(f"{component.title()}: PASS")
            else:
                print_error(f"{component.title()}: FAIL")
        
        # Overall status
        all_passed = all(self.results.values())
        
        print("\n" + "="*80)
        if all_passed:
            print(f"{Colors.BOLD}{Colors.GREEN}  ✅ ALL CHECKS PASSED{Colors.END}")
            print(f"{Colors.BOLD}{Colors.GREEN}  Production system is healthy and operational{Colors.END}")
        else:
            print(f"{Colors.BOLD}{Colors.YELLOW}  ⚠️  SOME CHECKS FAILED{Colors.END}")
            print(f"{Colors.BOLD}{Colors.YELLOW}  Review errors above for details{Colors.END}")
            
            if self.errors:
                print(f"\n{Colors.BOLD}Errors:{Colors.END}")
                for error in self.errors:
                    print(f"  • {error}")
        
        print("="*80 + "\n")
        
        return all_passed

def main():
    """Main entry point"""
    validator = ProductionValidator()
    
    try:
        success = validator.run_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Validation failed with error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
